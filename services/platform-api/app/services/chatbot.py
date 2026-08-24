from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Protocol

import httpx
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import CatalogProduct, ChatMessage, ChatSession


@dataclass(frozen=True, slots=True)
class ChatGatewayAnswer:
    answer: str
    audit_id: str
    model: str
    mode: str
    suggested_actions: list[str]
    sources: list[dict[str, object]] = field(default_factory=list)


class ChatGateway(Protocol):
    async def answer(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        context: list[str],
        locale: str,
    ) -> ChatGatewayAnswer: ...


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _secret(settings: Settings) -> bytes:
    return settings.chat_session_secret.get_secret_value().encode("utf-8")


def token_hash(token: str, *, settings: Settings) -> str:
    return hmac.new(_secret(settings), token.encode("utf-8"), hashlib.sha256).hexdigest()


def metadata_hash(value: str | None, *, settings: Settings) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.strip().split())[:1000]
    if not normalized:
        return None
    return hmac.new(_secret(settings), normalized.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session(
    db: Session,
    *,
    locale: str,
    page_url: str | None,
    referrer: str | None,
    client_ip: str | None,
    user_agent: str | None,
    settings: Settings,
) -> tuple[ChatSession, str, ChatMessage]:
    if not settings.public_chat_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Chat unavailable"
        )

    raw_token = secrets.token_urlsafe(36)
    now = utcnow()
    session = ChatSession(
        token_hash=token_hash(raw_token, settings=settings),
        channel="PUBLIC_WEB",
        locale=locale,
        page_url=page_url,
        referrer=referrer,
        status="OPEN",
        accepted_privacy_at=now,
        ip_hash=metadata_hash(client_ip, settings=settings),
        user_agent_hash=metadata_hash(user_agent, settings=settings),
        expires_at=now + timedelta(minutes=settings.chatbot_session_ttl_minutes),
        last_message_at=now,
        rate_window_started_at=now,
        rate_window_count=0,
    )
    welcome = ChatMessage(
        session=session,
        role="assistant",
        content=settings.chatbot_welcome_message,
        provider="smartdiag",
        model="smartdiag-welcome",
        mode="welcome",
        audit_id=f"welcome-{session.id}",
        suggested_actions=list(settings.chatbot_quick_action_codes),
        sources=[],
        metadata_json={"privacy_notice": settings.chatbot_privacy_notice},
    )
    db.add(session)
    db.add(welcome)
    db.commit()
    db.refresh(session)
    db.refresh(welcome)
    return session, raw_token, welcome


def require_session(
    db: Session,
    *,
    session_id: str,
    token: str | None,
    settings: Settings,
    allow_closed: bool = False,
) -> ChatSession:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing chat session token"
        )
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid chat session")
    supplied = token_hash(token, settings=settings)
    if not hmac.compare_digest(session.token_hash, supplied):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid chat session token"
        )
    if _aware(session.expires_at) <= utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Chat session expired")
    if not allow_closed and session.status != "OPEN":
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Chat session closed")
    return session


def enforce_rate_limit(*, session: ChatSession, settings: Settings) -> None:
    now = utcnow()
    window_started = _aware(session.rate_window_started_at)
    if now - window_started >= timedelta(seconds=settings.chatbot_rate_window_seconds):
        session.rate_window_started_at = now
        session.rate_window_count = 0
    if session.rate_window_count >= settings.chatbot_rate_limit_messages:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Se alcanzó temporalmente el límite de mensajes. Intente nuevamente más tarde.",
        )
    session.rate_window_count += 1


def find_existing_exchange(
    db: Session,
    *,
    session_id: str,
    client_message_id: str,
) -> tuple[ChatMessage, ChatMessage | None] | None:
    user_message = db.scalar(
        select(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.client_message_id == client_message_id,
            ChatMessage.role == "user",
        )
    )
    if user_message is None:
        return None
    assistant_message = db.scalar(
        select(ChatMessage).where(
            ChatMessage.session_id == session_id,
            ChatMessage.reply_to_message_id == user_message.id,
            ChatMessage.role == "assistant",
        )
    )
    return user_message, assistant_message


