from __future__ import annotations

import re
import unicodedata
from enum import StrEnum


class IntentDecision(StrEnum):
    READ_ONLY = "READ_ONLY"
    BLOCKED_WRITE = "BLOCKED_WRITE"


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


_BLOCKED_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(emit[ea]|gener[ae]|cre[ae]|cerr[ae])\b.{0,35}\bfactur",
        r"\b(registr[ae]|aplic[ae]|marc[ae])\b.{0,35}\b(pago|abono|efectivo|tarjeta)",
        r"\b(consum[ae]|descuent[ae]|rebaj[ae]|retir[ae])\b.{0,35}\b(inventario|existencia|repuesto|filtro|pieza)",
        r"\b(liber[ae]|entreg[ae]|cerr[ae])\b.{0,35}\b(vehiculo|carro|auto|ot|orden)",
        r"\b(delete|create|post|submit|cancel|close|invoice|charge|capture payment)\b",
    )
)


def classify_intent(prompt: str) -> IntentDecision:
    normalized = _normalize(prompt)
    if any(pattern.search(normalized) for pattern in _BLOCKED_PATTERNS):
        return IntentDecision.BLOCKED_WRITE
    return IntentDecision.READ_ONLY
