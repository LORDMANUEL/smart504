# SmartDiag504 Workshop OS — Implementación maestra v0.4.0

**Fecha de corte:** 12 de agosto de 2026  
**Empresa:** SmartDiag504  
**Entrega:** monorepo completo para Codex, CI y despliegue Docker en VPS.

## 1. Alcance de esta versión

SmartDiag504 v0.4.0 reúne en un solo producto:

- landing page profesional con el logo entregado por SmartDiag504 y fotografías reales existentes;
- catálogo de repuestos, carrito y solicitud de pedido web;
- carga administrativa de fotografías por archivo, URL o búsqueda opcional con Google Programmable Search;
- chatbot incrustado en la misma página pública;
- reservas de diagnóstico y servicio;
- PWA operacional para asesor, técnico, bodega, caja, supervisor y administración;
- Kanban de órdenes de trabajo con seis estados oficiales;
- vista de bahías activable o desactivable por configuración;
- ERPNext/Frappe para inventario, compras, POS, caja, facturación, pagos y contabilidad;
- Beveren FSM como base del flujo de servicio;
- aplicación Frappe propia `smartdiag_workshop` para VIN, recepción, diagnóstico, técnicos, repuestos, calidad, garantía e historial;
- FastAPI, PostgreSQL, Valkey, ChromaDB, Garage S3 y servicios de IA/alertas;
- réplicas A/B, heartbeat, lease de workers, HAProxy, Caddy, backup y restauración;
- scripts de instalación no interactiva para Codex y una VPS Debian/Ubuntu.

## 2. Decisión arquitectónica

```text
Internet
   │
Caddy: TLS, dominios y cabeceras
   │
HAProxy
   ├── public-web A/B      landing + tienda + reserva + chatbot
   ├── ops-web A/B         Kanban + bahías + catálogo + pedidos
   ├── platform-api A/B    BFF, catálogo, chat, OT, heartbeat
   └── ai-gateway A/B      fallback seguro / Ollama / LLM externo

ERPNext/Frappe v16
   ├── Beveren FSM fijado y parcheado
   └── smartdiag_workshop

Datos
   ├── MariaDB      ERPNext y Beveren
   ├── PostgreSQL   proyección operacional, chat, eventos y auditoría
   ├── Valkey       caché, rate limit, locks, lease y coordinación
   ├── ChromaDB     índice de conocimiento autorizado
   └── Garage S3    evidencia y objetos privados
```

### Reglas de propiedad

1. **ERPNext es la única fuente financiera y de inventario.**
2. La OT central es Beveren **`Service Order`**; no se crea otra OT paralela.
3. PostgreSQL no replica el libro mayor, Stock Ledger, factura ni Payment Entry.
4. El navegador nunca se conecta directamente a MariaDB o PostgreSQL.
5. La IA no puede facturar, cobrar, mover stock, cambiar precios ni liberar vehículos.

## 3. Flujo oficial de la OT

La proyección SmartDiag504 conserva exactamente estos estados:

```text
CREATED
→ QUOTED_BY_TECHNICIAN
→ PENDING_CUSTOMER_APPROVAL
→ PENDING_PARTS
→ READY_TO_INVOICE
→ INVOICED
```

| Estado | Significado operativo |
|---|---|
| `CREATED` | Vehículo recibido y OT abierta. |
| `QUOTED_BY_TECHNICIAN` | Técnico documentó diagnóstico, mano de obra y repuestos. |
| `PENDING_CUSTOMER_APPROVAL` | Cotización enviada; no se ejecuta trabajo no aprobado. |
| `PENDING_PARTS` | Trabajo aprobado, pero falta reservar, entregar o comprar repuestos. |
| `READY_TO_INVOICE` | Trabajo y control de calidad terminados; listo para facturar. |
| `INVOICED` | Factura ERPNext verificada y vinculada. |

La máquina de estados vive en `packages/smartdiag_domain/smartdiag_domain/work_orders.py`. Cada transición conserva usuario, fecha, motivo y evento. No permite saltos arbitrarios.

## 4. Taller y dominio automotriz

`frappe-apps/smartdiag_workshop` agrega 17 DocTypes iniciales:

1. SmartDiag Vehicle.
2. Vehicle Check In.
3. Vehicle Check In Photo.
4. Diagnostic Session.
5. Diagnostic Finding.
6. Labor Operation.
7. Technician Assignment.
8. Workshop Bay.
9. Bay Assignment.
10. Part Request.
11. Part Request Item.
12. Workshop Quality Check.
13. Quality Check Item.
14. Workshop Warranty Claim.
15. Maintenance Recommendation.
16. SmartDiag Event Outbox.
17. SmartDiag Settings.