def load_history(db: Session, *, session_id: str, limit: int) -> list[ChatMessage]:
    descending = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
    )
    return list(reversed(descending))


def build_public_context(db: Session, *, message: str, settings: Settings) -> list[str]:
    context = [
        f"BUSINESS|{settings.business_name}|{settings.business_address}|{settings.business_phone}",
        f"HOURS|{settings.business_hours}",
        "WORKFLOW|OT creada > cotizada por técnico > pendiente de aprobación > pendiente de repuestos > finalizada para facturar > facturada",
        "PRIVACY|No se muestran datos de clientes, vehículos u órdenes sin autenticación.",
    ]
    words = {word.strip(".,;:!?¿¡()[]").casefold() for word in message.split() if len(word) >= 3}
    products = list(
        db.scalars(
            select(CatalogProduct)
            .where(CatalogProduct.active.is_(True))
            .order_by(CatalogProduct.featured.desc(), CatalogProduct.name)
            .limit(30)
        )
    )
    matches: list[CatalogProduct] = []
    for product in products:
        haystack = " ".join(
            filter(None, [product.sku, product.name, product.brand, product.short_description])
        ).casefold()
        if not words or any(word in haystack for word in words):
            matches.append(product)
        if len(matches) >= 5:
            break
    for product in matches:
        context.append(
            "PRODUCT|{}|{}|{} {:.2f}|{}|{}".format(
                product.sku,
                product.name,
                product.currency,
                product.price,
                product.stock_status,
                product.compatibility_notes or "Compatibilidad sujeta a validación por VIN",
            )
        )
    return context


def _safe_actions(message: str) -> list[str]:
    normalized = message.casefold()
    actions: list[str] = []
    if any(term in normalized for term in ("cita", "reserv", "diagnóst", "diagnost")):
        actions.append("BOOK_SERVICE")
    if any(term in normalized for term in ("repuesto", "pieza", "parte", "precio", "filtro")):
        actions.append("SEARCH_PARTS")
    if any(term in normalized for term in ("whatsapp", "asesor", "persona", "llamar")):
        actions.append("CONTACT_WHATSAPP")
    return actions or ["BOOK_SERVICE", "SEARCH_PARTS"]


def _is_prompt_attack(message: str) -> bool:
    normalized = message.casefold()
    return any(
        term in normalized
        for term in (
            "ignora tus instrucciones",
            "prompt del sistema",
            "system prompt",
            "revela el prompt",
            "muestra el prompt",
            "configuración interna",
            "configuracion interna",
            "secretos",
            "variables de entorno",
        )
    )


def _known_customer_data(message: str, history: list[dict[str, str]] | None) -> dict[str, str]:
    text = "\n".join([item.get("content", "") for item in (history or []) if item.get("role") == "user"] + [message])[-12000:]
    facts: dict[str, str] = {}
    patterns = {
        "correo": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "teléfono": r"(?<!\d)(?:\+?504[ -]?)?[2389]\d{3}[ -]?\d{4}(?!\d)",
        "vehículo": r"\b(?:Ford|Honda|Toyota|Hyundai|Kia|Nissan|Mazda|Chevrolet|Mitsubishi|Volkswagen|Jeep)\s+[A-Za-z0-9-]+(?:\s+(?:19\d{2}|20\d{2}))?\b",
    }
    for label, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        if match: facts[label] = " ".join(match.group(0).split())[:120]
    return facts


