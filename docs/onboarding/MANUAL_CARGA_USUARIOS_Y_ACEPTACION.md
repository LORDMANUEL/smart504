# Manual de carga, usuarios y aceptación

## Portales del VPS de pruebas

- Landing/tienda: `https://taller.169.58.217.146.sslip.io/lading`
- Operaciones: `https://app.169.58.217.146.sslip.io/tallerv1/login`
- ERPNext: `https://erp.169.58.217.146.sslip.io`
- API: `https://api.169.58.217.146.sslip.io`
- Coolify: `http://169.58.217.146:8000`

Las credenciales no se guardan en documentos ni Git.

## Catálogo

1. Ingresar como administrador de catálogo.
2. Descargar y completar la plantilla 01 sin cambiar encabezados.
3. Ejecutar **Vista previa**, corregir hasta cero errores y guardar evidencia.
4. Ejecutar **Aplicar**; la escritura usa la integración con ERPNext.
5. Buscar tres SKU y comprobar costo, precio, foto, compatibilidad y existencia.

## Empleados y usuarios

1. RRHH valida identidad, contrato, salario, seguro, pago y sucursal.
2. Crear contrato; el sistema genera `EMP-######`.
3. Crear cuenta individual con correo único y asignar sólo roles aprobados.
4. Entregar contraseña temporal por canal separado y exigir cambio.
5. Probar que el lanzador sólo muestre aplicaciones autorizadas.
6. Al retirar personal, desactivar acceso sin borrar historial.

## Prueba por rol

| Rol | Flujo obligatorio |
|---|---|
| Asesor | Cita, recepción, cotización por VIN y conversión a OT |
| Técnico | OT, cronómetro, diagnóstico y fotografías |
| Bodega | Solicitud, reserva, picking, entrega y devolución |
| Caja | Apertura, cobro, referencia POS, impresión y arqueo |
| Compras | Proveedor, orden, recepción e importación |
| RRHH | Empleado, contrato, asistencia, deducción y comprobante |
| Contador | CAI, asiento, impuestos, conciliación y reportes |
| Gerencia | Margen, ventas, productividad y aprobaciones |
| Administrador | Marca, documentos, usuarios, auditoría y respaldo |

## Operación completa de aceptación

Crear cliente/VIN → cita → check-in → OT → diagnóstico con fotos → cotización HTML/PDF → aprobación → reserva y entrega → calidad → pase de salida → apertura de caja → cobro con referencia → factura → arqueo. Al final deben coincidir factura, pago, inventario y asiento en ERPNext, y el historial debe aparecer por VIN.

SMTP permanece en pausa mientras se transfiere el dominio; los eventos internos sí se validan, pero correo externo no se declara operativo.

## Acta

| Control | Responsable | Resultado | Evidencia | Fecha |
|---|---|---|---|---|
| Empresa/sucursales/bodegas | Gerencia | Pendiente | | |
| Catálogo e inventario | Bodega | Pendiente | | |
| Empleados/nómina/accesos | RRHH | Pendiente | | |
| Compra/importación | Compras | Pendiente | | |
| Cita → OT → factura | Taller | Pendiente | | |
| Fiscalidad/contabilidad | Contador | Pendiente | | |
| Documentos/impresión | Gerencia/contador | Pendiente | | |
| Seguridad/auditoría/respaldo | Administrador técnico | Pendiente | | |

No se firma hasta corregir diferencias. Hardware, SMTP o fiscalidad pendientes quedan como excepciones explícitas.
