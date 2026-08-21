# Arquitectura de SmartDiag504

Este documento es la referencia viva de arquitectura para ingeniería y operación. Debe actualizarse cuando cambien la propiedad de datos, los servicios, el despliegue o los límites de seguridad.

## 1. Estructura del proyecto

```text
smartdiag504-platform-v0.4.0/
├── apps/
│   ├── public-web/                 # Landing, tienda, acceso y portal del cliente
│   └── ops-web/                    # Operación del taller, ventas, bodega y administración
├── services/
│   ├── platform-api/               # BFF, persistencia operacional e integraciones
│   ├── ai-gateway/                 # Chat, guardrails, Ollama y RAG
│   ├── alerts-worker/              # Evaluación de alertas
│   └── heartbeat-agent/            # Señales de salud de réplicas
├── frappe-apps/smartdiag_workshop/ # Extensión automotriz de Frappe/Beveren
├── packages/smartdiag_domain/      # Reglas puras de dominio
├── contracts/                      # Contratos OpenAPI y eventos
├── infra/                          # ERPNext, proxy, observabilidad, backup y HA
├── scripts/                        # Validación, despliegue, backup y utilidades
├── docs/                           # Arquitectura, operación, producto, pruebas y seguridad
├── compose*.yaml                   # Variantes local, demo y Coolify
├── AGENTS.md                       # Reglas obligatorias de desarrollo
└── ARCHITECTURE.md                 # Este documento
```

El repositorio funciona como monorepo poliglota, aunque no usa un orquestador de workspaces en la raíz.

## 2. Diagrama general

```text
Cliente/empleado
      │ HTTPS
      ▼
Coolify/Traefik ──► gateway ──┬──► public-web
                              ├──► ops-web
                              └──► platform-api ──┬──► PostgreSQL
                                                  ├──► Valkey
                                                  ├──► ai-gateway ──► Ollama/ChromaDB
                                                  └──► adaptador Frappe/ERPNext

Arquitectura financiera efectiva en el VPS de pruebas:
platform-api ──► ERPNext/Frappe/Beveren ──► MariaDB
                         │
                         └──► eventos/proyecciones regenerables en PostgreSQL
```

El override efectivo de Coolify exige Frappe y verificación estricta. Para OT, la API confirma el `Service Order` antes de responder éxito; PostgreSQL conserva una proyección operativa, el outbox idempotente, la referencia ERP y el estado de conciliación. El Compose base sigue siendo portable y no debe interpretarse como el estado efectivo sin su override.

## 3. Componentes principales

### 3.1. Web pública

**Propósito:** promoción del taller, catálogo, compatibilidad por vehículo/VIN, carrito, pedidos, citas, acceso y portal del cliente.

**Tecnologías:** React 19, TypeScript 5.8, Vite 7 y Vitest.

**Despliegue:** imagen Nginx detrás del gateway de Coolify.

### 3.2. Portal operativo

**Propósito:** Kanban, OTs, citas, cotizaciones, mostrador, caja, bodega, calidad, CRM, publicidad, personal, documentos y configuración.

**Tecnologías:** React 19, TypeScript 5.8, Vite 7 y Vitest.

**Despliegue:** imagen Nginx detrás del gateway. La navegación aplica permisos de interfaz, pero toda autorización efectiva debe permanecer en la API.

### 3.3. Platform API

**Propósito:** BFF de ambas aplicaciones, autenticación, reglas operativas, persistencia, PDF/Excel, eventos e integración ERP.

**Tecnologías:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic, FastAPI Users, ReportLab/xhtml2pdf y openpyxl.

**Límite:** no debe convertirse en un segundo libro contable, stock ledger u OT autoritativa. Las OTs locales son proyecciones conciliadas: altas, ediciones técnicas, mano de obra, evidencias y solicitudes de repuesto reencolan un UPSERT; en modo estricto la API no confirma éxito hasta obtener el identificador ERP. `POST /api/v1/operations/work-orders/{id}/reconcile` vuelve a leer Beveren y actualiza la proyección con eventos auditables.

