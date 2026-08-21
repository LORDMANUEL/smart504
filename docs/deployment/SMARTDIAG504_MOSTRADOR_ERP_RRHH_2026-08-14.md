# SmartDiag504: Mostrador, ERPNext y RRHH

Fecha de corte: 2026-08-14. Entorno: `taller.nexusmedi.org` y `erp.nexusmedi.org`.

## Resultado entregado

Se agrego un modulo independiente de **Venta por mostrador** en
`/tallerv1/mostrador`. No reutiliza la pantalla de cobro de una OT: atiende la
venta directa de repuestos con su propio carrito, cliente, sucursal, bodega,
medio de pago, factura, devolucion e historial.

El VPS tambien tiene un stack aislado de Frappe 16, ERPNext 16 y HRMS 16. El
sitio `erp.nexusmedi.org` fue configurado para Honduras, moneda HNL, zona
`America/Tegucigalpa` y empresa `SmartDiag504 Demo`. ERPNext es la autoridad
objetivo para contabilidad e inventario; HRMS aporta empleados, asistencia y
nomina.

## Flujo funcional de mostrador

1. Caja debe tener un turno abierto.
2. El cajero selecciona sucursal y bodega.
3. El catalogo muestra precio y existencia disponible.
4. El carrito acepta cantidades sin exceder la existencia.
5. Se captura consumidor final o cliente, telefono, RTN y VIN opcional.
6. Se cobra en efectivo, tarjeta/POS o transferencia; los medios electronicos
   exigen referencia.
7. La operacion descuenta inventario de la bodega, registra movimiento y pago,
   emite numero de venta y factura, y conserva el evento de auditoria.
8. La factura HTML se transforma a PDF y queda registrada como documento
   renderizado.
9. Una devolucion valida lo ya devuelto, reintegra existencia, registra el
   reembolso y deja la venta en `PARTIAL_RETURN` o `RETURNED`.
10. Un adaptador idempotente crea y presenta en ERPNext la factura con
    `update_stock=1`, el pago, la nota de credito y el reembolso. La referencia
    operativa evita facturas duplicadas cuando se reintenta una sincronizacion.

## Datos y codigo

- Migraciones `0012_counter_sales` y `0013_counter_sales_erp_outbox`.
- Tablas nuevas: `retail_sales`, `retail_sale_items`, `retail_returns`,
  `retail_return_items`, `inventory_balances` e `inventory_movements`.
- `payments.work_order_id` ahora permite ventas que no pertenecen a una OT y
  `payments.retail_sale_id` enlaza el cobro con mostrador.
- API en `services/platform-api/app/routes/finance.py`.
- Interfaz en `apps/ops-web/src/components/CounterSalesView.tsx`.
- Permiso de servidor asociado al rol `CASHIER`; ocultar el menu no sustituye
  la autorizacion del API.
- La bodega se sincroniza despues de cargar el contexto, evitando que el
  selector quede vacio durante una carga asincrona.
- Ventas y devoluciones conservan documento ERP, pago ERP, estado, numero de
  intentos, ultimo intento y error seguro para reintentos observables.
- El API opera con `FRAPPE_REQUIRED=true` e
  `INVOICE_VERIFICATION_MODE=strict`; las credenciales viven fuera del repo.

## Evidencia de validacion

- API local: 67 pruebas aprobadas.
- Panel de operaciones: 16 pruebas aprobadas.
- Compilacion TypeScript/Vite aprobada.
- Respaldo previo con manifiesto y restauracion aislada:
  `/opt/smartdiag504-backups/20260814T141813Z-pre-counter-sales`.
- La restauracion aislada recupero 35 tablas y la base temporal fue eliminada.
- Respaldo inmediatamente anterior a la integracion:
  `/opt/smartdiag504-backups/20260814T151133Z-pre-erp-sync`; su restauracion
  aislada recupero 41 tablas PostgreSQL.
- Respaldo ERP con manifiesto SHA-256 en
  `/opt/smartdiag504-backups/20260814T150401Z-erp`; la restauracion aislada
  recupero 896 tablas MariaDB y la base temporal fue eliminada.
- Contenedores `platform-api` y `ops-web` saludables despues del despliegue.
- Flujo servido comprobado: venta `MOST-260814-816E25`, factura
  `FAC-M-260814-816E25` por L 320.00, PDF HTTP 200 `application/pdf` y
  devolucion `DEV-M-260814-65374A` por L 320.00. La venta termino en
  `RETURNED` y el inventario fue reintegrado.
- Validacion visual: sucursal principal, bodega `MAIN-STOCK`, trece productos,
  carrito, metodos de pago, historial y cero errores de consola.
