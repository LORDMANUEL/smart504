from __future__ import annotations

from contextvars import ContextVar, Token
from contextlib import contextmanager
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class RequestIdentity:
    actor: str
    organization_id: str
    branch_id: str | None
    is_recovery: bool = False
    enforce_branch_scope: bool = False


_identity: ContextVar[RequestIdentity] = ContextVar(
    "smartdiag_request_identity",
    default=RequestIdentity(
        actor="anonymous",
        organization_id="SMARTDIAG504",
        branch_id=None,
    ),
)


def begin_request() -> Token[RequestIdentity]:
    return _identity.set(
        RequestIdentity(
            actor="anonymous",
            organization_id="SMARTDIAG504",
            branch_id=None,
        )
    )


def end_request(token: Token[RequestIdentity]) -> None:
    _identity.reset(token)


def set_staff_identity(
    *,
    actor: str,
    organization_id: str,
    branch_id: str | None,
    is_recovery: bool = False,
    enforce_branch_scope: bool = False,
) -> None:
    _identity.set(
        RequestIdentity(
            actor=actor,
            organization_id=organization_id,
            branch_id=branch_id,
            is_recovery=is_recovery,
            enforce_branch_scope=enforce_branch_scope,
        )
    )


@contextmanager
def worker_identity(*, actor: str, organization_id: str) -> Iterator[RequestIdentity]:
    """Run one background job with tenant isolation and restore prior context."""
    token = _identity.set(
        RequestIdentity(
            actor=actor,
            organization_id=organization_id,
            branch_id=None,
            is_recovery=False,
        )
    )
    try:
        yield _identity.get()
    finally:
        _identity.reset(token)


def current_identity() -> RequestIdentity:
    return _identity.get()


def audit_actor(claimed_actor: str | None = None) -> str:
    identity = current_identity()
    if identity.actor != "anonymous":
        return identity.actor
    return (claimed_actor or "anonymous").strip()