### 3.4. AI Gateway

**Propósito:** respuestas públicas, fallback determinista, proveedor compatible, Ollama local, recuperación RAG y guardrails.

**Estado:** infraestructura funcional; el corpus de demostración y las herramientas declarativas no equivalen a un asistente técnico certificado.

### 3.5. Frappe, ERPNext y Beveren

**Propósito objetivo:** fuente autoritativa de clientes, artículos, inventario, compras, cotizaciones de servicio, OT, facturas, pagos y contabilidad.

**Estado:** el stack separado de ERPNext/HRMS/Beveren y la app `smartdiag_workshop` están desplegados. La imagen 34 agrega al `Service Order` los campos `sd_platform_*` para diagnóstico, técnicos, bahía, repuestos, mano de obra, evidencias y fecha de actualización. El Compose administrado del demo requiere el stack/override externo y no incluye MariaDB por sí solo.

### 3.6. Workers y disponibilidad

Alerts Worker evalúa reglas; Heartbeat Agent registra salud; HAProxy y los manifiestos completos describen redundancia A/B. El demo Coolify activo usa una sola réplica por servicio, por lo que no tiene alta disponibilidad física ni de aplicación certificada.

## 4. Almacenes de datos

### 4.1. PostgreSQL 17

Guarda identidad operativa, citas, pedidos, modelos/proyecciones del demo, eventos, auditoría, CRM, plantillas y heartbeats. El esquema servido llega a `0031_client_credit_amount`; nómina, vouchers y solicitudes de crédito locales son proyecciones operativas, no libros contables.

No debe ser la fuente final de contabilidad, valoración de inventario o documentos fiscales.

### 4.2. MariaDB de ERPNext

Almacén objetivo de ERPNext/Frappe/Beveren. En el demo administrado no forma parte del Compose base; su estado efectivo depende del override externo.

### 4.3. Valkey

Cache, coordinación y estado temporal. No es fuente de verdad.

### 4.4. ChromaDB

Índice vectorial para RAG. El corpus actual es de demostración y necesita gobierno, versionado, fuentes y evaluación.

### 4.5. Evidencias y medios

Las evidencias nuevas de OT usan Garage/S3 privado dentro del VPS y sólo se leen a través de la API autenticada. Los medios públicos de marca, catálogo y campañas continúan en `/media`. Antes de producción real faltan política de retención, análisis antivirus y réplica cifrada fuera del VPS.

## 5. Integraciones externas

| Integración | Propósito | Estado |
|---|---|---|
| ERPNext/Frappe/Beveren | OT, inventario, ventas, pagos y contabilidad | Activo y estricto; OT y mostrador conciliados, certificación fiscal externa pendiente |
| Ollama | Modelo local pequeño | Desplegado en demo |
| ChromaDB | RAG | Desplegado con corpus demo |
| SMTP | Enlaces de autorización | Parcial y condicionado a configuración |
| Google Programmable Search | Candidatos de imágenes | Opcional |
| Meta/WhatsApp Business | Atención y notificaciones | No integrado |
| Adquirente/datáfono | Pago con tarjeta | No integrado; sólo se registra referencia externa |
| SAR/CAI | Documentos fiscales hondureños | No certificado |

## 6. Despliegue e infraestructura

**Proveedor:** VPS administrada con Coolify; DNS/TLS gestionados en la entrada de la plataforma.

**Demo activo:** gateway, public-web, ops-web, platform-api, PostgreSQL, Valkey, ChromaDB, Ollama y AI Gateway. Las bases no publican puertos del host.

**CI/CD:** GitHub Actions y scripts del repositorio. Falta consolidar una liberación reproducible del árbol actualmente modificado, fijar imágenes por digest y demostrar SBOM, escaneo y firma en el artefacto desplegado.