- `erp.nexusmedi.org/api/method/ping` responde HTTP 200.
- Aplicaciones instaladas: Frappe 16.31.0, ERPNext 16.32.1 y HRMS 16.16.0.
- Vistas verificadas: Company, Accounting, Invoicing, Payments, Financial
  Reports, Stock, Employee y Payroll Entry.
- Conciliacion inicial `SMARTDIAG504-OPENING-STOCK-20260814`: 13 repuestos en
  `MAIN-STOCK - SD504`, sin habilitar inventario negativo.
- Venta integral `MOST-260814-B8B740`: factura ERP
  `ACC-SINV-2026-00001` presentada, pago `ACC-PAY-2026-00001` presentado,
  nota de credito `ACC-SINV-2026-00002` presentada y reembolso
  `ACC-PAY-2026-00002` presentado. El segundo reintento reutilizo la misma
  factura; el conteo por referencia permanecio en uno.
- La venta demo anterior `MOST-260814-816E25` y su devolucion tambien quedaron
  sincronizadas (`ACC-SINV-2026-00003` y `ACC-SINV-2026-00004`). El historial
  de mostrador no conserva filas pendientes de ERP.
- Auditoria de navegador con usuario de caja: cero errores y cero advertencias
  despues de la autenticacion; a 390 px no existe desbordamiento horizontal.
  Las autorizaciones de cobro y devolucion usan dialogos internos accesibles,
  no ventanas nativas del navegador.

## Infraestructura y aislamiento

El ERP se despliega desde `/opt/smartdiag504-erpnext` como proyecto Docker
`smartdiag504-erp`, con MariaDB, Redis, backend, frontend, websocket,
scheduler y colas propios. Solamente su frontend comparte la red de entrada
del recurso SmartDiag504. No se reinicio Coolify, Traefik ni otro proyecto del
VPS.

Los archivos reproducibles estan en `infra/erpnext`: manifiesto de aplicaciones,
variables de ejemplo, override de red/proxy y runbook. Las claves y contrasenas
reales no se versionan.

## Limites que no deben declararse terminados

El PDF es funcional, pero la validez fiscal hondurena exige datos y aprobacion
reales de RTN, CAI, rango autorizado, fecha limite y reglas SAR. Una impresora
termica, gaveta, lector o POS bancario solo puede certificarse con el modelo,
driver, ancho de papel y proveedor fisico que usara el taller. Meta/WhatsApp,
correo transaccional, cobro bancario y autenticacion social tambien requieren
cuentas y credenciales oficiales del negocio.

## Siguiente cierre tecnico

1. Configurar formatos fiscales y de impresion con la informacion aprobada por
   el negocio y probarlos en el hardware real.
2. Completar empleados, contratos, turnos, asistencia, estructura salarial y
   reglas de nomina con datos autorizados; no inventar datos laborales.
3. Sustituir los costos demo de apertura por costos reales aprobados antes de
   usar reportes de margen o utilidad para decisiones financieras.
# Mejora ecommerce y búsqueda por VIN — 2026-08-14

## Decisión funcional

- Mostrador y tienda separan dos intenciones: validar un vehículo por VIN y buscar libremente por nombre, SKU, marca u OEM.
- Un VIN sólo produce compatibilidad cuando existe exactamente en `vehicles`. El sistema no decodifica, completa ni inventa vehículos desconocidos.
- Los repuestos compatibles se obtienen de la compatibilidad persistida del catálogo (`compatibility_notes`) contra marca, modelo y año del vehículo registrado.
- Una carga de imagen administrada en Catálogo tiene prioridad. Si el demo todavía no tiene fotografía propia, la interfaz utiliza una imagen de referencia generada y claramente descrita como tal.

## Superficies implementadas

- Público: `GET /api/v1/catalog/fitment?vin=...` y vista `/lading/repuestos`.
- Personal: `GET /api/v1/operations/finance/counter-sales/fitment?vin=...` y vista `/tallerv1/mostrador`.
- El endpoint interno también devuelve propietario y placa para evitar recaptura en caja; el endpoint público no expone esos datos.
- Mostrador conserva existencia por bodega, cobro, factura, devolución y sincronización estricta con ERPNext.

## Activos visuales sustituibles

Los cuatro recursos bajo `apps/*/public/images/products/` cubren filtro de aceite, filtro de aire, pastillas y bujías. No contienen marcas ni afirmaciones OEM. Se reemplazan desde Catálogo cargando la fotografía real del repuesto; la base conserva esa imagen y pasa a ser la fuente visual prioritaria.

## Pruebas ejecutadas antes del despliegue

- API completa: 69 pruebas aprobadas.
- Público React: 5 pruebas aprobadas y compilación de producción aprobada.
- Operaciones React: 16 pruebas aprobadas y compilación de producción aprobada.
- Casos explícitos: VIN conocido filtra únicamente la aplicación persistida; VIN desconocido devuelve `NOT_FOUND` y cero piezas sugeridas.
