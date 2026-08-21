# SmartDiag504 v0.4 Chatbot and Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an installable SmartDiag504 v0.4 release with a persisted public chatbot, redundant AI gateway containers, real landing assets, vendored Beveren FSM, tests, installer and Codex VPS handoff.

**Architecture:** The React public site creates an anonymous chat session through `platform-api`. FastAPI persists the session and messages in PostgreSQL, gathers public catalog/business context and calls two internal `ai-gateway` replicas through HAProxy. The AI gateway provides a deterministic offline fallback and optional OpenAI-compatible LLM mode.

**Tech Stack:** React 19, TypeScript, Vite, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, HAProxy, Caddy, Docker Compose, ERPNext/Frappe v16, Beveren FSM, ChromaDB.

## Global Constraints

- ERPNext remains the source of truth for stock, invoices, payments, cash and accounting.
- No browser-visible secret or direct LLM credential.
- Public chatbot has no financial or inventory write tools.
- Store only hashed chat session tokens.
- All new behavior follows failing-test-first TDD.
- Docker runtime claims require execution on a host with Docker; local validation may only prove static contracts.

---

### Task 1: Chat persistence and API

**Files:**
- Create: `services/platform-api/app/routes/chat.py`
- Create: `services/platform-api/app/services/chatbot.py`
- Modify: `services/platform-api/app/models.py`
- Modify: `services/platform-api/app/schemas.py`
- Create: `services/platform-api/alembic/versions/0002_public_chat.py`
- Test: `services/platform-api/tests/test_chat_api.py`

**Interfaces:**
- Produces: session creation, authenticated history and idempotent message endpoints.
- Consumes: `ChatGateway.answer(...)`.

### Task 2: Public AI gateway mode

**Files:**
- Create: `services/ai-gateway/smartdiag_ai_gateway/public_chat.py`
- Modify: `services/ai-gateway/smartdiag_ai_gateway/main.py`
- Modify: `services/ai-gateway/smartdiag_ai_gateway/models.py`
- Modify: `services/ai-gateway/smartdiag_ai_gateway/providers.py`
- Test: `services/ai-gateway/tests/test_public_chat.py`

**Interfaces:**
- Produces: internal `POST /v1/public-chat` with deterministic fallback and optional LLM.

### Task 3: Landing chatbot widget

**Files:**
- Create: `apps/public-web/src/components/ChatWidget.tsx`
- Modify: `apps/public-web/src/lib/api.ts`
- Modify: `apps/public-web/src/types.ts`
- Modify: `apps/public-web/src/App.tsx`
- Modify: `apps/public-web/src/styles.css`
- Test: `apps/public-web/src/components/ChatWidget.test.tsx`

**Interfaces:**
- Consumes: public chat API.
- Produces: accessible floating chat widget.

### Task 4: Docker redundancy and deployment

**Files:**
- Modify: `compose.yaml`
- Modify: `compose.preview.yaml`
- Modify: `infra/haproxy/haproxy.cfg`
- Modify: `.env.example`
- Modify: `scripts/install-vps.sh`
- Modify: `scripts/smoke-test.sh`
- Test: `tests/test_chatbot_release_contract.py`

**Interfaces:**
- Produces: redundant AI gateway and end-to-end health checks.

### Task 5: Complete dependencies and real assets

**Files:**
- Populate: `vendor/beveren_fsm/**`
- Modify: `infra/frappe/patches/beveren/0001-v16-compat.patch`
- Populate: `apps/public-web/public/images/stock/**`
- Populate: `services/platform-api/seed_assets/products/**`
- Modify: attribution and licensing docs.

### Task 6: Verification and release

**Files:**
- Modify: `README.md`
- Modify: `docs/CODEX_EXECUTION_GUIDE.md`
- Create: `CODEX_VPS_DEPLOY_PROMPT.md`
- Modify: `scripts/package-release.sh`
- Create: `docs/testing/V04_VERIFICATION_REPORT.md`

**Verification:** Python tests, frontend tests/builds, YAML/JSON, Compose config parser, shell syntax, manifest, ZIP integrity and checksum.