El flujo objetivo es:

```text
reserva/llegada
→ cliente y vehículo
→ recepción con evidencia
→ Service Order
→ diagnóstico y DTC
→ cotización versionada
→ aprobación
→ repuestos y técnicos
→ ejecución
→ control de calidad
→ factura/pago ERPNext
→ entrega
→ historial por VIN y garantía
```

## 5. Kanban y bahías

La vista predeterminada es **Kanban**, con las seis columnas oficiales. En `SmartDiag Settings` o desde `/api/v1/operations/settings/workshop` se puede habilitar el módulo de bahías.

- `default_view=KANBAN` funciona aun sin definir bahías.
- `default_view=BAYS` solamente se acepta cuando `bays_enabled=true`.
- Las bahías no sustituyen el estado de OT; son una ubicación operacional adicional.
- La PWA puede volver a Kanban en cualquier momento sin perder datos.

## 6. Página pública, repuestos y fotografías

`apps/public-web` contiene:

- inicio, servicios, proceso y propuesta comercial;
- fotografías reales descargadas durante la instalación y servidas localmente;
- búsqueda de repuestos por código, nombre o marca;
- disponibilidad y nota de compatibilidad;
- carrito y solicitud de pedido;
- reserva de diagnóstico;
- chatbot flotante;
- diseño responsive y navegación accesible.

Las fotografías públicas se documentan en `apps/public-web/public/images/stock/ATTRIBUTION.md`. Pueden sustituirse por fotografías propias manteniendo los mismos nombres.

### Imágenes de repuestos

El administrador dispone de tres rutas:

1. **Carga directa:** JPEG, PNG o WEBP con tamaño máximo configurable.
2. **Importación por URL:** el servidor valida y copia la imagen al almacenamiento administrado; no se depende indefinidamente de hotlinks.
3. **Google Programmable Search:** devuelve candidatos cuando `GOOGLE_CSE_API_KEY` y `GOOGLE_CSE_ID` están configurados. El operador elige la imagen y conserva procedencia/atribución.

La carga directa funciona aunque Google no esté configurado. El navegador no recibe la clave de Google.

### Pedido web

El checkout crea una **solicitud de pedido** idempotente en PostgreSQL. No descuenta stock ni genera factura por sí mismo. El panel administrativo permite revisar y vincular la futura Sales Order de ERPNext. La activación de pago en línea exige el Gate de pasarela, impuestos, reserva de stock y conciliación.

## 7. Chatbot incrustado

`ChatWidget` se monta dentro de la landing page y usa este flujo:

```text
navegador
→ POST /api/v1/chat/sessions
→ token opaco de sesión
→ platform-api
→ contexto público permitido
→ ai-gateway
→ fallback determinista / Ollama / proveedor compatible
```

Capacidades públicas:

- explicar servicios;
- orientar una reserva;
- buscar coincidencias públicas de repuestos;
- explicar el proceso de una OT;
- derivar a WhatsApp o al formulario de reserva;
- advertir ante síntomas de seguridad.

Restricciones:

- no revela una OT sin autenticación;
- no confirma diagnóstico ni compatibilidad por VIN sin validación;
- no crea o altera factura, pago, inventario, precio, descuento o entrega;
- aplica TTL, rate limit, idempotencia por mensaje y auditoría;
- no expone claves de LLM en el frontend;
- funciona en modo seguro sin clave externa con `LLM_PROVIDER=demo`.

## 8. ERPNext y Beveren FSM

La imagen Frappe incluye:

```text
Frappe:     v16.31.0
ERPNext:    v16.32.0
Beveren:    ab6d56d1069882326475f256d09cc63236eddec1
SmartDiag:  0.4.0
```

El parche `infra/frappe/patches/beveren/0001-v16-compat.patch`:

- declara ERPNext como dependencia;
- fija compatibilidad v16;
- corrige consultas de dirección/contacto;
- corrige el registro en Apps;
- hace que Service Order y Service Quotation hereden el controlador de venta requerido para `process_item_selection`.

No se instala la rama `develop` directamente en producción. La certificación real de cotización → OT → cita → factura debe ejecutarse en staging con Docker.

## 9. Servicios y persistencia

### Platform API

Incluye rutas para:

- health/readiness;
- catálogo y categorías;
- reservas;
- chatbot;
- pedidos web;
- administración de catálogo e imágenes;
- clientes, vehículos y tablero de OT;
- configuración Kanban/bahías;
- heartbeat y lease.

Contrato: `contracts/openapi-public.yaml`.

### AI Gateway

- fallback determinista;
- proveedor compatible con OpenAI/Ollama;
- RAG opcional en ChromaDB;
- allowlist de herramientas de lectura;
- guardrails y token interno.

