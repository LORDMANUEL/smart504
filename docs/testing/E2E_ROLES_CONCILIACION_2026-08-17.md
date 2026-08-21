# Evidencia E2E por roles y conciliación

Fecha de ejecución: 17 de agosto de 2026. Entorno: VPS de pruebas `taller.nexusmedi.org`; no es certificación productiva ni fiscal.

## Pruebas servidas por rol

Cada usuario inició sesión contra la aplicación publicada y consultó un recurso protegido correspondiente a su rol. Los nueve inicios devolvieron `204` y los nueve recursos autorizados devolvieron `200`.

| Rol | Usuario de prueba | Recurso comprobado | Resultado |
|---|---|---|---|
| Propietario | `demo.admin@smartdiag504.com` | usuarios y administración | Aprobado |
| Recepción | `recepcion.demo@taller.nexusmedi.org` | agenda de citas | Aprobado |
| Técnico | `tecnico.demo@taller.nexusmedi.org` | Kanban y portal `/tallerv1/tecnico` | Aprobado |
| Cajero | `caja.demo@taller.nexusmedi.org` | resumen de caja y venta mostrador | Aprobado |
| Bodega | `bodega.demo@taller.nexusmedi.org` | overview, traslado y conciliación | Aprobado |
| Gerencia | `gerencia.demo@taller.nexusmedi.org` | reporte financiero | Aprobado |
| Marketing | `mercadeo.demo@taller.nexusmedi.org` | campañas y TV | Aprobado |
| Auditor | `auditor.demo@taller.nexusmedi.org` | mapa de eventos | Aprobado |
| Contador | `contador.demo@taller.nexusmedi.org` | reporte y configuración fiscal | Aprobado |

El navegador servido comprobó además:

- el técnico vio dos OTs, abrió `OT-2026-000008` y encontró las vistas Resumen, Mano de obra, Fotos, Repuestos, Historial y Manuales;
- la vista Fotos mostró carga de imagen e impresión del diagnóstico;
- el contador abrió `/tallerv1/contador`, vio la única serie activa y el selector ERPNext/hoja preimpresa;
- `/tallerv1/publicida/tv` reprodujo una campaña publicada con imagen, precio y llamada a la acción, sin errores de consola.

## Operaciones autoritativas conciliadas

### Cotización

- Cotización SmartDiag: `COT-260817-1823E`, total L 850.00.
- Vehículo: Ford Escape 2020, VIN `1FMCU0G6XLUA12545`.
- Estado de sincronización: `SYNCED`.
- Documento ERPNext: `SQ-2026-00001`.
- HTML servido: `200 text/html`; PDF comenzó con la firma `%PDF-`.

### Venta, pago, contabilidad e inventario

- Venta SmartDiag: `MOST-260817-404871`.
- Factura operativa: `FAC-M-260817-404871`.
- Total y cobro: L 320.00.
- Factura ERPNext: `ACC-SINV-2026-00005`, enviada, pagada y con saldo 0.00.
- Pago ERPNext: `ACC-PAY-2026-00005`, enviado, L 320.00 y sin monto sin asignar.
- GL factura: débito Clientes L 320, crédito Ventas L 320, débito Costo de ventas L 192 y crédito Inventario L 192.
- GL pago: débito Transferencias por confirmar L 320 y crédito Clientes L 320.
- Stock Ledger: una unidad de `SD-SPARK-PLUG-001` salió de `MAIN-STOCK - SD504`.
- El actor enviado por el navegador fue descartado; venta y recibo quedaron auditados como `CAJ-DEMO` desde la sesión.
- PDF de factura comenzó con la firma `%PDF-`.

### Traslado entre bodegas

- Movimiento SmartDiag: `MOV-260817-F425AB`.
- Actor autoritativo: `BOD-DEMO`.
- Stock Entry ERPNext: `MAT-STE-2026-00001`, enviado.
- ERP movió una unidad de `SD-SPARK-PLUG-001` de `MAIN-STOCK - SD504` a `PROCESS-E2E - SD504`.
- La proyección local quedó en 22 unidades en `MAIN-STOCK` y 1 en `PROCESS-E2E`, con referencia `MAT-STE-2026-00001`.

### Autorización y devolución

