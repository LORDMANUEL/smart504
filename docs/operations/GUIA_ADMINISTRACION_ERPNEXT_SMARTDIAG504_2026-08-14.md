# Guía de administración: SmartDiag504 + ERPNext

Fecha de corte: 2026-08-14  
Ámbito: demo de taller en `taller.nexusmedi.org` y ERP en `erp.nexusmedi.org`.

## 1. Qué hace cada sistema

SmartDiag504 es la única interfaz de negocio. El técnico, recepción, caja, bodega, mercadeo, gerencia y contabilidad trabajan en vistas simples por rol. ERPNext queda al fondo como fuente de verdad financiera, laboral y de inventario valorizado: artículos, costos, bodegas contables, facturas oficiales, pagos, compras, empleados, impuestos y libros. Su escritorio estándar no forma parte de la capacitación normal.

No se deben capturar dos veces los mismos documentos. SmartDiag envía al ERP únicamente el movimiento que ya fue validado por el flujo operativo y conserva su identificador ERP, estado de sincronización y error auditable.

| Persona | Entrada normal | Trabajo principal | Resultado que llega al ERP |
|---|---|---|---|
| Técnico | `/tallerv1/login` | OT, diagnóstico, evidencias, tiempo y solicitud de piezas | Consumo aprobado y servicios facturables |
| Recepción | `/tallerv1/citas` y cotizaciones | Cliente, VIN, cita, inspección y aprobación | Cliente/vehículo y documento comercial aprobado |
| Cajera | `/tallerv1/mostrador` y `/tallerv1/caja` | Cotizar, cobrar, devolver, cierre y documentos | Factura, pago, nota de crédito y movimiento de stock |
| Bodega | `/tallerv1/bodega` | Reserva, picking, entrega, devolución y recepción | Salida/entrada o transferencia de inventario |
| Dueño/contador | `/tallerv1/3gj` y `/tallerv1/gerencia` | Política, autorización, compras, impuestos y cierre | Consultas y documentos respaldados por el ERP |

## 2. Cómo se une una operación

1. SmartDiag identifica la empresa, sucursal, bodega, usuario y documento origen.
2. La API valida permiso, existencia, precio mínimo, aprobación y estado del turno.
3. La operación local se guarda con un evento idempotente en PostgreSQL.
4. La cola ERP crea o actualiza el documento equivalente en ERPNext usando una referencia única.
5. SmartDiag guarda el ID de ERP y muestra `Contabilizada`, `Pendiente ERP` o `Error ERP`.
6. Un reintento usa la misma referencia; no debe crear otra factura.

Una respuesta HTTP 200 o un contenedor saludable no demuestra que el asiento exista. La validación funcional debe comprobar el ID ERP, el documento enviado y su efecto en inventario/pago.

## 3. Administración diaria sin confundir al personal

### Personal y accesos SmartDiag

Ruta: `/tallerv1/personal`.

El gerente crea el acceso operativo, asigna sucursal y uno de estos roles: gerente, técnico, caja, bodega, recepción, mercadeo o auditor. Cada persona usa su propia cuenta y código privado; no se comparten usuarios. Los técnicos entran a SmartDiag, no al escritorio contable de ERPNext.

### Empleados y RR. HH. oficiales

El registro laboral, contrato, departamento, asistencia y nómina viven en ERPNext/HRMS, pero se administrarán desde el módulo de Personal SmartDiag. Durante esta etapa, el código de empleado de SmartDiag debe coincidir con `Employee ID` del ERP. La pantalla de usuarios ya controla acceso a la aplicación; la ficha laboral completa y su sincronización automática siguen siendo un bloque pendiente y no deben presentarse como terminados.

### Productos, costos y precios

SmartDiag: `/tallerv1/catalogo`. El usuario no necesita abrir Item, Item Price, Purchase Receipt o Warehouse en el frontend estándar de ERPNext.

ERPNext conserva el artículo y su costo valorizado. SmartDiag proyecta ese costo para bloquear ventas riesgosas y permitir una configuración operativa sencilla:

