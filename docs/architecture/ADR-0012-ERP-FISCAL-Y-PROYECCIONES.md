# ADR-0012: ERPNext, fiscalidad y proyecciones operativas

- Estado: aceptado para staging; pendiente certificación del contador para producción.
- Fecha: 2026-08-17.

## Decisión

ERPNext/Beveren es la fuente autoritativa de OTs, cotizaciones, movimientos de inventario, facturas, pagos, notas de crédito y contabilidad. PostgreSQL conserva proyecciones para UX, colas, auditoría, CRM, campañas y analítica; no constituye un segundo libro contable.

Toda mutación financiera u operativa autoritativa usa una cola durable e idempotente. La interfaz muestra `PENDING`, `SYNCED`, `FAILED` o `BLOCKED` y sólo presenta una referencia ERP cuando ERPNext la devolvió. En particular:

- OT → `Service Order`.
- Cotización → `Service Quotation`.
- Traslado recibido → `Stock Entry` sometido.
- Venta de mostrador → `Sales Invoice` + `Payment Entry`.
- Devolución → nota de crédito + reembolso.

## Numeración fiscal

Cada sucursal y tipo documental tiene una sola configuración activa:

1. `ERPNEXT`: ERPNext genera y conserva el correlativo. SmartDiag sólo presenta e imprime el documento devuelto por ERP.
2. `PREPRINTED`: el documento físico conserva el correlativo autorizado. SmartDiag registra CAI, prefijo, rango, vigencia y número usado; no genera un segundo correlativo fiscal.

La configuración nace en borrador, requiere confirmación explícita del contador y al activarse expira la anterior. Plantillas HTML/CSS versionadas controlan presentación, no numeración ni asientos.

## Consecuencias

- Una caída de ERP no produce falsos documentos “terminados”; quedan en cola con error visible y reintento.
- No se permite declarar producción hasta conciliar una operación completa con el libro mayor de ERPNext.
- Las reglas de SAR/CAI, impuestos, rangos y formatos deben ser aprobadas por el contador y certificadas con la impresora real.
- El VPS de demo no recibe credenciales de almacenamiento externo ni una programación productiva de respaldos.