- Solicitud de autorización: `90eed1a4-82c5-4b10-b7d0-3b97d0e51a9f`.
- La identidad solicitante quedó como `CAJ-DEMO`, no como el actor enviado por la pantalla.
- El correo quedó explícitamente en `PENDING_EMAIL_CONFIGURATION`; el sistema no simuló una entrega.
- El enlace público fue aprobado una sola vez y luego consumido por la devolución `DEV-M-260817-270F05`.
- Nota de crédito ERPNext: `ACC-SINV-2026-00006`, retorno enviado contra `ACC-SINV-2026-00005`, total L -320 y saldo cero.
- Reembolso ERPNext: `ACC-PAY-2026-00006`, enviado y completamente asignado.
- GL revirtió venta, cuenta por cobrar, costo e inventario; Stock Ledger reintegró una unidad a `MAIN-STOCK - SD504`.

## Configuración fiscal comprobada

Se creó el borrador `E2E-FISCAL-20260817T140806Z`. La activación sin confirmación del contador devolvió `422`; con confirmación pasó a `ACTIVE`. Es una configuración marcada como prueba y no contiene autorización SAR real.

## Problemas encontrados y correcciones

1. La migración Alembic usó inicialmente un identificador mayor a 32 caracteres. La transacción falló sin cambios parciales; se acortó a `0021_quote_inventory_erp` y se repitió correctamente.
2. Frappe intentó reescribir campos personalizados antiguos durante `after_migrate`. Se cambió a creación idempotente sin actualización masiva y la migración terminó.
3. Las credenciales demo por rol no eran reproducibles. Se normalizaron en este VPS de pruebas y se agregó el contador.
4. El código privado de caja no estaba documentado. En pruebas quedó `5040`; producción debe inyectar y rotar otro valor mediante secretos de Coolify.
5. Un traslado podía quedar confirmado en ERP sin actualizar su proyección PostgreSQL. Ahora la proyección se ajusta sólo después del `Stock Entry`, bajo bloqueo y una sola vez.
6. ERPNext tenía idioma global inglés. Se estableció `System Settings.language = es` y `Administrator.language = es`; las sesiones ERP ya abiertas deben volver a iniciar para aplicar la traducción.
7. Reservas, fletes, calidad, CRM y aprobación de cotizaciones todavía aceptaban el actor descriptivo del navegador en algunos campos. Se normalizaron para tomar siempre el código del empleado autenticado.

## Pruebas automáticas

- API: 84 pruebas aprobadas dentro de un contenedor construido en el VPS.
- Ops web: 18 pruebas aprobadas y compilación TypeScript/Vite exitosa en el VPS.
- Migración activa: `0023_employee_birth_date (head)`.

## Validación empresarial servida — 2026-08-17

Se ejecutó `scripts/validate_enterprise_served.sh` contra el dominio HTTPS real. Resultado: proveedor `SYNCED`, compra `RECEIVED:SYNCED`, importación `ALLOCATED:SYNCED`, contrato `SYNCED`, nómina `APPROVED:SYNCED`, usado `ACQUIRED` y mensaje social `QUEUED`. El worker cambió la entrega WhatsApp a `BLOCKED` porque no hay proveedor configurado en este VPS. La consulta posterior de trabajos ERP fallidos devolvió `[]`.

La primera corrida reveló y permitió corregir tres fallos reales: bodega faltante en recepción, cuenta de pasivo obligatoria en `Payroll Entry` y fecha de nacimiento obligatoria en `Employee`. La fecha no se rellenó por defecto: ahora interfaz/API la exige y el dato E2E incompleto se corrigió explícitamente antes del reintento.

Playwright Chromium se ejecutó dentro del VPS contra el dominio servido. Compras, RRHH, usados, Hub Social, portal técnico, guía interactiva y TV devolvieron contenido real, cero overlays y cero errores de consola después del inicio de sesión. Las capturas están en `docs/testing/evidence/enterprise-ui-20260817/`.

## Límites que bloquean producción

No se validaron en este VPS: CAI/SAR real, impresora térmica, gaveta, lector, datáfono, proveedor de correo/WhatsApp/SMS, almacenamiento S3 privado, aislamiento multiempresa negativo, ni restauración desde un proveedor externo. Estos controles requieren contador, hardware, credenciales o infraestructura productiva y no deben declararse aprobados.
