from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    role: str = Field(default="advisor", min_length=2, max_length=40)
    vehicle_vin: str | None = None
    work_order_id: str | None = None


class Source(BaseModel):
    source_id: str
    title: str
    score: float


class AssistantResponse(BaseModel):
    answer: str
    audit_id: str
    model: str
    mode: str
    sources: list[Source]
    allowed_tools: list[str]


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class PublicChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    locale: str = Field(default="es-HN", min_length=2, max_length=20)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=20)
    context: list[str] = Field(default_factory=list, max_length=20)


class PublicChatResponse(BaseModel):
    answer: str
    audit_id: str
    model: str
    mode: str
    suggested_actions: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