- `costo puesto = costo de compra × factor de importación`;
- `precio mínimo = costo puesto × (1 + margen mínimo / 100)`;
- `precio sugerido = costo puesto × (1 + margen objetivo / 100)`;
- el descuento máximo es la diferencia entre el precio de lista y el precio mínimo total;
- si falta costo confiable, el producto debe revisarse antes de habilitar descuentos.

Ejemplo: compra L 1,000; factor 1.25; margen mínimo 20 %. Costo puesto L 1,250 y piso L 1,500. Una promoción puede bajar hasta L 1,500, nunca a L 1,499.99.

### Plantillas de factura y cotización

Ruta: `/tallerv1/documentos`.

Cada plantilla es HTML editable con variables permitidas, historial de versión, vista previa y conversión a PDF. La empresa puede reemplazar logo, encabezado, pie, textos y columnas sin cambiar el código fuente. Una versión publicada queda asociada al documento generado para que una edición posterior no altere impresiones históricas.

Para documentos fiscales, el número, CAI/rango, impuestos y datos legales deben provenir de configuración autorizada y del ERP. La plantilla modifica presentación; no puede cambiar totales contabilizados.

### Mostrador y seguimiento comercial

Ruta: `/tallerv1/mostrador`.

1. La cajera consulta VIN; SmartDiag muestra únicamente piezas compatibles y existencia publicada.
2. Puede buscar por SKU, OEM o nombre y ver imagen, precio, piso y clase ABC/XYZ.
3. `Guardar cotización y seguimiento` crea una cotización ligada al cliente/vehículo y la envía al Kanban de Mostrador.
4. El Kanban separa por contactar, en seguimiento, aprobada y no concretada.
5. `Cobrar, descontar existencia y facturar` exige caja abierta y código privado.
6. Al finalizar se genera PDF y queda visible el estado de sincronización ERP.

### Devoluciones y garantías

Desde la venta, la cajera elige devolución o garantía, cantidad y motivo. El sistema genera un token aleatorio, guarda únicamente su hash y envía un enlace con vencimiento al correo configurado del dueño. El dueño aprueba o rechaza una sola vez. La devolución sólo puede ejecutarse si la aprobación coincide con venta, piezas, cantidades, método y motivo. Al consumirla no vuelve a utilizarse.

El envío automático requiere SMTP configurado. Sin SMTP, la solicitud se guarda como `PENDING_EMAIL_CONFIGURATION` y el enlace se puede copiar desde el panel para pruebas; no se presenta falsamente como correo enviado.

### Caja y reportes

La caja exige apertura, fondo, usuario/código, cobros por efectivo/POS/transferencia, factura PDF, devolución autorizada, arqueo y cierre. SmartDiag muestra venta neta, costo, ganancia bruta, margen y movimientos pendientes. Los reportes de factura, pagos, libro diario/mayor, ventas por artículo, existencias valorizadas y cuentas por cobrar deben consultarse por API y representarse dentro de Gerencia SmartDiag. No se enlaza al escritorio ERP como solución de experiencia de usuario.

La ganancia operativa de SmartDiag sirve para gestionar el día. El estado de resultados y los libros del ERP son la referencia contable.

## 4. ABC/XYZ para compras

La política se recalcula con valor de inventario y variabilidad de demanda de 180 días:

- A: mayor valor económico acumulado; control y conteo frecuentes.
- B: valor intermedio; revisión programada.
- C: bajo valor; reposición simple, sin comprar cantidades ciegamente.
- X: demanda estable; punto de reorden predecible.
- Y: demanda variable/estacional; revisar campañas y estacionalidad.
- Z: demanda irregular o escasa; comprar contra pedido o reserva.

Reglas sugeridas: AX mantiene stock de seguridad y reposición frecuente; AY usa pronóstico estacional; AZ requiere autorización; BX/BY revisión periódica; CZ sólo bajo pedido salvo consumibles críticos. La clasificación recomienda, no compra sola ni sustituye la aprobación humana.

## 5. Idioma y frontend del ERPNext

