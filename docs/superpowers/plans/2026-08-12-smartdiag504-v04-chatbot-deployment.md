# SmartDiag504 v0.4 Chatbot and VPS Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an embedded public chatbot and produce a self-contained VPS deployment package with reproducible verification.

**Architecture:** The React public site calls the persistent FastAPI `platform-api`, which validates anonymous chat sessions and proxies read-only prompts to redundant `ai-gateway` replicas through HAProxy. PostgreSQL stores chat audit data; ChromaDB and an optional OpenAI-compatible/Ollama provider enrich answers, while a deterministic FAQ fallback keeps the widget functional without credentials.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17, React 19, TypeScript 5, Vite 7, HAProxy, Caddy, Docker Compose, ChromaDB, optional Ollama/OpenAI-compatible API.

## Global Constraints

- ERPNext remains the source of truth for inventory, invoicing, payments and accounting.
- The public chatbot is read-only and cannot change work orders, inventory, invoices, payments or vehicle release.
- No plaintext client IP, session token or provider key is persisted.
- The default installation must work without an external LLM key.
- Physical HA requires two VPS hosts plus an independent witness.
- Every behavioral change is covered by an automated test before implementation.

---

### Task 1: Repair the baseline configuration and test harness

**Files:**
- Modify: `services/platform-api/app/config.py`
- Modify: `scripts/validate_repository.py`
- Modify: `tests/test_compose_contract.py`

**Interfaces:**
- Produces: deterministic environment parsing and repository validation aligned with `compose.yaml`.

- [ ] Add a failing test for comma-separated/empty CORS values.
- [ ] Implement `NoDecode` parsing and rerun the test.
- [ ] Align compose validation service names and environment keys.

### Task 2: Persistent chatbot domain and API

**Files:**
- Modify: `services/platform-api/app/models.py`
- Modify: `services/platform-api/app/schemas.py`
- Create: `services/platform-api/app/services/chat.py`
- Create: `services/platform-api/app/routes/chat.py`
- Create: `services/platform-api/alembic/versions/0002_chatbot.py`
- Modify: `services/platform-api/app/main.py`
- Create: `services/platform-api/tests/test_chat_api.py`

**Interfaces:**
- Produces: `POST /api/v1/chat/sessions`, message submission, history and close endpoints.

- [ ] Write failing tests for session token, persistence, fallback and close.
- [ ] Implement models, service, client and endpoints.
- [ ] Verify tokens are stored only as hashes and provider failures use fallback.

### Task 3: Production AI gateway and safe fallback

**Files:**
- Modify: `services/ai-gateway/smartdiag_ai_gateway/*.py`
- Modify: `services/ai-gateway/app/main.py`
- Modify: `services/ai-gateway/requirements.txt`
- Modify: `services/ai-gateway/tests/*.py`

**Interfaces:**
- Produces: `/v1/assist`, `/health`, `/ready`, deterministic FAQ mode, optional Chroma and OpenAI-compatible provider.

- [ ] Add failing tests for public FAQ and graceful provider failure.
- [ ] Implement role-aware prompt, retriever configuration and fallback.
- [ ] Verify blocked write intents remain rejected.

### Task 4: Embedded website chatbot

**Files:**
- Create: `apps/public-web/src/components/ChatWidget.tsx`
- Modify: `apps/public-web/src/lib/api.ts`
- Modify: `apps/public-web/src/types.ts`
- Modify: `apps/public-web/src/App.tsx`
- Modify: `apps/public-web/src/styles.css`
- Modify: `apps/public-web/src/App.test.tsx`
- Add: `apps/public-web/public/brand/smartdiag504-logo.png`

**Interfaces:**
- Consumes: public chat session/message API.

- [ ] Write failing UI test for open, consent and message flow.
- [ ] Implement accessible widget, quick prompts, loading/error states and persistent session.
- [ ] Verify desktop/mobile build.

### Task 5: Docker topology and installer

**Files:**
- Modify: `compose.yaml`
- Modify: `compose.preview.yaml`
- Modify: `infra/haproxy/haproxy.cfg`
- Modify: `infra/caddy/Caddyfile`
- Modify: `.env.example`
- Modify: `scripts/install-vps.sh`
- Modify: `scripts/smoke-test.sh`
- Modify: `scripts/verify.sh`

**Interfaces:**
- Produces: two AI replicas, optional local Ollama profile and reproducible VPS bootstrap.

- [ ] Add failing infrastructure contract tests.
- [ ] Implement topology, healthchecks and environment variables.
- [ ] Validate YAML, scripts and compose contracts.

### Task 6: Codex handoff, release and evidence

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/CODEX_EXECUTION_GUIDE.md`
- Modify: `docs/deployment/VPS_RUNBOOK.md`
- Modify: `README.md`
- Create: `docs/SMARTDIAG504_V04_RELEASE.md`

**Interfaces:**
- Produces: precise Codex instructions, verification commands, deployment and rollback procedure.

- [ ] Run all Python and frontend tests.
- [ ] Build both TypeScript applications.
- [ ] Validate Python, YAML, JSON and Bash syntax.
- [ ] Generate manifest, ZIP and SHA-256.
