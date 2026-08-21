# SmartDiag504 v0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar un ZIP instalable que demuestre tienda, medios administrables, flujo de OT, vista Kanban/Bahías y failover de servicios, con un perfil documentado para dos VPS.

**Architecture:** ERPNext/Beveren conservan el núcleo ERP/FSM; `platform-api` implementa catálogo, reservas, proyección de OT, settings y heartbeats en PostgreSQL. Dos frontends TypeScript consumen esa API. HAProxy/Caddy distribuyen tráfico y los workers usan un lease en Valkey para ejecución única.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, Valkey 8, React, TypeScript, Vite, Vitest, Playwright, Docker Compose, HAProxy, Caddy, Restic, MariaDB Galera/garbd para el perfil multinodo.

## Global Constraints

- No duplicar contabilidad ni inventario valorizado fuera de ERPNext.
- Kanban es predeterminado y Bahías es opcional.
- Usar fotografías existentes con atribución; no generar fotografías de vehículos.
- No afirmar alta disponibilidad física sin dos hosts y testigo independiente.
- Toda transición de OT debe validarse en servidor y auditarse.
- Toda función nueva debe tener prueba automatizada antes de implementación.

---

### Task 1: Contratos de dominio y máquina de estados

**Files:**
- Create: `packages/smartdiag_domain/smartdiag_domain/work_orders.py`
- Test: `packages/smartdiag_domain/tests/test_work_orders.py`

**Interfaces:**
- Produces: `WorkOrderStatus`, `TransitionCommand`, `transition_work_order(current, command)`.

- [ ] Escribir pruebas de estados, transiciones válidas, rechazo, factura requerida e idempotencia.
- [ ] Ejecutar pruebas y confirmar fallo por implementación inexistente.
- [ ] Implementar la lógica mínima inmutable.
- [ ] Ejecutar pruebas y confirmar éxito.

### Task 2: Base de datos y migraciones

**Files:**
- Create: `services/platform-api/app/db.py`
- Create: `services/platform-api/app/models/*.py`
- Create: `services/platform-api/alembic/versions/20260812_01_v03_core.py`
- Test: `services/platform-api/tests/test_database_schema.py`

**Interfaces:**
- Produces: modelos para catálogo, imágenes, reservas, OT, eventos, settings y heartbeats.

- [ ] Probar constraints y relaciones con SQLite/PostgreSQL de prueba.
- [ ] Crear modelos y migración.
- [ ] Ejecutar migración hacia arriba y abajo.

### Task 3: Administración de productos e imágenes

**Files:**
- Create: `services/platform-api/app/routes/admin_catalog.py`
- Create: `services/platform-api/app/services/media.py`
- Create: `services/platform-api/app/services/google_images.py`
- Test: `services/platform-api/tests/test_admin_catalog.py`

**Interfaces:**
- Produces: CRUD, upload, URL externa, búsqueda Google opcional y selección de imagen principal.

- [ ] Probar validación, publicación, carga y atribución.
- [ ] Implementar repositorio y endpoints.
- [ ] Verificar OpenAPI y permisos.

### Task 4: API de OT, settings y heartbeat

**Files:**
- Create: `services/platform-api/app/routes/work_orders.py`
- Create: `services/platform-api/app/routes/settings.py`
- Create: `services/platform-api/app/routes/heartbeat.py`
- Test: `services/platform-api/tests/test_work_order_api.py`
- Test: `services/platform-api/tests/test_heartbeat.py`

**Interfaces:**
- Produces: endpoints de Kanban, transición, toggle Bahías, health y leader lease.

- [ ] Probar transiciones y auditoría.
- [ ] Probar toggle compartido.
- [ ] Probar vencimiento y adquisición del lease.
- [ ] Implementar endpoints y servicios.

### Task 5: Landing y tienda profesional

**Files:**
- Modify: `apps/public-web/src/**`
- Create: `apps/public-web/src/data/photo-attributions.ts`
- Test: `apps/public-web/src/**/*.test.tsx`

**Interfaces:**
- Consumes: catálogo público, productos, imágenes y reservas.

- [ ] Probar navegación, búsqueda, carrito y fallback de imágenes.
- [ ] Implementar layout, secciones y componentes responsivos.
- [ ] Verificar accesibilidad y responsive.

### Task 6: PWA operacional y administración

**Files:**
- Modify: `apps/ops-web/src/**`
- Test: `apps/ops-web/src/**/*.test.tsx`

**Interfaces:**
- Consumes: Kanban, settings, catálogo administrativo y media.

- [ ] Probar seis columnas y transición.
- [ ] Probar activación/desactivación de Bahías.
- [ ] Probar alta de producto y carga de imagen.
- [ ] Implementar UI y estados de error.

### Task 7: Alta disponibilidad, respaldo e instalación

**Files:**
- Modify: `compose.yaml`
- Create: `infra/ha/**`
- Create: `scripts/install-vps.sh`
- Create: `scripts/install-ha-node.sh`
- Create: `scripts/ha-smoke-test.sh`
- Modify: `scripts/backup.sh`
- Modify: `scripts/restore.sh`
- Test: `tests/test_infra_contracts.py`

**Interfaces:**
- Produces: perfil de una VPS y perfil de dos nodos con testigo.

- [ ] Probar contratos de Compose, healthchecks y secretos.
- [ ] Implementar réplicas, balanceo, leases y backups.
- [ ] Simular caída de una réplica y comprobar continuidad.
- [ ] Documentar límites físicos y quorum.

### Task 8: Verificación, previews y release

**Files:**
- Create: `docs/SMARTDIAG504_V03_OPERATIONS.md`
- Create: `docs/SMARTDIAG504_V03_VERIFICATION.md`
- Modify: `README.md`

- [ ] Ejecutar pruebas Python y TypeScript.
- [ ] Construir ambos frontends.
- [ ] Validar YAML/JSON/OpenAPI y Compose.
- [ ] Ejecutar E2E disponible y capturar previews.
- [ ] Ejecutar backup/restore de prueba disponible.
- [ ] Crear manifiesto, ZIP y checksum.
