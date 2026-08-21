from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import ChatMessage
from app.schemas import (
    ChatHistoryRead,
    ChatMessageCreate,
    ChatReplyRead,
    ChatSessionClosed,
    ChatSessionCreate,
    ChatSessionCreated,
)
from app.services.chatbot import (
    ChatGateway,
    build_public_context,
    create_session,
    enforce_rate_limit,
    find_existing_exchange,
    get_chat_gateway,
    load_history,
    require_session,
    utcnow,
)
from app.services.public_abuse import enforce_public_limit, reject_honeypot

router = APIRouter(prefix="/api/v1/chat", tags=["public-chat"])


def _client_ip(request: Request) -> str | None:
    # Uvicorn accepts forwarded headers only from FORWARDED_ALLOW_IPS. Never
    # trust a browser-supplied X-Forwarded-For value here.
    return request.client.host if request.client else None


@router.post(
    "/sessions",
    response_model=ChatSessionCreated,
    status_code=status.HTTP_201_CREATED,
)
def start_chat_session(
    data: ChatSessionCreate,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ChatSessionCreated:
    reject_honeypot(data.website)
    enforce_public_limit(
        request,
        settings,
        surface="chat-session",
        limit=settings.public_chat_session_limit_per_minute,
    )
    session, raw_token, _welcome = create_session(
        db,
        locale=data.locale,
        page_url=data.page_url,
        referrer=data.referrer or request.headers.get("referer"),
        client_ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        settings=settings,
    )
    return ChatSessionCreated(
        session_id=session.id,
        session_token=raw_token,
        expires_at=session.expires_at,
        welcome_message=settings.chatbot_welcome_message,
        quick_prompts=list(settings.chatbot_quick_prompts),
        privacy_notice=settings.chatbot_privacy_notice,
    )


@router.get("/sessions/{session_id}/messages", response_model=ChatHistoryRead)
def chat_history(
    session_id: str,
    x_chat_session_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ChatHistoryRead:
    require_session(
        db,
        session_id=session_id,
        token=x_chat_session_token,
        settings=settings,
    )
    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(100)
        )
    )
    return ChatHistoryRead(session_id=session_id, messages=messages)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatReplyRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_chat_message(
    session_id: str,
    data: ChatMessageCreate,
    request: Request,
    response: Response,
    x_chat_session_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    gateway: ChatGateway = Depends(get_chat_gateway),
) -> ChatReplyRead:
    enforce_public_limit(
        request,
        settings,
        surface="chat-message",
        limit=settings.public_chat_message_limit_per_minute,
    )
    session = require_session(
        db,
        session_id=session_id,
        token=x_chat_session_token,
        settings=settings,
    )
    existing = find_existing_exchange(
        db,
        session_id=session_id,
        client_message_id=data.client_message_id,
    )
    if existing and existing[1]:
        response.status_code = status.HTTP_200_OK
        user_message, assistant_message = existing
        assert assistant_message is not None
        return ChatReplyRead(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            audit_id=assistant_message.audit_id,
            mode=assistant_message.mode or "unknown",
            suggested_actions=list(assistant_message.suggested_actions),
        )

    prior_messages = load_history(
        db,
        session_id=session_id,
        limit=settings.chatbot_max_history_messages,
    )
    history = [
        {"role": item.role, "content": item.content}
        for item in prior_messages
        if item.role in {"user", "assistant"}
    ]
    context = build_public_context(db, message=data.message, settings=settings)

    if existing:
        user_message = existing[0]
    else:
        enforce_rate_limit(session=session, settings=settings)
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=data.message,
            client_message_id=data.client_message_id,
            suggested_actions=[],
            sources=[],
            metadata_json={},
        )
        db.add(user_message)
        session.last_message_at = utcnow()
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            replay = find_existing_exchange(
                db,
                session_id=session_id,
                client_message_id=data.client_message_id,
            )
            if replay is None:
                raise
            user_message = replay[0]
            if replay[1] is not None:
                response.status_code = status.HTTP_200_OK
                assistant_message = replay[1]
                return ChatReplyRead(
                    session_id=session_id,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    audit_id=assistant_message.audit_id,
                    mode=assistant_message.mode or "unknown",
                    suggested_actions=list(assistant_message.suggested_actions),
                )
        else:
            db.refresh(user_message)

    answer = await gateway.answer(
        message=data.message,
        history=history,
        context=context,
        locale=session.locale,
    )
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer.answer,
        reply_to_message_id=user_message.id,
        provider="ai-gateway" if answer.mode not in {"fallback", "blocked"} else "smartdiag",
        audit_id=answer.audit_id,
        model=answer.model,
        mode=answer.mode,
        blocked=answer.mode == "blocked",
        suggested_actions=answer.suggested_actions,
        sources=answer.sources,
        metadata_json={},
    )
    db.add(assistant_message)
    session.last_message_at = utcnow()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        replay = find_existing_exchange(
            db,
            session_id=session_id,
            client_message_id=data.client_message_id,
        )
        if replay is None or replay[1] is None:
            raise
        response.status_code = status.HTTP_200_OK
        user_message, assistant_message = replay
    else:
        db.refresh(assistant_message)

    return ChatReplyRead(
        session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
        audit_id=assistant_message.audit_id,
        mode=assistant_message.mode or "unknown",
        suggested_actions=list(assistant_message.suggested_actions),
    )


@router.post("/sessions/{session_id}/close", response_model=ChatSessionClosed)
def close_chat_session(
    session_id: str,
    x_chat_session_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ChatSessionClosed:
    session = require_session(
        db,
        session_id=session_id,
        token=x_chat_session_token,
        settings=settings,
        allow_closed=True,
    )
    if session.status != "CLOSED":
        session.status = "CLOSED"
        session.closed_at = utcnow()
        db.commit()
        db.refresh(session)
    assert session.closed_at is not None
    return ChatSessionClosed(session_id=session.id, status="CLOSED", closed_at=session.closed_at)
