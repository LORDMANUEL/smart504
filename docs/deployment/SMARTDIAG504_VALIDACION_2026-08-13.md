# SmartDiag504: módulos, decisiones y validación de staging

Fecha de corte: 2026-08-13. Entorno: `taller.nexusmedi.org`, administrado como recurso de Coolify y aislado de los demás proyectos del VPS.

## Módulos y rutas

| Área | Ruta o acceso | Persistencia / estado esperado |
|---|---|---|
| Landing promocional | `/lading` | Reserva guardada en PostgreSQL |
| Selector digital | `/lading/acceso` | Enlaces a tienda, cliente y personal |
| Tienda de repuestos | `/lading/repuestos` | Pedido y líneas guardados en PostgreSQL |
| Acceso de cliente | `/lading/loginclie` | Sesión firmada y limitada en tiempo |
| Portal de cliente | `/lading/cliente` | Vehículos demo, compatibilidad, alertas, cotización y factura PDF autenticada |
| Personal / técnicos | `/tallerv1/login` | Autenticación de staging y acceso a operación |
| Citas de recepción | menú `Citas` | Bandeja de citas web con contacto, confirmación y cancelación persistentes |
| Kanban / time control | `/tallerv1/kanban` | Tarjeta de OT abre resumen, repuestos, historial y búsqueda guiada de manuales |
| Bahías | menú `Bahías` | Vista operacional derivada de la misma OT |
| Pedidos web | menú `Pedidos web` | Estado del pedido persistente |
| Catálogo | menú `Catálogo` | Productos, imágenes y plantilla Excel demo |
| Caja | `/tallerv1/caja` | Evento de pago de demostración guardado en `flow_events` |
| Bodega | `/tallerv1/bodega` | Picking generado por la OT; ubicación, responsable y entrega regresan a la OT |
| Publicidad | `/tallerv1/publicida` | Evento de publicación guardado; contenido TV visible |
| Pantalla TV | `/tallerv1/publicida/tv` | Vista pública de campaña |
| Administración | `/tallerv1/3gj` | Resumen y directorio de módulos |
| Mapa de flujos | `/tallerv1/flujos` | Agregación real de eventos por módulo/acción |
| Hub Social | `/tallerv1/social` | Módulo visible; conectores externos pendientes de credenciales oficiales |
| Configuración | menú `Configuración` | Preferencia Kanban/bahías persistente |
| Sistema | menú `Sistema` | Estado de nodos y servicios |

## Catálogo de demostración

La descarga desde Configuración usa `template?demo=true`. Incluye cinco códigos de mano de obra, cada uno compatible con los tres vehículos de prueba, y nueve repuestos: tres para Ford Escape 2020, tres para Ford F-150 2020 y tres para Honda Civic 2008. La API conserva una plantilla vacía sin parámetros para cargas reales.

La vista previa valida encabezados, códigos, descripción, marca/modelo/años/motor, horas, costo, venta y que venta no sea menor al costo. La aplicación a ERPNext continúa siendo una acción separada y explícita.

Además se precargó una biblioteca interna de más de 30 combinaciones vehículo/año y más de 12 marcas frecuentes. Cada vehículo tiene tres fichas de repuesto preparadas con existencia cero y estado inactivo. No se publican como inventario real: primero se completa número de parte, costo, precio, existencia, fotografía y compatibilidad por VIN.

## Persistencia y mapa de flujo

La migración `0005_flow_events` crea una bitácora append-only con módulo, acción, referencia del artículo u OT, actor, resultado, metadatos y fecha. La migración `0006_flow_history_backfill` incorpora las citas y el historial de OT existentes al mapa. Citas, OT, solicitudes de repuesto, bodega, caja y publicidad registran eventos antes de mostrar éxito. El lienzo agrupa esos datos; no usa contadores inventados en el navegador.

## IA local y RAG

El despliegue de staging define contenedores exclusivos `ollama`, `chromadb`, `ai-gateway` y `rag-seed`, con volúmenes exclusivos de SmartDiag504. El modelo escogido es `gemma3:270m` por la ausencia de GPU y el límite de memoria del VPS. El RAG se inicia con documentos de flujo de OT, seguridad, compatibilidad, reservas y privacidad. La IA es de lectura: no cobra, no factura, no modifica inventario y no libera vehículos.

## Excel, PDF y seguridad de rutas

