# Tutorial guiado, accesos y creación de usuarios

Fecha de corte: 2026-08-14  
Entorno de pruebas: VPS SmartDiag504 sobre Coolify y Docker

## Regla de trabajo

La computadora local se usa sólo para conversación, edición y respaldo. No se crean máquinas virtuales ni se ejecutan localmente Python, migraciones, compilaciones o pruebas. Todo gate se ejecuta en el VPS y no se reinicia el proxy compartido de Coolify.

## Accesos

| Uso | Enlace | Quién debe entrar |
|---|---|---|
| Landing promocional | <https://taller.nexusmedi.org/lading> | Público |
| Tienda de repuestos | <https://taller.nexusmedi.org/lading/repuestos> | Público y clientes |
| Portal del cliente | <https://taller.nexusmedi.org/lading/loginclie> | Clientes |
| Operación del taller | <https://taller.nexusmedi.org/tallerv1/login> | Dueño, gerencia, recepción, técnicos, caja, bodega, mercadeo y auditoría |
| Guía interactiva | <https://taller.nexusmedi.org/tallerv1/guias> | Todo el personal autenticado |
| ERP administrativo | <https://erp.nexusmedi.org/app> | Dueño, contador, compras y RRHH autorizados |

El personal del taller trabaja en SmartDiag504. ERPNext queda detrás como fuente financiera, contable y de inventario; no es necesario entregar acceso ERP al técnico o cajero si su función completa está en SmartDiag.

## Accesos de demostración

- Administrador SmartDiag: `demo.admin@smartdiag504.com`
- Contraseña temporal demo: `SmartDiag504-Demo!2026`
- Cliente demo: `cliente.demo@smartdiag504.com`
- Contraseña cliente demo: `Cliente504-Prueba-2026!`

Estas credenciales son exclusivas de demostración. Antes de usar datos reales se deben cambiar, activar MFA y crear cuentas individuales. Nunca se comparte una cuenta de cajera, técnico o administrador.

## Crear un usuario operativo SmartDiag

1. Entre en [Operación del taller](https://taller.nexusmedi.org/tallerv1/login) con rol Dueño o Administrador.
2. Abra **Personal y accesos**.
3. Cree el registro con nombre, correo individual, código de empleado, puesto, rol, empresa, sucursal y contraseña temporal.
4. Asigne sólo el rol necesario: recepción, técnico, cajera, bodega, marketing, auditor, gerente o administrador.
5. Pida al empleado iniciar sesión y cambiar su contraseña.
6. En **Configuración > Seguridad**, active MFA y confirme el código de la aplicación autenticadora.
7. Valide que el menú muestre únicamente los módulos autorizados.

El actor de cada movimiento se obtiene de la sesión del servidor. No se debe escribir ni confiar en nombres como `cajero-demo` o `tecnico-demo` enviados por el navegador.

## Crear empleado y usuario ERPNext

1. Entre a [ERPNext](https://erp.nexusmedi.org/app) con una cuenta administrativa individual.
2. Abra **Employee** en <https://erp.nexusmedi.org/app/employee> y cree el expediente laboral.
3. Sólo si necesita trabajar dentro del ERP, abra **User** en <https://erp.nexusmedi.org/app/user> y cree la cuenta.
4. Vincule empleado y usuario, asigne compañía y roles mínimos.
5. Configure idioma **Español** en las preferencias del usuario.
6. Verifique que no pueda consultar compañías o sucursales ajenas.

No se debe crear dos veces una misma OT, factura, pago o movimiento de inventario. SmartDiag muestra una proyección operativa y ERPNext conserva la verdad autoritativa.

## Orden recomendado para levantar la operación

1. Dueño: datos legales, empresa, sucursales y responsables.
2. Administración: bodegas, cuentas, impuestos, series y plantillas.
3. Personal: usuarios, roles, salario fijo, costo por hora normal y especializada.
4. Catálogo: vehículos, manos de obra, repuestos, fotos, compatibilidad, costo aterrizado y reglas de margen.
5. Recepción: cita, confirmación, check-in y creación de OT.
6. Técnico: diagnóstico, fotos, mano de obra, repuestos y envío a aprobación.
7. Bodega: reserva, picking, entrega, devolución y documento PDF.
8. Cliente: aprobación por línea de cotización.
9. Caja: apertura, Kanban de OTs, cobro, documentos, arqueo y cierre.
10. Calidad: inspección final, garantía y pase de salida.
11. Gerencia: conciliación ERP, márgenes, productividad y excepciones.

## Estado honesto de los procesos

- Listo para demo: acceso por rol, Kanban OT, diagnóstico y fotos, catálogo, mostrador, cotizaciones, caja demo, portal cliente, documentos HTML/PDF y sincronización básica ERP.
- Parcial: bodega completa contra el stock ledger ERP, ecommerce con pago/logística real, compras, HRMS/nómina, reportería consolidada, CRM automatizado y notificaciones externas.
- Requiere proveedor o certificación: SAR/CAI, impresora fiscal/térmica y gaveta, datáfono, adquirente de pago, WhatsApp/Meta, SMS, correo transaccional y push.

## Tutorial dentro del producto

El módulo **Guía interactiva** ofrece rutas para dueño, recepción, técnico, bodega, cotizaciones/caja, mostrador, ecommerce y ERP/RRHH. Cada ruta:

- explica el objetivo y el orden;
- identifica si está lista o parcial;
- conserva el progreso en el navegador;
- abre directamente la pantalla operativa;
- evita afirmar que un canal externo está funcionando si no está configurado.
