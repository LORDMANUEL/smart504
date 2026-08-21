# SmartDiag504 v0.3 — Diseño de producto y despliegue

## Objetivo

Convertir el skeleton v0.2 en una plataforma demostrable y desplegable para taller automotriz, tienda de repuestos y operación administrativa. El paquete debe instalar una instancia funcional de staging en una VPS, permitir administrar catálogo e imágenes, gobernar el ciclo de vida de la OT y ofrecer una arquitectura de alta disponibilidad de dos nodos con testigo.

## Decisiones cerradas

1. ERPNext/Frappe conserva la fuente oficial de inventario, compras, ventas, caja y contabilidad.
2. Beveren FSM se instala como base de servicio, pero el dominio automotriz vive en `smartdiag_workshop`.
3. El portal público y la PWA operacional consumen `platform-api`; nunca consultan MariaDB directamente.
4. PostgreSQL almacena catálogo público, medios, reservas, configuración, proyección de OT, eventos, heartbeats y auditoría. La contabilidad no se duplica allí.
5. Las fotografías predeterminadas son fotografías existentes de terceros con atribución. El administrador puede sustituirlas por archivos propios.
6. Las imágenes de producto admiten tres fuentes: carga administrada, URL externa y búsqueda opcional mediante Google Programmable Search. Google nunca se usa como almacenamiento definitivo: una imagen elegida debe importarse o conservar una URL con su atribución.
7. Kanban es la vista operativa predeterminada. La vista Bahías es una capacidad activable en configuración y usa las mismas OT.
8. Los estados de OT son inmutables como catálogo y las transiciones son validadas en servidor.
9. La instalación de una sola VPS se prueba como staging. La alta disponibilidad real requiere dos VPS y un testigo independiente para quorum; el ZIP incluye automatización y simulación local, pero no puede crear infraestructura física que el usuario no haya aprovisionado.

## Máquina de estados de OT

Estados canónicos:

- `CREATED`: OT creada.
- `QUOTED_BY_TECHNICIAN`: OT cotizada por técnico.
- `PENDING_CUSTOMER_APPROVAL`: OT pendiente de aprobación del cliente.
- `PENDING_PARTS`: OT pendiente de repuestos.
- `READY_TO_INVOICE`: OT finalizada para facturar.
- `INVOICED`: OT facturada.

Transiciones permitidas:

- `CREATED → QUOTED_BY_TECHNICIAN`
- `QUOTED_BY_TECHNICIAN → PENDING_CUSTOMER_APPROVAL`
- `PENDING_CUSTOMER_APPROVAL → QUOTED_BY_TECHNICIAN` para revisión.
- `PENDING_CUSTOMER_APPROVAL → PENDING_PARTS` cuando se aprueba y faltan repuestos.
- `PENDING_CUSTOMER_APPROVAL → READY_TO_INVOICE` cuando se aprueba y no requiere ejecución adicional.
- `PENDING_PARTS → READY_TO_INVOICE` cuando todos los repuestos y operaciones están terminados.
- `READY_TO_INVOICE → INVOICED` únicamente con referencia válida de factura ERPNext.

Cada transición registra actor, fecha, motivo, versión y clave de idempotencia.

## Catálogo e imágenes

Entidades:

- `catalog_products`
- `catalog_product_images`
- `catalog_categories`
- `media_assets`
- `image_search_audits`

El producto contiene SKU, nombre, descripción, precio de exhibición, moneda, disponibilidad, categoría, marca, estado publicado y referencia ERPNext. Una imagen tiene origen, URL, objeto S3, texto alternativo, atribución, orden, estado y checksum.

La API administrativa permite crear, editar, publicar, archivar, cargar imágenes, definir principal, reordenar y eliminar. Las cargas se validan por MIME, tamaño y checksum. Los URLs se validan contra HTTP/HTTPS y se sirven mediante proxy opcional para evitar contenido mixto.

## Experiencia visual

### Landing

- Encabezado limpio con Servicios, Repuestos, Reservar y Mi vehículo.
- Hero con fotografía real de diagnóstico automotriz, propuesta clara y dos acciones.
- Servicios especializados con fotografías reales.
- Proceso de atención en seis pasos.
- Evidencia del producto: seguimiento de OT, aprobación y entrega.
- Catálogo destacado con fotos reales o cargadas.
- Reserva, ubicación, contacto y WhatsApp.
- Pie con atribuciones fotográficas.

### Tienda

- Buscador por número de parte, nombre, marca, modelo y año.
- Filtros, disponibilidad, compatibilidad y ordenamiento.
- Ficha de producto con galería, atribución, stock y solicitud de validación por VIN.
- Carrito persistente y solicitud/pedido.
- Administración de imágenes y productos en PWA operacional.

### Operación

- Kanban con seis columnas canónicas.
- Vista Bahías opcional, activada por `workshop_bays_enabled`.
- Detalle de OT con vehículo, técnico, cotización, repuestos, evidencia, historial y facturación.
- Panel de configuración para alternar vistas y políticas.

## Alta disponibilidad

### Perfil de una VPS

Dos réplicas de web/API detrás de HAProxy, healthchecks, reinicio automático, leader lease para workers y respaldo local/remoto. Demuestra failover de contenedores, pero no protege ante pérdida total del host.

### Perfil de dos VPS

- Keepalived VRRP o DNS failover para la IP/entrada.
- HAProxy en ambos nodos.
- Réplicas de aplicación en ambos.
- MariaDB Galera en nodo A y B más `garbd` en un testigo independiente.
- PostgreSQL Patroni en A y B más DCS con quorum independiente; alternativamente PostgreSQL administrado.
- Almacenamiento de objetos replicado fuera de ambos nodos o bucket S3 administrado.
- Restic para respaldos cifrados y prueba de restauración.
- Heartbeat firmado, lease de líder y fencing operativo documentado.

Un clúster de dos nodos sin testigo no se presenta como alta disponibilidad segura.

## Seguridad

- Secretos generados fuera de Git.
- JWT/sesión para administración; rutas públicas separadas.
- RBAC por rol.
- Límites de carga, MIME allowlist, checksum y nombres aleatorios.
- CORS explícito, rate limiting, HMAC de eventos e idempotencia.
- Auditoría de cambios y transiciones.
- Bases de datos y caches no publican puertos al exterior.

## Pruebas

- Unitarias: máquina de estados, imágenes, catálogo, settings y leader lease.
- Integración: migraciones y CRUD PostgreSQL.
- Contratos: OpenAPI y eventos.
- Frontend: pruebas de componentes y flujos.
- E2E: landing, catálogo, administración, Kanban, toggle de Bahías.
- Infraestructura: `docker compose config`, healthchecks, caída de una réplica y continuidad del endpoint.
- Respaldo: crear, verificar checksum y ejecutar restauración de prueba.