**Observabilidad:** healthchecks, heartbeat, outbox ERP y eventos de conciliación. Faltan métricas, trazas y alertas externas. El readiness interno comprobado reporta base, Valkey, Frappe, esquema, IA y seguridad en `ok`.

**Continuidad:** existen runbooks y diseño de dos nodos, pero el demo activo no demuestra réplica, backup externo cifrado ni HA física.

## 7. Seguridad

**Autenticación:** cookie segura para personal mediante FastAPI Users/JWT y sesión separada para clientes demo.

**Autorización:** RBAC por roles, MFA TOTP, bloqueo por intentos y revocación de sesiones. Continúa pendiente certificar aislamiento por organización/sucursal en toda la superficie y recuperación productiva por correo.

**Auditoría:** los actores de negocio deben derivarse de la sesión. Todavía existen actores `*-demo` enviados desde el frontend y campos de actor controlables por formulario.

**Secretos:** variables de entorno/runtime; no deben reutilizarse secretos entre chat y personal ni conservarse tokens universales en el navegador.

**Evidencia:** las fotos de OT no deben permanecer públicamente accesibles en producción.

## 8. Desarrollo y pruebas

**Gates declarados:** `make test`, `make typecheck` y `make validate`.

**Estado comprobado en el VPS el 2026-08-21:**

- suite API completa aprobada dentro de la imagen desplegable, incluida convergencia y reconciliación de OT;
- 19 pruebas Vitest de operaciones aprobadas;
- 6 pruebas Vitest de web pública aprobadas;
- builds TypeScript/Vite de ambas aplicaciones aprobados;
- validación de 732 archivos, 29 YAML, 35 JSON, 38 servicios y Compose aprobada;
- recorrido servido `OT-2026-000009` ↔ `SVC-ORD-2026-00009` aprobado con alta, edición y reconciliación `SYNCED`.

Los E2E históricos usan fixtures/bundles y no certifican todavía el React servido, la base, ERPNext, roles, impresoras o datáfono de extremo a extremo.

## 9. Roadmap de arquitectura

1. Extender la confirmación estricta ya activa en OT y mostrador a cualquier flujo residual de cotización, stock, factura o pago que todavía pueda quedar pendiente.
2. Implementar tenant/organización/sucursal en modelos, consultas, sesiones, índices y pruebas de aislamiento.
3. Derivar actor y permisos desde la sesión; completar MFA, recuperación y segregación de funciones.
4. Crear una cola de sincronización ERP general, idempotente, conciliable y observable.
5. Proteger evidencias y documentos; certificar fiscalidad, impresión y backup/restore.
6. Completar RRHH/HRMS, compras, proveedores, importación y reportería.
7. Completar ecommerce, notificaciones, CRM, marketing, Hub Social y usados.
8. Certificar E2E por rol, accesibilidad, carga, seguridad y recuperación.

El detalle y los criterios de salida están en [docs/product/AUDITORIA_BRECHAS_Y_ROADMAP_2026-08-14.md](docs/product/AUDITORIA_BRECHAS_Y_ROADMAP_2026-08-14.md).

## 10. Identificación

**Proyecto:** SmartDiag504 Platform v0.4.0  
**Repositorio remoto:** no determinado desde la auditoría local  
**Equipo:** SmartDiag504  
**Última actualización:** 2026-08-21

## 11. Glosario

| Término | Definición |
|---|---|
| OT | Orden de trabajo del taller |
| BFF | API orientada a las necesidades de los frontends |
| Beveren | Aplicación Frappe usada como base del flujo de servicio |
| CAI | Código de Autorización de Impresión usado en Honduras |
| DTC | Código de diagnóstico del vehículo |
| RAG | Recuperación de conocimiento para complementar respuestas de IA |
| SoD | Segregación de funciones y autorizaciones incompatibles |
| Proyección | Copia regenerable para consulta; no es fuente autoritativa |