El frontend estándar de ERPNext queda reservado a soporte, migraciones y contingencia. Se configura en español para esos administradores, pero el idioma que verá el personal proviene de SmartDiag. En ERP el idioma se configura en tres niveles:

1. `System Settings > Language = Español` para el valor predeterminado.
2. `User > Language = Español` para cada usuario interactivo.
3. `My Settings > Language = Español` si el usuario desea sobrescribirlo.

Después se limpia caché y se vuelve a iniciar sesión. La empresa debe conservar `Honduras`, moneda `HNL` y zona horaria `America/Tegucigalpa`. Traducir la interfaz no cambia el plan contable ni los datos fiscales.

## 6. Alta inicial de una empresa

1. Crear compañía, moneda, país, zona horaria y año fiscal en ERPNext.
2. Configurar plan contable, impuestos, series, CAI/rangos y cuentas de caja/banco con un contador hondureño.
3. Crear sucursales/bodegas y relacionarlas con las vistas SmartDiag.
4. Crear empleados en HRMS y accesos operativos en SmartDiag usando el mismo código de empleado.
5. Importar artículos y precios; registrar recepción de compra para obtener costo real.
6. Configurar factores/márgenes y revisar la tabla ABC/XYZ.
7. Publicar plantillas de cotización, factura, picking, entrega y devolución.
8. Configurar SMTP y probar un correo de autorización en un buzón controlado.
9. Ejecutar venta completa de prueba: VIN → cotización → aprobación → caja → ERP → PDF → reporte.
10. Ejecutar devolución completa: solicitud → correo/enlace → aprobación → nota de crédito → inventario → reporte.

## 7. Límites actuales que no deben ocultarse

- La creación de empleados en HRMS y la creación de acceso SmartDiag son registros relacionados, pero todavía no constituyen un alta automática bidireccional.
- Sin SMTP válido, el enlace de autorización funciona y queda auditado, pero no se entrega por correo automáticamente.
- Las métricas SmartDiag son operativas; la certificación fiscal depende de la configuración contable/legal de ERPNext.
- ABC/XYZ necesita historial suficiente. Un producto nuevo o sin demanda queda marcado para revisión, no para reposición automática.

Estos límites deben mostrarse durante capacitación y cerrarse con credenciales/configuración reales; no se deben sustituir con datos simulados.

## 8. Cobertura del backend ERP validada en código

| Contrato SmartDiag → ERP | Estado | Evidencia funcional esperada |
|---|---|---|
| Leer artículos, lista de precios, existencias y costo valorizado | Implementado | Sincronización Item + Item Price + Bin hacia la proyección visual |
| Importar catálogo de mano de obra y repuestos XLSX | Implementado mediante app Frappe | Resultado de importación y posterior sincronización visible |
| Venta de mostrador | Implementado | Sales Invoice enviada con stock y Payment Entry; IDs guardados |
| Reintento sin duplicar venta | Implementado | Búsqueda por referencia `po_no` antes de crear |
| Devolución | Implementado | Nota de crédito contra factura original y movimiento inverso |
| Alta/edición de empleados HRMS desde SmartDiag | Pendiente | Debe crear/actualizar Employee y luego acceso por rol |
| Compras, recepción e importación desde SmartDiag | Pendiente | Purchase Order, Purchase Receipt y Landed Cost Voucher |
| Reportes contables embebidos | Pendiente | Consultas tipadas a reportes ERP, filtros y exportación PDF/XLSX |
| Nómina y asistencia embebidas | Pendiente | Contratos de lectura/escritura controlada de HRMS |
| Configuración fiscal completa desde SmartDiag | Pendiente y de alto riesgo | Requiere permisos separados, validaciones y contador responsable |

La siguiente ampliación no debe copiar tablas contables a PostgreSQL. Se crearán adaptadores tipados por dominio (`catalog`, `purchasing`, `hr`, `accounting-reports`) que validen las respuestas externas, oculten secretos, normalicen errores y expongan a React sólo los campos requeridos por cada vista.
