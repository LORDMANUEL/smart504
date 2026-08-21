# SmartDiag504 - OT, cotizacion, caja, bodega y CRM

Fecha de corte: 2026-08-13.

## Alcance entregado

### Orden de trabajo y diagnostico

- La OT permite cargar fotografias JPG, PNG o WebP desde camara o archivo, con descripcion, autor y fecha.
- Las evidencias quedan ligadas a la OT y a su bitacora auditable.
- El documento `diagnosis` incluye diagnostico, datos de la OT y fotografias registradas; se genera desde HTML y se exporta a PDF.
- Limite por imagen: 8 MB. No se aceptan archivos que no puedan ser validados como imagen.

### Cotizacion previa a la OT

- La pantalla de cotizaciones busca por VIN, placa, propietario, telefono o correo.
- Se seleccionan mano de obra, repuestos u otros conceptos y se calcula subtotal, descuento, impuesto y total.
- La cotizacion se conserva en base de datos, se imprime como HTML o PDF y admite aprobacion por concepto.
- Solo una cotizacion aprobada puede convertirse a OT. La conversion conserva cliente, vehiculo y referencia de origen.

### Caja

- La entrada operativa es un Kanban de OTs listas para cobro; la tarjeta abre el cobro de una OT concreta.
- Apertura, cobro y cierre solicitan un codigo privado de cajera cuando `CASHIER_ACCESS_CODE` esta configurado.
- Se registran fondo inicial, efectivo, tarjeta, transferencia o enlace, arqueo esperado/contado y diferencia.
- Factura, garantia y pase de salida se generan como PDF imprimible.
- La integracion fisica con gaveta o impresora requiere modelo, controlador, conexion y ancho de papel. El sistema entrega PDF/HTML estandar; no se declara validacion fisica sin ese equipo.

### Bodega

- Kanban por solicitud de OT: solicitado, preparando, listo, entregado, devolucion solicitada, devuelto y recibido.
- Cada cambio queda auditado con actor, fecha y ubicacion.
- PDF disponibles: ticket de picking, entrega, devolucion y entrada/recepcion de mercancia.

### Procesos, calidad y CRM

- Calidad opera con casos reales: abierto, analisis, accion, verificacion, cerrado y rechazado.
- El mapa de flujo consume eventos persistidos y permite filtrar por modulo e inspeccionar cada evento.
- CRM permite crear leads, moverlos por prospeccion, registrar contactos, abrir WhatsApp y guardar encuestas.
- Actividades y encuestas se almacenan como eventos de flujo para trazabilidad y analisis.

### Notificaciones

- Confirmaciones y cambios de citas y pedidos crean notificaciones internas del portal con estado de entrega.
- El cliente las ve en Alertas; las cotizaciones pendientes aparecen como aprobaciones.
- Correo, SMS y WhatsApp externos necesitan proveedor y credenciales empresariales. No se simula envio externo sin configuracion.

### Fotografias de catalogo

- El sembrado asigna una imagen generica de referencia a productos sin fotografia y registra procedencia `AI_GENERATED`.
- La imagen generica no sustituye la foto exacta del numero de parte; una foto real debe pasar a principal.

## Controles de seguridad y operacion

- El codigo de cajera se compara de forma constante y no se devuelve por API.
- La evidencia se valida por tipo y contenido antes de guardarse.
- Las transiciones de cotizacion, bodega y calidad se validan en servidor.
- El despliegue sigue inventario, respaldo, migracion, recreacion selectiva y prueba del runtime. No reinicia el proxy compartido de Coolify.

## Variable nueva

| Variable | Uso |
|---|---|
| `CASHIER_ACCESS_CODE` | Codigo privado para abrir/cerrar caja y registrar pagos. |

## Rutas API principales

| Flujo | Ruta |
|---|---|
| Fotos OT | `GET/POST /api/v1/operations/work-orders/{id}/evidence` |
| Diagnostico PDF | `GET /api/v1/operations/finance/work-orders/{id}/documents/diagnosis.pdf` |
| Buscar VIN/dueno | `GET /api/v1/operations/finance/quote-context?query=` |
| Convertir cotizacion | `POST /api/v1/operations/finance/quotes/{id}/convert-to-work-order` |
| Documentos bodega | `GET /api/v1/operations/finance/work-orders/{id}/warehouse-documents/{kind}.pdf` |
| Leads | `POST /api/v1/operations/control/leads` |
| Actividad/encuesta | `POST /api/v1/operations/control/leads/{id}/activities` y `/surveys` |

