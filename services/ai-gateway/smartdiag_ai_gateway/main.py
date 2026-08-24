from __future__ import annotations

import hmac
import os
import uuid

from fastapi import FastAPI, Header, HTTPException, status

from .guardrails import IntentDecision, classify_intent
from .models import (
    AssistantRequest,
    AssistantResponse,
    PublicChatRequest,
    PublicChatResponse,
    Source,
)
from .providers import DemoProvider, LLMProvider, OpenAICompatibleProvider
from .public_chat import answer_public_chat
from .rag import ChromaRetriever, NullRetriever, Retriever
from .tools import ToolRegistry, build_default_registry


def _provider_from_env(*, testing: bool) -> LLMProvider:
    provider = "demo" if testing else os.getenv("LLM_PROVIDER", "demo").casefold()
    if provider == "demo":
        return DemoProvider()
    if provider in {"openai", "openai-compatible", "ollama"}:
        return OpenAICompatibleProvider(
            base_url=os.getenv("LLM_BASE_URL", "http://ollama:11434/v1"),
            api_key=os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            model=os.getenv("LLM_MODEL", "qwen2.5:7b-instruct"),
            timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "90")),
        )
    raise RuntimeError(f"Unsupported LLM_PROVIDER: {provider}")


def _retriever_from_env() -> Retriever:
    if os.getenv("CHROMA_ENABLED", "false").casefold() not in {"1", "true", "yes", "on"}:
        return NullRetriever()
    raw_url = os.getenv("CHROMA_URL", "http://chromadb:8000")
    without_scheme = raw_url.split("://", 1)[-1]
    host, _, port = without_scheme.partition(":")
    return ChromaRetriever(
        host=host or "chromadb",
        port=int(port or "8000"),
        collection_name=os.getenv("CHROMA_COLLECTION", "smartdiag_knowledge"),
    )


def _require_internal_token(token: str | None) -> None:
    expected = os.getenv("AI_GATEWAY_INTERNAL_TOKEN", "")
    if not expected or not token or not hmac.compare_digest(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid AI gateway credentials",
        )


def create_app(*, testing: bool = False) -> FastAPI:
    application = FastAPI(title="SmartDiag504 AI Gateway", version="0.4.0", redoc_url=None)
    application.state.provider = _provider_from_env(testing=testing)
    application.state.retriever = _retriever_from_env()
    application.state.tools = build_default_registry()

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ai-gateway", "version": "0.4.0"}

    @application.get("/ready")
    async def ready() -> dict[str, object]:
        expected = os.getenv("AI_GATEWAY_INTERNAL_TOKEN", "")
        environment = os.getenv("ENVIRONMENT", "development").casefold()
        if not expected or (environment == "production" and expected.startswith("change-")):
            raise HTTPException(status_code=503, detail="AI gateway secret is not configured")
        provider = application.state.provider
        if environment == "production" and isinstance(provider, DemoProvider):
            raise HTTPException(status_code=503, detail="Production LLM provider is not configured")
        try:
            provider_ready = await provider.ready()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Configured LLM provider is unavailable") from exc
        if not provider_ready:
            raise HTTPException(status_code=503, detail="Configured LLM model is unavailable")
        return {
            "status": "ready",
            "provider": type(provider).__name__,
            "model": getattr(provider, "model", "demo"),
            "provider_status": "ok",
            "retriever": type(application.state.retriever).__name__,
        }

    @application.post("/v1/assist", response_model=AssistantResponse)
    async def assist(
        payload: AssistantRequest,
        x_ai_gateway_token: str | None = Header(default=None),
    ) -> AssistantResponse:
        _require_internal_token(x_ai_gateway_token)
        if classify_intent(payload.question) is IntentDecision.BLOCKED_WRITE:
            raise HTTPException(
                status_code=403,
                detail=(
                    "La IA de SmartDiag504 opera en lectura segura. "
                    "La acción solicitada requiere una herramienta autorizada y confirmación humana."
                ),
            )
        retriever: Retriever = application.state.retriever
        registry: ToolRegistry = application.state.tools
        chunks = retriever.search(payload.question, limit=5)
        result = await application.state.provider.complete(
            prompt=payload.question,
            context=[f"{chunk.title}: {chunk.text}" for chunk in chunks],
        )
        return AssistantResponse(
            answer=result.text,
            audit_id=str(uuid.uuid4()),
            model=result.model,
            mode=result.mode,
            sources=[Source(source_id=chunk.source_id, title=chunk.title, score=chunk.score) for chunk in chunks],
            allowed_tools=[tool.name for tool in registry.allowed_for(payload.role) if tool.read_only],
        )

    @application.post("/v1/public-chat", response_model=PublicChatResponse)
    async def public_chat(
        payload: PublicChatRequest,
        x_ai_gateway_token: str | None = Header(default=None),
    ) -> PublicChatResponse:
        _require_internal_token(x_ai_gateway_token)
        if classify_intent(payload.message) is IntentDecision.BLOCKED_WRITE:
            raise HTTPException(
                status_code=403,
                detail=(
                    "El asistente público no puede ejecutar facturas, pagos, inventario ni entregas. "
                    "Puede explicar el proceso o dirigirle al personal autorizado."
                ),
            )
        retriever: Retriever = application.state.retriever
        chunks = retriever.search(payload.message, limit=4)
        rag_context = [f"RAG|{chunk.title}|{chunk.text}" for chunk in chunks]
        result = await answer_public_chat(
            provider=application.state.provider,
            message=payload.message,
            history=[item.model_dump() for item in payload.history],
            context=[*payload.context, *rag_context],
        )
        return PublicChatResponse(
            answer=result.answer,
            audit_id=str(uuid.uuid4()),
            model=result.model,
            mode=result.mode,
            suggested_actions=result.suggested_actions,
            sources=[
                Source(source_id=chunk.source_id, title=chunk.title, score=chunk.score)
                for chunk in chunks
            ],
        )

    return application


app = create_app()
