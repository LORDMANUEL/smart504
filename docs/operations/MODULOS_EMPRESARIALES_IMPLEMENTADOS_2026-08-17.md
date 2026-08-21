# SmartDiag504 — módulos empresariales implementados

Estado funcional del VPS de pruebas al 17 de agosto de 2026. Se separa lo interno, lo conciliado con ERP y lo que depende de terceros.

## Accesos

- Compras e importaciones: `https://taller.nexusmedi.org/tallerv1/compras`
- RRHH y nómina: `https://taller.nexusmedi.org/tallerv1/rrhh`
- Compra y venta de usados: `https://taller.nexusmedi.org/tallerv1/usados`
- Hub Social: `https://taller.nexusmedi.org/tallerv1/social`
- Guía interactiva: menú **Tutoriales** dentro de operaciones.
- ERPNext administrativo: `https://erp.nexusmedi.org/app`

## Compras, proveedores e importación

1. Crear proveedor con código, identidad fiscal, contacto, plazo y moneda.
2. Crear una orden con varias líneas, SKU, cantidad, costo, moneda, tasa y fecha esperada.
3. Avanzar `DRAFT → SUBMITTED → APPROVED → PARTIALLY_RECEIVED/RECEIVED → CLOSED`.
4. Registrar recepciones parciales o finales por SKU y referencia; el sistema impide recibir más de lo comprado.
5. ERPNext crea `Supplier`, `Purchase Order` y un `Purchase Receipt` idempotente por cada recepción en bodega válida.
6. Abrir importación con Incoterm, origen, puerto, ETA, documentos, flete, seguro, aduana, impuestos y manejo.
7. Avanzar `PLANNED → IN_TRANSIT → CUSTOMS → RECEIVED → ALLOCATED`.
8. Al asignar, ERPNext crea y envía `Landed Cost Voucher` sobre las recepciones reales.

El costo vive en ERP. La proyección SmartDiag sirve para seguimiento y UX; no reemplaza valoración ni cuentas por pagar.

## RRHH, asistencia y nómina

El contrato exige código, nombre, fecha de nacimiento, cargo, tipo, inicio, salario mensual, horas semanales y moneda. ERP crea `Employee` y el maestro de cargo cuando corresponde.

El contrato también conserva el horario semanal y puede editarse o terminarse de forma auditada. La asistencia registra horas regulares/extra, estado y actor de sesión. Las horas extra quedan pendientes y sólo entran en nómina después de aprobación. Los permisos admiten vacaciones, incapacidad, asuntos personales, maternidad, paternidad o ausencia sin goce, con decisión auditada.

El borrador calcula `hora base = salario mensual / (horas semanales × 4.3333)` y `hora extra = hora base × 1.5`. Permite comisiones, bonos, asignaciones y deducciones trazables. Al aprobar crea `Payroll Entry` en HRMS. SmartDiag conserva `APPROVED:SYNCED`; no lo marca contabilizado. Deducciones legales, seguridad social, retenciones, recibos, pago y asiento se configuran y envían en HRMS.

## Vehículos usados

Registra VIN único, marca, modelo, año, kilometraje, compra/consignación/permuta, costos, precio objetivo, propietario, inspección y medios. Estados: `APPRAISAL → ACQUIRED → RECONDITIONING → READY → PUBLISHED → RESERVED/SOLD`.

Al adquirir se crea el maestro serializado en ERP. Esto no acredita existencia ni costo contable. Faltan antes de producción los documentos ERP de entrada, consignación, liquidación, factura y financiamiento.

## Hub Social

Registra canales, conversaciones, contacto, consentimiento y respuestas. Una salida requiere `OPTED_IN` y aprobación humana. Secretos sólo se referencian como `secret://` o `vault://`. Email/WhatsApp pasan al worker; Facebook/Instagram sin conector quedan `CONNECTOR_PENDING`; proveedor ausente queda `BLOCKED`, nunca `SENT`.

En este VPS WhatsApp está bloqueado por falta de webhook/token real. Configurarlo corresponde al entorno productivo.

## Seguridad y multiempresa

Las tablas empresariales incluyen `organization_id`, timestamps e índices. Consultas tenant-scoped usan la sesión. Permisos nuevos: `PROCUREMENT`, `HR`, `USED_VEHICLES`, `SOCIAL` y `ENTERPRISE`. La migración `0022` creó los módulos, `0023` agregó fecha de nacimiento sin inventarla en registros previos y `0024` incorporó horario contractual y aprobación de horas extra.

Los formatos de impresión se administran en `/tallerv1/documentos`. Cada empresa puede cargar HTML y CSS, reemplazarlo creando una versión nueva, publicarlo, previsualizarlo y exportar un respaldo JSON. La sucursal es opcional y los documentos emitidos conservan versión y hash.

## Evidencia del VPS

- Suite completa de API: aprobada en un contenedor del VPS.
- TypeScript/Vite: 1,610 módulos compilados.
- Alembic: `0024_procurement_hr_operations (head)`.
- Readiness: base, Valkey, esquema, ERP, IA y seguridad en `ok`.
- ERPNext/HRMS: `smartdiag504-erpnext-workshop:20`.
- E2E servido: proveedor `SYNCED`; compra con recepción parcial/final `RECEIVED:SYNCED`; importación multicosto `ALLOCATED:SYNCED`; contrato `SYNCED`; horas extra `APPROVED`; nómina con comisión `APPROVED:SYNCED`; formato HTML/CSS importado/exportado; usado `ACQUIRED`.
- Cola ERP: cero trabajos fallidos.
- WhatsApp: mensaje encolado y luego `BLOCKED` al faltar proveedor, como debe ser.
- Navegador servido: once vistas aprobadas, sin overlays ni errores de consola. Detalle en `docs/testing/VALIDACION_COMPRAS_RRHH_FORMATOS_DEB_2026-08-17.md`.

## No se declara terminado

- SAR/CAI, rangos, impuestos y papel preimpreso aprobados por contador.
- Datáfono, impresora, gaveta y lectores reales.
- Deducciones y pago definitivo de nómina HRMS.
- Entrada/venta/financiamiento contable de usados.
- Credenciales Meta, WhatsApp, correo, SMS y push.
- Pago ecommerce, transportistas, S3 privado, MFA productivo y aislamiento negativo con dos empresas reales.
- Respaldo externo/restauración: se diseña para producción y no se programa en este VPS de pruebas.
