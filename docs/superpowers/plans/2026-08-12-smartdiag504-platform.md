# SmartDiag504 Platform Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear un monorepo ejecutable y desplegable que deje listos los límites, contratos, código inicial, diseño visual, Docker, pruebas y documentación de SmartDiag504.

**Architecture:** ERPNext/Frappe con Beveren y `smartdiag_workshop` controla la transacción del taller; FastAPI expone catálogo, reservas, IA y eventos; Valkey, ChromaDB, PostgreSQL y Garage S3 cumplen funciones separadas. Dos frontends TypeScript presentan la superficie pública y la operación interna.

**Tech Stack:** Frappe/ERPNext v16, Beveren FSM, Python 3.13 para servicios independientes, FastAPI, MariaDB, PostgreSQL, Valkey, ChromaDB, Garage S3, TypeScript 5.8, HTML/CSS, Caddy y Docker Compose.

## Global Constraints

- ERPNext es la única fuente de verdad para inventario, compras, facturación, pagos, caja y contabilidad.
- `Service Order` de Beveren es la OT central; no crear una segunda OT.
- MariaDB es la base transaccional Frappe; PostgreSQL solo conserva eventos, alertas, idempotencia y auditoría IA.
- Toda escritura repetible usa una clave de idempotencia.
- Las herramientas IA son de solo lectura por defecto.
- No guardar secretos en Git.
- Todo contenedor debe tener healthcheck o una justificación documentada.
- Ningún despliegue productivo consume la rama `develop` de Beveren sin fijar commit/tag.

---

### Task 1: Estructura, especificación y contratos del repositorio

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `.env.example`
- Create: `Makefile`
- Create: `docs/architecture/service-map.md`
- Create: `contracts/events.yaml`
- Create: `contracts/openapi-public.yaml`

**Interfaces:**
- Produces: nombres estables de servicios, variables de entorno y contratos consumidos por todas las tareas posteriores.

- [x] **Step 1: Crear una prueba de contrato del árbol mínimo**

```python
REQUIRED = {
    "apps/public-web",
    "apps/ops-web",
    "services/platform-api",
    "services/ai-gateway",
    "services/alerts-worker",
    "frappe-apps/smartdiag_workshop",
    "infra/frappe",
}
```

- [x] **Step 2: Ejecutar la prueba y confirmar que falla por directorios ausentes**

```bash
pytest tests/test_repository_contract.py -q
```

- [x] **Step 3: Crear la estructura y contratos**

```bash
mkdir -p apps/{public-web,ops-web} services/{platform-api,ai-gateway,alerts-worker} \
  frappe-apps/smartdiag_workshop infra/frappe contracts docs/architecture
```

- [x] **Step 4: Ejecutar la prueba y confirmar que pasa**

```bash
pytest tests/test_repository_contract.py -q
```

- [x] **Step 5: Commit**

```bash
git add README.md AGENTS.md .env.example Makefile contracts docs tests apps services frappe-apps infra
git commit -m "chore: establish SmartDiag504 monorepo contracts"
```

### Task 2: Dominio compartido y máquina de estados

**Files:**
- Create: `packages/smartdiag_domain/smartdiag_domain/vin.py`
- Create: `packages/smartdiag_domain/smartdiag_domain/work_orders.py`
- Create: `packages/smartdiag_domain/smartdiag_domain/events.py`
- Create: `packages/smartdiag_domain/smartdiag_domain/money.py`
- Test: `packages/smartdiag_domain/tests/`

**Interfaces:**
- Produces: `normalize_vin`, `is_valid_vin`, `can_transition`, `transition`, `event_key`, `calculate_line_margin`.

- [x] **Step 1: Escribir pruebas para VIN, transiciones, eventos y margen**
- [x] **Step 2: Ejecutar `pytest packages/smartdiag_domain/tests -q` y observar fallos de importación**
- [x] **Step 3: Implementar funciones puras y tipos**
- [x] **Step 4: Ejecutar pruebas y confirmar que pasan**
- [x] **Step 5: Commit con mensaje `feat: add shared automotive domain rules`**

### Task 3: API pública y BFF

**Files:**
- Create: `services/platform-api/smartdiag_platform_api/main.py`
- Create: `services/platform-api/smartdiag_platform_api/settings.py`
- Create: `services/platform-api/smartdiag_platform_api/repositories.py`
- Create: `services/platform-api/smartdiag_platform_api/security.py`
- Create: `services/platform-api/smartdiag_platform_api/routers/*.py`
- Test: `services/platform-api/tests/`

**Interfaces:**
- Produces: `/health`, `/ready`, `/api/v1/catalog/products`, `/api/v1/bookings`, `/api/v1/events`.
- Consumes: `smartdiag_domain.event_key` y adaptador Frappe.

