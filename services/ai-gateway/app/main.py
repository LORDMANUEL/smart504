from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="SmartDiag504 AI Gateway", version="0.4.0")
CHROMA_URL = os.environ.get("CHROMA_URL", "http://chromadb:8000").rstrip("/")


class ExplainRequest(BaseModel):
    subject: str = Field(min_length=3, max_length=300)
    technical_notes: str = Field(min_length=3, max_length=8000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-gateway"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{CHROMA_URL}/api/v2/heartbeat")
            if response.status_code >= 400:
                response = await client.get(f"{CHROMA_URL}/api/v1/heartbeat")
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="ChromaDB unavailable") from exc
    return {"status": "ready", "chroma": "ok"}


@app.post("/api/v1/ai/explain-for-customer")
def explain_for_customer(data: ExplainRequest) -> dict[str, object]:
    # This endpoint deliberately returns a structured draft until an approved LLM provider is configured.
    # It cannot write to inventory, invoices, payments, work-order state or vehicle release.
    return {
        "status": "provider-not-configured",
        "safe_draft": {
            "subject": data.subject,
            "summary": data.technical_notes[:800],
        },
        "write_permissions": [],
    }
