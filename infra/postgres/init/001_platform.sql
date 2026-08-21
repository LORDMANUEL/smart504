CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_key TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    schema_version SMALLINT NOT NULL DEFAULT 1 CHECK (schema_version > 0),
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    actor_id TEXT,
    occurred_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_system TEXT NOT NULL DEFAULT 'smartdiag_workshop',
    correlation_id UUID,
    causation_id UUID,
    payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    signature_verified BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_event_log_aggregate
    ON event_log (aggregate_type, aggregate_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_log_type_time
    ON event_log (event_type, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_log_payload_gin
    ON event_log USING GIN (payload);

CREATE TABLE IF NOT EXISTS alert (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint TEXT NOT NULL UNIQUE,
    event_id UUID REFERENCES event_log(id) ON DELETE SET NULL,
    rule_code TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved', 'suppressed')),
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    branch_id TEXT,
    assigned_to TEXT,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by TEXT,
    resolved_at TIMESTAMPTZ,
    resolved_by TEXT,
    resolution_note TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_alert_open_priority
    ON alert (status, severity, opened_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_entity
    ON alert (entity_type, entity_id, opened_at DESC);

CREATE TABLE IF NOT EXISTS idempotency_key (
    scope TEXT NOT NULL,
    key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'processing' CHECK (state IN ('processing', 'completed', 'failed')),
    http_status INTEGER,
    response_body JSONB,
    resource_type TEXT,
    resource_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (scope, key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_expiry
    ON idempotency_key (expires_at);

CREATE TABLE IF NOT EXISTS ai_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL UNIQUE,
    user_id TEXT,
    role_name TEXT,
    session_id TEXT,
    question_hash TEXT NOT NULL,
    question_redacted TEXT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    mode TEXT NOT NULL,
    intent_decision TEXT NOT NULL,
    allowed_tools JSONB NOT NULL DEFAULT '[]'::JSONB,
    invoked_tools JSONB NOT NULL DEFAULT '[]'::JSONB,
    source_ids JSONB NOT NULL DEFAULT '[]'::JSONB,
    result_status TEXT NOT NULL CHECK (result_status IN ('completed', 'blocked', 'failed')),
    latency_ms INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
    token_usage JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ai_audit_user_time
    ON ai_audit (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_audit_status_time
    ON ai_audit (result_status, created_at DESC);

CREATE TABLE IF NOT EXISTS webhook_delivery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_key TEXT NOT NULL,
    destination TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1 CHECK (attempt > 0),
    status TEXT NOT NULL CHECK (status IN ('pending', 'delivered', 'failed', 'dead_letter')),
    http_status INTEGER,
    response_excerpt TEXT,
    next_attempt_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    UNIQUE (event_key, destination, attempt)
);

CREATE INDEX IF NOT EXISTS idx_webhook_delivery_pending
    ON webhook_delivery (status, next_attempt_at);