- [x] **Step 1: Escribir pruebas de health, filtro de catálogo, idempotencia y HMAC**
- [x] **Step 2: Confirmar fallos con `pytest services/platform-api/tests -q`**
- [x] **Step 3: Implementar repositorio demo y endpoints**
- [x] **Step 4: Confirmar respuestas y esquemas con pytest**
- [x] **Step 5: Commit con mensaje `feat: add public platform api`**

### Task 4: Gateway de IA seguro

**Files:**
- Create: `services/ai-gateway/smartdiag_ai_gateway/main.py`
- Create: `services/ai-gateway/smartdiag_ai_gateway/guardrails.py`
- Create: `services/ai-gateway/smartdiag_ai_gateway/providers.py`
- Create: `services/ai-gateway/smartdiag_ai_gateway/rag.py`
- Create: `services/ai-gateway/smartdiag_ai_gateway/tools.py`
- Test: `services/ai-gateway/tests/`

**Interfaces:**
- Produces: `/health`, `/v1/assist`, `ToolRegistry`, `IntentDecision`.
- Consumes: proveedor LLM configurable y retriever ChromaDB.

- [x] **Step 1: Escribir pruebas que bloqueen facturar, pagar, consumir inventario y liberar vehículos**
- [x] **Step 2: Confirmar que las pruebas fallan**
- [x] **Step 3: Implementar guardas, proveedor demo y registro de herramientas de lectura**
- [x] **Step 4: Confirmar que todas las pruebas pasan**
- [x] **Step 5: Commit con mensaje `feat: add guarded ai gateway`**

### Task 5: Motor de alertas

**Files:**
- Create: `services/alerts-worker/smartdiag_alerts/rules.py`
- Create: `services/alerts-worker/smartdiag_alerts/worker.py`
- Create: `services/alerts-worker/smartdiag_alerts/main.py`
- Test: `services/alerts-worker/tests/`

**Interfaces:**
- Produces: `AlertRuleEngine.evaluate(event, now)` y proceso consumidor.
- Consumes: eventos definidos en `contracts/events.yaml`.

- [x] **Step 1: Escribir pruebas para promesa vencida, cotización pendiente, repuesto pendiente, técnico inactivo y diferencia de caja**
- [x] **Step 2: Confirmar fallos**
- [x] **Step 3: Implementar reglas deterministas y severidad**
- [x] **Step 4: Confirmar que pasan**
- [x] **Step 5: Commit con mensaje `feat: add workshop alert rules`**

### Task 6: Aplicación Frappe automotriz

**Files:**
- Create: `frappe-apps/smartdiag_workshop/pyproject.toml`
- Create: `frappe-apps/smartdiag_workshop/smartdiag_workshop/hooks.py`
- Create: `frappe-apps/smartdiag_workshop/smartdiag_workshop/setup/`
- Create: `frappe-apps/smartdiag_workshop/smartdiag_workshop/smartdiag_workshop/doctype/`
- Create: `frappe-apps/smartdiag_workshop/smartdiag_workshop/events/`

**Interfaces:**
- Produces: DocTypes `SmartDiag Vehicle`, `Vehicle Check In`, `Diagnostic Session`, `Workshop Bay`, `Part Request`, `Workshop Quality Check`, `Workshop Warranty Claim` y `SmartDiag Event Outbox`.
- Extiende: `Service Request`, `Service Quotation`, `Service Order`, `Service Appointment`, `Item`, `Customer` y `Employee` con campos prefijados `sd_`.

- [x] **Step 1: Escribir validadores de JSON para DocTypes y hooks**
- [x] **Step 2: Confirmar que fallan por archivos ausentes**
- [x] **Step 3: Crear app, DocTypes, custom fields y handlers**
- [x] **Step 4: Ejecutar validadores, compileall y pruebas de dominio**
- [x] **Step 5: Commit con mensaje `feat: scaffold SmartDiag Frappe app`**

### Task 7: Capa controlada de Beveren

**Files:**
- Create: `infra/frappe/patches/beveren/0001-v16-compat.patch`
- Create: `infra/frappe/BEVEREN_PATCH_STATUS.md`
- Create: `infra/frappe/Containerfile`
- Create: `infra/frappe/apps.json`

**Interfaces:**
- Produce: imagen Frappe personalizada con ERPNext, Beveren parcheado, dominio compartido y SmartDiag app.

- [x] **Step 1: Registrar commit upstream y checksum del parche**
- [x] **Step 2: Incorporar las correcciones verificables del PR de compatibilidad v16**
- [x] **Step 3: Documentar el gate pendiente de selección de artículos**
- [x] **Step 4: Crear Containerfile reproducible**
- [x] **Step 5: Commit con mensaje `build: add pinned Beveren integration layer`**

### Task 8: Sistema visual compartido