- Excel: `openpyxl` genera y valida XLSX.
- PDF: `reportlab` genera una factura PDF real, únicamente tras validar la sesión firmada del cliente.
- HAProxy devuelve 404 a solicitudes de `.php`, `.phtml`, `.phar`, source maps, `.env` y `.git`.
- Los archivos CSS compilados deben seguir siendo públicos para que el navegador pueda renderizar la aplicación. Sus nombres contienen hash y no exponen código de servidor; ocultar la extensión CSS no agrega seguridad.

## Identidad externa y Hub Social

No se simula OAuth ni Meta. Para el acceso de clientes se eligió como siguiente integración una pantalla administrada de Clerk con código por correo; Google no será obligatorio. Las redes sociales y Meta necesitan sus credenciales y permisos oficiales. Hasta recibirlos, el Hub muestra `Configuración pendiente` y bloquea publicaciones automáticas. La decisión y sus requisitos están en `docs/architecture/ADR-0011-acceso-cliente-administrado.md`; no se instaló el SDK sin claves porque bloquearía el acceso demo actual.

## Decisiones de interfaz

Se agregaron cristal esmerilado moderado, separación visual, microtransiciones y revelado con zoom corto. Todos los efectos respetan `prefers-reduced-motion`. No se añadieron comentarios redundantes a cada línea: los comentarios se reservan para decisiones, límites de seguridad y comportamiento no evidente; esta documentación explica el flujo y la intención de los componentes.

## Evidencia automatizada antes del despliegue

- 21 pruebas focalizadas de IA/RAG, Excel y persistencia: aprobadas.
- 8 pruebas focalizadas de PDF, autenticación de cliente, Excel y eventos: aprobadas.
- Builds TypeScript/Vite de `public-web` y `ops-web`: aprobados.
- Suite Python completa anterior: 129 pruebas aprobadas (una advertencia no bloqueante).
- Suite focalizada de Platform API tras cerrar citas/OT/bodega: 45 pruebas aprobadas.
- Suite frontend pública: 4 de 4 pruebas aprobadas.
- Suite frontend operativa: 9 de 9 pruebas aprobadas.
- Validador del repositorio: 908 archivos, 21 YAML, 30 JSON, 38 servicios y 95 variables revisadas; aprobado.
- `docker compose config --quiet` del Compose de Coolify: debe ejecutarse antes de cada despliegue con las variables del recurso.

La evidencia de navegador y los estados de contenedor se actualizan al final de cada despliegue; HTTP 200 por sí solo no certifica un flujo.

## Cierre del despliegue

Las 13 rutas públicas solicitadas respondieron HTTP 200 el 2026-08-13. Los nueve servicios persistentes del recurso (`gateway`, `public-web`, `ops-web`, `platform-api`, `postgres`, `redis`, `ollama`, `chromadb` y `ai-gateway`) quedaron en estado `healthy`. Además de comprobar la representación visual, se ejercitaron en navegador las acciones de caja, bodega y publicidad y se confirmó su aparición posterior en el mapa de flujos.

Durante el cierre se corrigió la inicialización del chat público: un cambio de estado de carga cancelaba prematuramente la creación de la sesión. La corrección se cubrió con una prueba de apertura, creación de sesión y respuesta del asistente, y se reconstruyó exclusivamente el contenedor `public-web`.

## Validación del flujo ampliado

Despliegue `e94a7df`, validado el 2026-08-13:

- Reserva pública creada con referencia `B4B2E912`, visible y confirmada desde `Citas`.
- `OT-DEMO-001` abierta desde Kanban con Resumen, Repuestos, Historial y Manuales.
- `ESC-FIL-2020` solicitado desde la OT, recibido en la cola real de Bodega y entregado desde `A-01-02`.
- El mapa mostró citas, confirmación, historial de OT, solicitud, entrega y cobro desde PostgreSQL.
- Portal cliente autenticado; Ford Escape 2020 mostró exactamente sus tres repuestos demo.
- Base activa después del seed: 124 productos, 5 citas y 34 eventos de flujo.
- Los nueve servicios persistentes quedaron saludables. El despliegue recreó únicamente API y frontends de SmartDiag504.
- Backup previo restaurado de forma aislada y verificado en `/opt/smartdiag504-demo/backups/20260813T173811Z-pre-flow-deploy`.

## Calendario autenticado y circuito financiero

Despliegue `9d9f85f`, validado el 2026-08-13:

