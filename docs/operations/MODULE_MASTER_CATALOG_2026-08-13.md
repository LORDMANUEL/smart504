# Catálogo maestro de módulos SmartDiag504

Estado fechado: 2026-08-13. Esta lista separa lo funcional, lo visual y lo que requiere integración externa. No sustituye la validación en el VPS.

## Funcional en la aplicación

| Módulo | Alcance implementado | Profundización pendiente |
|---|---|---|
| Landing y tienda | Landing promocional, catálogo, compatibilidad, carrito, solicitud de pedido, logo y acceso cliente | Pago en línea real y tarifas de entrega requieren proveedores |
| Cliente | Login, vehículos, calendario separado de la landing, citas, documentos PDF | Registro social/correo requiere proveedor de identidad configurado |
| Citas | Fuente `WEB` o `CLIENT_PORTAL`, disponibilidad, confirmación y eventos | Reglas de capacidad por técnico/bahía |
| OT / Kanban | OT única, diagnóstico, estados, repuestos, entrega de bodega e historial | Checklist técnico y firma del cliente |
| Cotizaciones | Creación manual o desde OT, mano de obra/repuestos, costos/precios, aprobación por línea | Firma remota y vigencia comercial parametrizable |
| Caja | Apertura, efectivo/tarjeta/transferencia, referencia POS, recibo, cierre, cuadre y reporte | Integración con adquirente POS y factura fiscal final |
| Pedidos web | Cola de Caja, contacto, WhatsApp registrado, reserva, preparación, envío, entrega y devolución | API oficial de WhatsApp y notificación automática |
| Bodega | Solicitud/entrega a OT, bodega principal, proceso, tránsito y devoluciones | Existencia contable se mantiene en ERPNext; falta adaptador de sincronización bidireccional aprobado |
| Fletes | Transportista, destinatario, estados, número y foto/enlace de guía obligatorios al enviar | Carga binaria de guía a S3 y webhooks de transportistas |
| Calidad | Devolución, garantía, reclamo y retrabajo; evidencia, resolución y auditoría | SLA, costos de no calidad y autorizaciones monetarias |
| Historial VIN | Eventos por VIN para diagnóstico, servicio, partes, calidad, devolución e inspección | Proyección automática desde ERPNext/Frappe |
| CRM de leads | Captura desde IA, nombre/teléfono/interés/vehículo y Kanban de seguimiento | Campañas, consentimientos y mensajería externa |
| Gerencia | Sucursales, documentos CAI, factura, cotización, proforma, cartas y correo; configuración visual | Validación legal/fiscal, almacenamiento y firma digital |
| IA pública | Respuestas rápidas estáticas, proveedor local/LLM opcional, RAG de catálogo público, captura de lead y guardas anti-extracción | Streaming real por SSE y base documental curada |
| Hub Social | Pantalla y política de seguridad | Conectar Meta requiere app, permisos, webhook y revisión de Meta |
| Observabilidad | Heartbeats, salud, mapa de eventos/flujo y heatmap | Alertas externas y pruebas periódicas de recuperación |

## Combinaciones de flujo formalizadas

1. Servicio completo: cita, recepción, diagnóstico, cotización, aprobación por línea, reserva/entrega de repuestos, trabajo, calidad, caja e historial VIN.
2. Solo diagnóstico: recepción, pruebas, informe, cobro e historial VIN.
3. Solo venta de repuesto: pedido, Caja contacta, confirma, reserva, prepara, adjunta guía, mueve a tránsito y entrega.
4. Venta nocturna: solicitud inmediata, aviso de confirmación al siguiente día hábil; no se promete existencia hasta validación.
5. Devolución: solicitud, evidencia, inspección, bodega de devoluciones, resolución e historial.
6. Garantía/reclamo: caso de calidad vinculado a OT/vehículo, inspección, retrabajo o rechazo y cierre.
7. Importación: solicitud, compra, recepción, bodega principal y posterior reserva/venta; el asiento contable sigue en ERPNext.

## Propiedad de datos

ERPNext/Frappe continúa como fuente autoritativa de clientes, vehículos, OT, cotizaciones fiscales, inventario, facturas y pagos. PostgreSQL conserva proyecciones de demo/control, trazas, leads, heartbeats, reservas logísticas y referencias externas. No se creó un segundo libro contable ni una OT paralela.

## Rutas nuevas

- `/tallerv1/procesos`: combinaciones, bodegas, fletes y calidad.
- `/tallerv1/leads`: Kanban CRM de interesados capturados por la IA.
- `/tallerv1/gerencia`: sucursales, CAI, plantillas y servicios corporativos.