### Alerts Worker

Dos réplicas compiten por un lease. Solo el poseedor vigente ejecuta reglas. El fencing token reduce riesgo de doble ejecución. Reglas iniciales: cotización demorada, fecha prometida, repuesto pendiente, técnico libre, QC fallido y diferencia de caja.

### Heartbeat

Cada réplica informa `node_id`, rol y URL de readiness. El dashboard muestra nodos saludables/degradados y el lease activo.

## 10. Docker y alta disponibilidad

`compose.yaml` contiene 38 servicios, incluidos perfiles opcionales. Solamente Caddy publica 80/443; Grafana y Prometheus se ligan a loopback cuando se activa observabilidad.

### Redundancia dentro de una VPS

- public-web A/B;
- ops-web A/B;
- platform-api A/B;
- ai-gateway A/B;
- heartbeat A/B;
- alerts-worker A/B activo/standby;
- HAProxy retira una réplica que falla healthcheck.

Esto tolera la caída de un contenedor o proceso, **no** la pérdida del servidor, disco, red o proveedor de la VPS.

### Redundancia física

`infra/ha/two-node/` documenta una topología de dos VPS más testigo/quorum, DNS o balanceador externo, replicación de datos y backup fuera del sitio. No se declara HA física hasta aprobar `infra/ha/two-node/HA_ACCEPTANCE.md`.

## 11. Backup y restauración

El backup incluye:

- dump PostgreSQL;
- dump MariaDB;
- sitios y archivos Frappe;
- media de plataforma;
- configuración, metadata y datos de Garage;
- manifiesto SHA-256;
- copia opcional con Restic fuera de la VPS.

Restauración:

```bash
bash scripts/restore.sh \
  --archive /ruta/smartdiag504-FECHA.tar.gz \
  --confirm RESTORE-SMARTDIAG504
```

Siempre se prueba primero en una instalación limpia de staging. Un Garage de un solo nodo no es un reemplazo de backup externo.

## 12. Instalación por Codex en VPS

```bash
unzip smartdiag504_platform_complete_v0.4.0.zip
cd smartdiag504-platform-v0.4.0
sudo bash scripts/bootstrap-host.sh --open-firewall
cp .env.example .env
bash scripts/generate-secrets.sh .env
nano .env
sudo bash scripts/codex-vps-deploy.sh \
  --env-file .env \
  --observability \
  --test-failover
```

Con IA local:

```bash
sudo bash scripts/codex-vps-deploy.sh \
  --env-file .env \
  --local-ai \
  --observability \
  --test-failover
```

Antes de publicar se deben sustituir teléfono, WhatsApp, correo, dominios, credenciales de integración, política fiscal y backup externo.

## 13. Validación y CI

Comando local:

```bash
bash scripts/verify.sh
```

En VPS/runner con Docker:

```bash
bash scripts/verify.sh --runtime --env-file .env
bash scripts/ha-smoke-test.sh .env
bash scripts/backup-now.sh .env
```

GitHub Actions:

- `.github/workflows/ci.yml`: Python, TypeScript, Vitest, Playwright y contratos;
- `.github/workflows/build-images.yml`: construcción/push de imágenes con SBOM y provenance.

## 14. Estado real de la entrega

### Incluido y verificado estáticamente

- código fuente del monorepo;
- API, migraciones y pruebas;
- landing, tienda, reserva, chatbot y PWA;
- logo proporcionado por SmartDiag504;
- catálogo y administración de imágenes;
- seis estados oficiales de OT;
- Kanban y bahías configurables;
- Docker Compose, Caddy y HAProxy;
- Frappe/ERPNext/Beveren/SmartDiag image definition;
- heartbeat, lease, backups y restore;
- contratos, documentación y scripts para Codex.

### Gates que requieren una VPS/runner con Docker

- `docker compose config` con el `.env` real;
- construcción completa de todas las imágenes;
- creación de ERPNext desde cero;
- certificación Beveren v16 de extremo a extremo;
- integración real del catálogo y facturación ERPNext;
- restore drill fuera de la VPS;
- pasarela de pago;
- localización fiscal hondureña;
- prueba de carga, análisis de vulnerabilidades y pentest;
- HA física de dos VPS cuando sea requerida.

## 15. Criterio de salida a producción

La versión productiva debe demostrar:

```text
OT técnica
= aprobación del cliente
= repuestos reservados/consumidos/devueltos
= documentos de stock ERPNext
= líneas facturadas
= pagos y caja
= historial por VIN
= evidencia, eventos y auditoría
```

Hasta que los Gates se ejecuten con evidencia en staging, este repositorio es una base completa de ingeniería y despliegue, no una certificación fiscal o de continuidad física.