**Files:**
- Create: `packages/design-system/tokens.css`
- Create: `packages/design-system/components.css`
- Create: `packages/design-system/brand.ts`
- Create: `packages/design-system/assets/smartdiag504-mark.svg`
- Create: `docs/brand/BRAND_SYSTEM.md`

**Interfaces:**
- Produce: tokens consumidos por `public-web` y `ops-web`.

- [x] **Step 1: Definir prueba estática de tokens obligatorios**
- [x] **Step 2: Confirmar fallo**
- [x] **Step 3: Implementar paleta, tipografía, espaciado, estados y marca provisional**
- [x] **Step 4: Confirmar prueba**
- [x] **Step 5: Commit con mensaje `feat: add SmartDiag visual system`**

### Task 9: Landing, tienda, reserva y portal público

**Files:**
- Create: `apps/public-web/index.html`
- Create: `apps/public-web/src/app.ts`
- Create: `apps/public-web/styles.css`
- Create: `apps/public-web/tsconfig.json`
- Create: `apps/public-web/Dockerfile`

**Interfaces:**
- Consume: `/api/v1/catalog/products` y `/api/v1/bookings`.
- Produce: experiencia responsive con catálogo, búsqueda, carrito, reserva y acceso al portal.

- [x] **Step 1: Escribir pruebas Playwright de navegación, filtro, carrito y reserva**
- [x] **Step 2: Confirmar fallos contra página vacía**
- [x] **Step 3: Implementar interfaz TypeScript y estados locales demo**
- [x] **Step 4: Ejecutar TypeScript y pruebas visuales funcionales**
- [x] **Step 5: Commit con mensaje `feat: add public storefront and booking experience`**

### Task 10: PWA operacional

**Files:**
- Create: `apps/ops-web/index.html`
- Create: `apps/ops-web/src/app.ts`
- Create: `apps/ops-web/styles.css`
- Create: `apps/ops-web/manifest.webmanifest`
- Create: `apps/ops-web/Dockerfile`

**Interfaces:**
- Produce: dashboard, Kanban, bahías, alertas, repuestos y resumen de caja.

- [x] **Step 1: Escribir pruebas Playwright para cambiar vistas y mover una OT en demo**
- [x] **Step 2: Confirmar fallos**
- [x] **Step 3: Implementar PWA TypeScript**
- [x] **Step 4: Ejecutar compilación y pruebas**
- [x] **Step 5: Commit con mensaje `feat: add workshop operations pwa`**

### Task 11: Docker y proxy

**Files:**
- Create: `compose.yaml`
- Create: `compose.preview.yaml`
- Create: `infra/caddy/Caddyfile`
- Create: `infra/postgres/init/001_platform.sql`
- Create: `scripts/install-vps.sh`
- Create: `scripts/bootstrap-site.sh`

**Interfaces:**
- Produce: redes, volúmenes, healthchecks y rutas por dominio.

- [x] **Step 1: Escribir validación YAML y reglas de servicios obligatorios**
- [x] **Step 2: Confirmar fallos**
- [x] **Step 3: Crear Compose completo y modo preview**
- [x] **Step 4: Ejecutar parser YAML y `docker compose config` cuando Docker esté disponible**
- [x] **Step 5: Commit con mensaje `build: add VPS container topology`**

### Task 12: Operación, seguridad y observabilidad

**Files:**
- Create: `scripts/backup.sh`
- Create: `scripts/restore.sh`
- Create: `scripts/verify.sh`
- Create: `infra/monitoring/prometheus.yml`
- Create: `docs/deployment/VPS_RUNBOOK.md`
- Create: `docs/security/THREAT_MODEL.md`

**Interfaces:**
- Produce: procedimientos repetibles de instalación, verificación, respaldo y recuperación.

- [x] **Step 1: Validar sintaxis shell con `bash -n`**
- [x] **Step 2: Implementar scripts fail-fast y manifiesto de backup**
- [x] **Step 3: Documentar firewall, DNS, TLS, secretos y restauración**
- [x] **Step 4: Repetir validación shell**
- [x] **Step 5: Commit con mensaje `ops: add security backup and verification runbooks`**

### Task 13: CI, QA y handoff a Codex

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/build-images.yml`
- Create: `docs/testing/ACCEPTANCE_TESTS.md`
- Create: `docs/CODEX_EXECUTION_GUIDE.md`
- Create: `MANIFEST.sha256`

**Interfaces:**
- Produce: gate de calidad y guía de ejecución incremental.

- [x] **Step 1: Ejecutar suite Python completa**
- [x] **Step 2: Ejecutar compilación TypeScript**
- [x] **Step 3: Ejecutar validación JSON/YAML/shell**
- [x] **Step 4: Renderizar las dos superficies y capturar desktop/móvil**
- [x] **Step 5: Generar manifiesto y ZIP; comprobar integridad**
- [x] **Step 6: Commit con mensaje `ci: finalize SmartDiag504 platform skeleton`**
