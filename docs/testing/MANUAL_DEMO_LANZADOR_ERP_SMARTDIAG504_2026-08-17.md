# Manual de demo: lanzador y ERP SmartDiag504

Fecha de corte: 21 de agosto de 2026. Entorno: VPS de pruebas.

## Acceso

- ERP y lanzador: https://erp.nexusmedi.org/app/smartdiag-workshop
- Usuario administrativo ERP de demo: `admin@smartdiag504.com`
- Contraseña temporal: `SmartDiag504-Demo!2026`
- Operación del taller: https://taller.nexusmedi.org/tallerv1/login
- Técnico móvil: https://taller.nexusmedi.org/tallerv1/tecnico
- Portal de cliente: https://taller.nexusmedi.org/lading/cliente
- Landing y tienda: https://taller.nexusmedi.org/lading

Cambie las contraseñas y elimine usuarios demo antes de producción.

## Cómo funciona el lanzador

El centro SmartDiag504 obtiene los permisos de la sesión Frappe. Sólo muestra un DocType cuando el usuario tiene permiso de lectura. Las métricas inaccesibles se presentan como `No disponible`; nunca deben abrir un diálogo de error. Los enlaces internos conservan la sesión ERP. Los enlaces de `taller.nexusmedi.org` conservan la sesión SmartDiag si el usuario ya inició sesión en ese dominio.

El usuario de taller usa el perfil de módulos **SmartDiag504 Taller**. Este perfil oculta Integraciones, OAuth, Webhooks, impresión técnica, personalización del framework y demás escritorios de Frappe que no forman parte de su trabajo. La portada muestra actividad real reciente de facturas, órdenes de compra y empleados; no utiliza contadores simulados.

Los conectores que sí utiliza el proyecto se abren desde **Redes, correo y automatización** dentro de SmartDiag504: correo, comunicaciones, notificaciones, webhooks, acceso social y OAuth. Permanecen sujetos al rol de la sesión y requieren credenciales reales del proveedor. No se declara Meta, WhatsApp ni otra red como conectada hasta completar sus credenciales y webhook.

Al abrir cualquier lista, formulario o reporte aparece el botón flotante **Volver a SmartDiag504**. Este botón conserva la sesión ERP y devuelve al lanzador sin depender del historial del navegador.

No se pasan contraseñas en URL ni se comparten cookies entre dominios. El inicio único entre ERP y SmartDiag requiere un proveedor OIDC o un intercambio de código de un solo uso; no debe simularse con tokens permanentes.

## Prueba guiada

1. Cierre sesiones ERP anteriores y entre con el usuario administrativo demo.
2. Confirme que abre directamente `SmartDiag504` y que la interfaz está en español.
3. Abra cada enlace visible. No debe aparecer `Permission Error`, `Insufficient Permission` ni `Not found`.
4. En **Taller y servicio**, abra OT, cotización de servicio, vehículo, recepción, bahías y calidad.
5. En **Ventas, caja y clientes**, abra cliente, factura, pago, cotización, cuentas por cobrar y libro mayor.
6. En **Repuestos, compras y bodega**, abra artículo, bodega, movimiento, proveedor, orden de compra y balance de existencias.
7. En **Personal y nómina**, abra empleado, asistencia, permiso, estructura salarial, entrada de nómina y comprobante.
8. Abra los cuatro accesos SmartDiag y compruebe la pantalla correspondiente según el rol.
9. Repita en teléfono: no debe existir desplazamiento horizontal.
10. Desde una OT, factura, empleado y reporte, pulse **Volver a SmartDiag504** y confirme el retorno al lanzador.
11. Abra **Logs, flujos y contabilidad** y revise eventos SmartDiag, solicitudes de integración, errores, actividad, asientos y diarios.

## Reportes que deben demostrarse

Los reportes contables e inventario salen del ERP, no de totales inventados en la interfaz:

- cuentas por cobrar y antigüedad;
- libro mayor y balance de comprobación;
- pérdidas y ganancias;
- balance de existencias y valoración;
- compras por proveedor;
- ventas y margen por artículo;
- nómina y comprobantes cuando HRMS tenga el período aprobado.

Antes de aceptar un reporte, compare documento origen, estado enviado, moneda, empresa, sucursal, período y asiento contable. Los documentos en borrador no deben contarse como contabilizados.

## Cobertura funcional de un taller completo

La plataforma dispone de operación de taller, citas, OT, evidencia fotográfica, cotizaciones, caja/mostrador, catálogo, bodega, ecommerce, pedidos, proveedores/compras/importación, RRHH/nómina, CRM, marketing, documentos configurables, calidad y reportería ERP.

Para producción aún requieren proveedor o aceptación externa: fiscalidad SAR/CAI y formato preimpreso, hardware POS/impresoras/datáfono, SMTP, almacenamiento privado de evidencias, respaldo externo y SSO OIDC entre dominios. Estas dependencias no deben mostrarse como operativas mientras no estén configuradas.

## Validación automatizada ejecutada

El script `scripts/verify_erp_spanish_workspace.mjs` inicia sesión como el usuario indicado en `ERP_USER`, verifica escritorio y móvil, configuración regional, logo, ausencia de desbordamiento y abre todos los enlaces internos visibles buscando errores de permisos o rutas.

Resultado final del corte: 39 enlaces internos visibles probados, 0 fallos, 0 errores de consola; idioma `es`, país Honduras y zona `America/Tegucigalpa`. La prueba confirmó 3 paneles de actividad, 12 filas obtenidas del ERP, 4 indicadores de salud y el botón de retorno, sin desbordamiento horizontal en escritorio ni móvil.

Datos del VPS de pruebas verificados con el usuario demo: 8 OT, 2 cotizaciones de servicio, 2 vehículos, 29 artículos, 3 clientes, 5 proveedores, 5 órdenes de compra, 6 facturas, 6 pagos y 8 empleados. Para que recepción, bahías y calidad no aparezcan vacías durante la demostración, se ejecutó una semilla idempotente de prueba que creó `BAHIA-01`, `SD-CI-2026-00003` y `SD-QC-2026-00004`. La semilla está en `smartdiag_workshop.setup.demo_data.seed_workshop_demo` y no se ejecuta automáticamente en producción.

La prueba `scripts/verify_erp_accounting.mjs` comprobó las 6 facturas enviadas contra 24 líneas de `GL Entry`: cada factura tiene asiento y cada comprobante balancea débitos y créditos. Esto valida los datos de demostración actuales; la configuración fiscal, cuentas, impuestos, cierres y períodos de una empresa real todavía deben ser aprobados por su contador.