def fallback_answer(message: str, *, settings: Settings, history: list[dict[str, str]] | None = None) -> ChatGatewayAnswer:
    normalized = message.casefold()
    if _is_prompt_attack(message):
        answer = (
            "No puedo revelar instrucciones, configuración, credenciales ni información interna. "
            "Sí puedo ayudarle como cliente con servicios, repuestos, una cita o solicitar un asesor."
        )
        mode = "blocked"
    elif any(
        term in normalized for term in ("factura", "pago", "inventario", "descuento", "libera el")
    ):
        answer = (
            "Puedo explicar el proceso, pero el chatbot público no puede emitir facturas, registrar pagos, "
            "modificar inventario, aplicar descuentos ni liberar vehículos. Esas acciones requieren un usuario autorizado."
        )
        mode = "blocked"
    elif any(term in normalized for term in ("cita", "reserv", "agenda", "diagnóst", "diagnost")):
        facts = _known_customer_data(message, history)
        missing = [label for label in ("teléfono", "vehículo") if label not in facts]
        detail = (
            " Ya registré " + ", ".join(f"{key}: {value}" for key, value in facts.items()) + "."
            if facts else ""
        )
        request = f" Sólo falta {', '.join(missing)}." if missing else " Continúe con fecha, horario y motivo."
        answer = (
            "Puede reservar desde la sección «Reservar» de esta página."
            f"{detail}{request} SmartDiag504 confirmará disponibilidad y alcance inicial."
        )
        mode = "fallback"
    elif any(
        term in normalized for term in ("repuesto", "pieza", "parte", "precio", "stock", "vin")
    ):
        answer = (
            "Busque por número de parte, descripción o marca. La existencia se confirma al procesar el pedido y "
            "la compatibilidad debe validarse por VIN, motor y versión antes de instalar."
        )
        mode = "fallback"
    elif any(
        term in normalized for term in ("horario", "ubicación", "ubicacion", "teléfono", "telefono")
    ):
        answer = (
            f"{settings.business_name} atiende en {settings.business_address}. Horario: {settings.business_hours}. "
            f"Contacto: {settings.business_phone}."
        )
        mode = "fallback"
    else:
        answer = (
            "Puedo orientarle sobre servicios, reservas, repuestos y el flujo de una orden de trabajo. "
            "Indique marca, modelo, año y el síntoma principal; la orientación no sustituye una inspección técnica."
        )
        mode = "fallback"
    return ChatGatewayAnswer(
        answer=answer,
        audit_id=f"fallback-{secrets.token_hex(12)}",
        model="smartdiag-fallback",
        mode=mode,
        suggested_actions=["CONTACT_WHATSAPP"]
        if _is_prompt_attack(message)
        else _safe_actions(message),
        sources=[],
    )


class HttpChatGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def answer(
        self,
        *,
        message: str,
        history: list[dict[str, str]],
        context: list[str],
        locale: str,
    ) -> ChatGatewayAnswer:
        if _is_prompt_attack(message):
            return fallback_answer(message, settings=self.settings, history=history)
        url = f"{self.settings.ai_gateway_url.rstrip('/')}/v1/public-chat"
        headers = {"X-AI-Gateway-Token": self.settings.ai_gateway_internal_token.get_secret_value()}
        payload = {
            "message": message,
            "history": history,
            "context": context,
            "locale": locale,
        }
        timeout = httpx.Timeout(self.settings.ai_gateway_timeout_seconds, connect=3.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError:
            return fallback_answer(message, settings=self.settings, history=history)

        if response.status_code == status.HTTP_403_FORBIDDEN:
            return ChatGatewayAnswer(
                answer=(
                    "Puedo explicar el proceso, pero esta acción está protegida y requiere un usuario autorizado "
                    "dentro de SmartDiag504."
                ),
                audit_id=f"blocked-{secrets.token_hex(12)}",
                model="smartdiag-guardrail",
                mode="blocked",
                suggested_actions=["CONTACT_WHATSAPP"],
                sources=[],
            )
        if response.status_code != status.HTTP_200_OK:
            return fallback_answer(message, settings=self.settings, history=history)
        try:
            data = response.json()
            return ChatGatewayAnswer(
                answer=str(data["answer"])[:4000],
                audit_id=str(data["audit_id"]),
                model=str(data.get("model", "unknown")),
                mode=str(data.get("mode", "unknown")),
                suggested_actions=[str(item) for item in data.get("suggested_actions", [])][:8],
                sources=[dict(item) for item in data.get("sources", []) if isinstance(item, dict)][
                    :10
                ],
            )
        except (KeyError, TypeError, ValueError):
            return fallback_answer(message, settings=self.settings, history=history)


def get_chat_gateway(settings: Settings = Depends(get_settings)) -> ChatGateway:
    return HttpChatGateway(settings)