- Migración activa: `0007_client_calendar_cashier`.
- Los nueve servicios persistentes del recurso quedaron saludables; solo se recrearon `platform-api`, `public-web` y `ops-web`.
- Las 15 rutas de landing, portal y operaciones comprobadas respondieron HTTP 200.
- Login de cliente real: HTTP 200.
- Cita autenticada creada, recuperada en el portal y visible en recepción con fuente `CLIENT_PORTAL` y estado `CONFIRMED`.
- Cotización demo `COT-DEMO-0183` visible con estado `APPROVED` y total de L 4,585.00.
- Turno abierto con L 1,000.00, pago POS de prueba persistido por L 100.00 con recibo `REC-260813-A80C0`, cierre efectuado y diferencia L 0.00.
- Navegador: Kanban, Citas, Cotizaciones, Caja, Bodega, Administración, Publicidad, Flujos y Hub Social mostraron contenido funcional; no se detectaron errores de consola en Caja ni en el portal del cliente.
- Pruebas locales: API 47/47, operaciones 12/12 y portal público 5/5; ambas compilaciones Vite de producción aprobaron. Caja conserva visible el reporte del último turno cerrado.
- Backup previo con checksum y restauración aislada de 85 tablas: `/opt/smartdiag504-demo/backups/20260813T181955Z-pre-finance-deploy`.

El registro POS demuestra el flujo interno, la referencia, el recibo y el arqueo. La comunicación directa con un datáfono/adquirente y la factura fiscal requieren contrato, credenciales y datos fiscales del taller; no se simularon.

## Control operativo, logística, calidad y CRM

Despliegues `8d30fb7` y corrección de seguridad `5558322`, validados el 2026-08-13:

- Migración activa `0008_operations_control_hub`.
- Nuevas vistas autenticadas y con contenido: `/tallerv1/procesos`, `/tallerv1/leads` y `/tallerv1/gerencia`; sin errores de consola durante la verificación visual.
- Las 16 rutas públicas/operativas solicitadas devolvieron HTTP 200 y sus bundles JavaScript/CSS devolvieron HTTP 200 con contenido.
- Estructura inicial persistida: una sucursal y cuatro bodegas (`STOCK`, `PROCESS`, `TRANSIT`, `RETURNS`).
- Lead de validación `LEAD-260813-ED5A30` creado desde la API pública y visible en CRM.
- Caso de calidad de validación `CAL-260813-52A706` creado y cerrado con resolución auditable.
- La extracción de prompt/secretos se bloqueó también en el fallback rápido: respuesta externa en 448 ms, modo `blocked`, auditoría y escalamiento a asesor.
- API Python: 136 pruebas aprobadas; operaciones web: 12; portal público: 5; ambas compilaciones Vite aprobaron.
- Backup verificado y restaurado aisladamente: `/opt/smartdiag504-demo/backups/20260813T190000Z-pre-operations-deploy` (21 tablas del esquema de aplicación). La base temporal fue eliminada.
- Nueve servicios persistentes saludables. Se recrearon solo API, IA, frontends y gateway propio de SmartDiag504; no se reinició el proxy compartido de Coolify.

La mensajería Meta/WhatsApp, adquirente POS, correo corporativo, identidad social y HA de dos VPS siguen requiriendo proveedores, credenciales y pruebas externas. Se documentan como integraciones/features, no como activas.

## Portal cliente, documentos, caja, pedidos y campañas

Entrega `client-commerce-20260813T2255Z`, validada el 2026-08-13:

- Portal cliente dividido en rutas internas independientes para vehículo, citas, repuestos, alertas, cotizaciones, facturas y configuración.
- Tres imágenes transparentes servidas desde `/vehicles/`: Ford Escape 2020, Ford F-150 2020 y Honda Civic 2008.
- Dashboard autenticado con 3 vehículos, 2 alertas, 1 cotización y 1 factura; documentos de la cotización HTTP 200 en HTML y PDF.
- Caja con Kanban, POS interno, factura, garantía, pase de salida, arqueo y cierre; Pedidos web con ocho columnas y detalle de tarjeta.
- Publicidad con creador, PNG/video validado, publicación, enlace único y clic persistido. Se corrigió el gateway para enviar `/c/` a la API: HTTP 302 y contador de clic 1.
- El detalle de `OT-DEMO-001` abrió sus cuatro pestañas. El catálogo quedó filtrado: Ford Escape incluyó `ESC-FIL-2020` y excluyó los SKU específicos de F-150 y Civic.
- API: 55 pruebas; contratos generales: 52; operaciones: 12; portal: 5. Builds Vite aprobados.
- Backup validado y restaurado aisladamente: `/opt/smartdiag504-demo/backups/20260813T223600Z-pre-client-commerce-deploy` (30 tablas). La base temporal se eliminó.
- Se recrearon únicamente `platform-api`, `public-web`, `ops-web` y el gateway propio de SmartDiag504. Coolify, Traefik y los servicios ajenos no se reiniciaron.
