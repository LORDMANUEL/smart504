# Manual ERPNext conectado a SmartDiag504

Fecha de validación: 17 de agosto de 2026  
Entorno: VPS de pruebas `erp.nexusmedi.org`

## 1. Acceso

- Inicio ERPNext: `https://erp.nexusmedi.org`
- Centro SmartDiag504 dentro del ERP: `https://erp.nexusmedi.org/app/smartdiag-workshop`
- Usuario administrador de pruebas: `Administrator`
- Contraseña temporal de pruebas: `SmartDiag504-Demo!2026`

Esta contraseña sólo corresponde al VPS demo y debe rotarse antes de copiar la solución a producción. Cada empleado debe usar una cuenta individual y los permisos mínimos de su función.

## 2. Qué hace cada plataforma

SmartDiag504 es la capa operativa rápida. Allí trabajan recepción, técnicos, caja, bodega, ventas y cliente. ERPNext/HRMS es la fuente administrativa y financiera para empleados, artículos, bodegas, proveedores, compras, facturas, pagos, nómina y contabilidad.

No se debe registrar una misma factura o movimiento dos veces. Si SmartDiag indica sincronización pendiente o fallida, se corrige la integración y se reintenta el mismo documento.

## 3. Configuración regional aplicada

- Idioma general y cuenta Administrator: español (`es`).
- País: Honduras.
- Zona horaria: `America/Tegucigalpa`.
- Moneda predeterminada: HNL.
- Fecha: día-mes-año.
- Logo y aplicación: SmartDiag504.
- Workspace inicial: SmartDiag504.

ERPNext conserva traducciones oficiales para sus módulos. Los nombres propios de la integración aparecen directamente en español para evitar mezclar términos ingleses en la portada.

## 4. Portada SmartDiag504

La portada incluye indicadores de OT abiertas, facturas pendientes, compras abiertas y empleados activos. Sus accesos externos son:

- **Abrir taller operativo:** `/tallerv1/login`.
- **Técnico móvil:** `/tallerv1/tecnico`.
- **Portal del cliente:** `/lading/cliente`.
- **Landing y tienda:** `/lading`.

La vista se adapta a escritorio y teléfono sin desplazamiento horizontal.

## 5. Secciones administrativas

### Taller y servicio

- Órdenes de trabajo (`Service Order`).
- Cotizaciones de servicio.
- Vehículos.
- Recepción del vehículo.
- Bahías.
- Control de calidad.

Los técnicos ejecutan el trabajo y cargan fotos desde SmartDiag504. ERPNext conserva el documento empresarial sincronizado.

### Ventas, caja y clientes

- Clientes.
- Facturas de venta.
- Pagos.
- Cotizaciones.
- Cuentas por cobrar.
- Libro mayor.

Caja cobra desde la vista operativa; ERPNext confirma factura, pago y asiento. El contador configura impuestos, CAI, series y cuentas antes de producción.

### Repuestos, compras y bodega

- Artículos y repuestos.
- Bodegas.
- Movimientos de inventario.
- Proveedores.
- Órdenes de compra.
- Balance de existencias.

Los picking y entregas se hacen desde SmartDiag504; el movimiento autoritativo queda en el ledger de inventario ERP.

### Personal y nómina

- Empleados.
- Asistencia.
- Permisos.
- Estructuras salariales.
- Entradas de nómina.
- Comprobantes de salario.

El técnico marca entrada/salida, pide permisos y consulta vouchers desde su portal móvil. RRHH revisa y ERPNext/HRMS contabiliza la nómina aprobada.

## 6. Creación de usuarios

1. Entre como administrador.
2. Abra **Usuarios** desde el buscador superior.
3. Cree correo, nombre completo e idioma español.
4. Asigne sólo los roles necesarios.
5. Vincule el usuario con el empleado correspondiente.
6. Pruebe el acceso en una ventana privada.
7. Cambie la contraseña temporal y active MFA cuando el entorno productivo lo permita.

Roles principales de la integración: Workshop Manager, Service Advisor, Workshop Technician, Workshop Quality Inspector, Parts Clerk y Workshop Cashier. Los roles contables, de bodega y RRHH siguen siendo los estándares de ERPNext/HRMS.

## 7. Despliegue y reversión

La aplicación `smartdiag_workshop` contiene Page, Workspace, logo, CSS, JavaScript y configuración idempotente. `bench migrate` registra la vista y ejecuta la regionalización. Los assets llevan versión para evitar que la caché pública entregue archivos anteriores.

Respaldo previo en el VPS:

`/opt/smartdiag504-backups/pre-20260817-erp-spanish-workspace/`

Imagen de reversión:

`smartdiag504-erpnext-workshop:pre-20260817-erp-spanish-workspace`

La reversión exige restaurar imagen, ejecutar Compose sólo para los servicios ERP afectados y, si los datos lo requieren, restaurar el backup de sitio en un procedimiento controlado.

## 8. Validación ejecutada

- Page `smartdiag-workshop`: HTTP 200.
- Workspace `SmartDiag504`: HTTP 200.
- Logo, CSS y JavaScript: HTTP 200 con MIME correcto.
- Idioma `es`, Honduras y `America/Tegucigalpa`: confirmados por API autenticada.
- Escritorio 1440×1000: aprobado.
- Móvil 390×844: aprobado.
- Cuatro enlaces entre ERP y SmartDiag504: aprobados.
- Sin desbordamiento horizontal.
- Sin errores de consola.

La validación demuestra funcionamiento técnico en el VPS demo. No certifica fiscalidad hondureña, hardware POS, cierre contable ni permisos definitivos de producción.
