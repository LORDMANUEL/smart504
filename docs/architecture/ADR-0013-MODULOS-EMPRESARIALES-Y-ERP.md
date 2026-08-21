# ADR-0013 — Módulos empresariales y autoridad ERP

- Fecha: 2026-08-17
- Estado: aceptado para el VPS de pruebas

## Decisión

SmartDiag504 captura y presenta el trabajo diario. PostgreSQL conserva proyecciones operativas, estados, auditoría, consentimientos e idempotencia. ERPNext/HRMS conserva los documentos autoritativos de compras, recepción, costo aterrizado, empleados y nómina. SmartDiag no crea libro diario, mayor, saldos fiscales ni existencias valorizadas paralelas.

## Límites por agregado

| Agregado SmartDiag | Documento ERP autoritativo | Regla |
|---|---|---|
| Proveedor | Supplier | Alta/actualización idempotente por referencia externa. |
| Orden de compra | Purchase Order | Sólo `SYNCED` después de respuesta ERP. |
| Recepción | Purchase Receipt | `RECEIVED` requiere recepción enviada en ERP. |
| Importación | Landed Cost Voucher | Costos se distribuyen sobre la recepción; no se alteran costos locales como libro paralelo. |
| Contrato | Employee | Datos legales obligatorios; no inventar fecha de nacimiento, cargo ni compañía. |
| Nómina | Payroll Entry | SmartDiag calcula un borrador; ERP/HRMS decide deducciones, envío y asiento. |
| Vehículo usado | Item serializado | El maestro no equivale a existencia ni adquisición contable. |
| Conversación social | Notification Delivery / proveedor | Consentimiento y aprobación humana obligatorios. Sin proveedor, estado `BLOCKED` o `CONNECTOR_PENDING`. |

## Consecuencias

- Toda orden de integración tiene clave idempotente, error durable y reintento controlado.
- La sesión aporta organización, sucursal y empleado; la pantalla no puede inventar el actor.
- Una respuesta HTTP o tarjeta visual no prueba conciliación. Terminado exige referencia ERP y estado confirmado.
- Fiscalidad, nómina definitiva, entrada/venta de usados y mensajería externa requieren parametrización y evidencia externa.

