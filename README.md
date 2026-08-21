# SmartDiag504 Platform v0.4.0

Plataforma integral para **taller automotriz, diagnóstico, órdenes de trabajo, técnicos, repuestos, caja, facturación, tienda web, reservas, portal operacional, alertas y chatbot público**.

La solución utiliza ERPNext/Frappe como núcleo financiero y de inventario, Beveren FSM como base de servicio, y la aplicación propia `smartdiag_workshop` para el dominio automotriz. El navegador nunca se conecta directamente a MariaDB ni PostgreSQL.

## Funcionalidad incluida

- Landing page profesional con fotografías reales existentes y logo de SmartDiag504.
- Catálogo y tienda de repuestos con carrito y solicitud de pedido.
- Carga de fotografías por administrador y descubrimiento opcional de candidatos mediante Google Programmable Search.
- Chatbot incrustado en la misma web para servicios, reservas, repuestos y orientación del proceso de OT.
- Modo de chatbot seguro sin proveedor externo, modo LLM compatible con OpenAI y modo local mediante Ollama.
- Reservas web y recepción del vehículo.
- Vehículos, VIN, síntomas, diagnóstico, DTC, evidencia y trazabilidad.
- Mano de obra, múltiples técnicos, tiempos y control de calidad.
- Kanban operacional como vista predeterminada y bahías como módulo opcional.
- ERPNext para artículos, bodegas, compras, POS, caja, facturas, pagos y contabilidad.
- PostgreSQL para proyección operacional, idempotencia, eventos, chatbot y auditoría.
- ChromaDB para conocimiento técnico autorizado; Valkey para estado temporal y coordinación.
- Dos réplicas de web, PWA, API, IA, heartbeat y alertas dentro de la misma VPS.
- Backups verificables, restauración destructiva controlada, observabilidad y documentación de HA física.

## Estados oficiales de la OT

La misma `Service Order` de Beveren/ERPNext se proyecta en el tablero SmartDiag504. No se crea una segunda OT.

```text
CREATED
→ QUOTED_BY_TECHNICIAN
→ PENDING_CUSTOMER_APPROVAL
→ PENDING_PARTS
→ READY_TO_INVOICE
→ INVOICED
```

## Estructura

```text
apps/public-web/                   Landing, tienda, reserva y chatbot
apps/ops-web/                      PWA de operación, Kanban, bahías y pedidos
frappe-apps/smartdiag_workshop/    Extensión automotriz de Frappe
services/platform-api/             API pública/operacional y persistencia
services/ai-gateway/               Chat/LLM/RAG con guardrails
services/alerts-worker/            Reglas y alertas con lease
services/heartbeat-agent/          Heartbeats de réplicas
packages/smartdiag_domain/         Reglas puras de estados e idempotencia
infra/                             Proxy, Frappe, backup, observabilidad y HA
scripts/                           Instalación, prueba, backup y empaquetado
```

## Instalación guiada desde GitHub

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/LORDMANUEL/smart504.git
cd smart504
sudo bash install.sh
```

El instalador gráfico de terminal solicita dominio base, IP pública, correo TLS y
datos de la empresa. Después genera secretos, prepara Docker y levanta el stack
completo. No carga datos demo en modo producción. Antes de continuar deben existir
estos registros DNS tipo A, todos dirigidos a la IP de la VPS:

- `taller.DOMINIO`: landing y tienda.
- `clientes.DOMINIO`: portal del cliente.
- `app.DOMINIO`: operación del taller.
- `api.DOMINIO`: API.
- `erp.DOMINIO`: ERPNext administrativo.

Para automatización sin interfaz:

```bash
sudo SMARTDIAG_BASE_DOMAIN=nexusmedi.org \
  SMARTDIAG_SERVER_IP=203.0.113.10 \
  SMARTDIAG_ACME_EMAIL=admin@nexusmedi.org \
  SMARTDIAG_BUSINESS_NAME='Mi taller' \
  bash install.sh --non-interactive
```

Manual completo: `docs/deployment/INSTALACION_GRAFICA_LINUX.md`.
Actualización y reversión: `docs/deployment/VERSIONADO_ACTUALIZACION_ROLLBACK.md`.

## Chatbot

El componente `ChatWidget` se carga en la landing page y llama únicamente a `/api/v1/chat/*`. No contiene claves de proveedor. El flujo es:

```text
Navegador
→ sesión opaca y temporal de chat
→ platform-api
→ guardrails y contexto público autorizado
→ ai-gateway
→ demo / Ollama / proveedor compatible con OpenAI
```

El asistente no puede facturar, registrar pagos, mover inventario, cambiar precios, cerrar una OT ni liberar un vehículo. El modo `demo`/fallback funciona sin clave externa. Para usar un proveedor compatible, configure en `.env` `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL` y una clave cuando el proveedor la exija.

## Verificación

```bash
bash scripts/verify.sh
```

En una máquina con Docker y DNS configurado:

```bash
bash scripts/verify.sh --runtime --env-file .env
bash scripts/ha-smoke-test.sh .env
```

La redundancia A/B dentro de una sola VPS protege contra la caída de un contenedor o proceso, pero **no** contra la pérdida física de la VPS. La arquitectura para dos VPS más testigo se encuentra en `infra/ha/two-node/` y requiere su propia prueba de aceptación.

## Documentación principal

- `ARCHITECTURE.md`
- `docs/product/AUDITORIA_BRECHAS_Y_ROADMAP_2026-08-14.md`
- `SMARTDIAG504_IMPLEMENTATION_MASTER.md`
- `docs/deployment/VPS_RUNBOOK.md`
- `docs/CODEX_VPS_DEPLOY_PROMPT.md`
- `docs/CODEX_EXECUTION_GUIDE.md`
- `docs/testing/ACCEPTANCE_TESTS.md`
- `docs/testing/VERIFICATION_REPORT.md`
- `docs/architecture/DATA_OWNERSHIP.md`
- `infra/ha/two-node/HA_ACCEPTANCE.md`
