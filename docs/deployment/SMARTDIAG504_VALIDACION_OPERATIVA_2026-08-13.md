# Validacion operativa SmartDiag504 - corte final 2026-08-13

Entorno servido: `https://taller.nexusmedi.org`.

## Despliegue

- Respaldo: `/opt/smartdiag504-demo/backups/20260813T2353Z-pre-operational-flows`.
- `database.dump` y `source.tar.gz` pasaron SHA-256.
- La base fue restaurada en `smartdiag504_restorecheck_20260813`, se comprobo `alembic_version` y luego se elimino la base temporal.
- Migracion aplicada: `0009_prequotes_by_vehicle`.
- Se recrearon solo `platform-api`, `ops-web`, `public-web` y el gateway propio del proyecto.
- Nueve contenedores persistentes del recurso SmartDiag504 quedaron saludables. No se reinicio Coolify ni Traefik.

## Pruebas locales

| Control | Resultado |
|---|---|
| API | 58 pruebas aprobadas |
| Contratos generales | 52 pruebas aprobadas |
| Operaciones web | 12 pruebas aprobadas |
| Portal publico | 5 pruebas aprobadas |
| Build operaciones | TypeScript y Vite aprobados |
| Validacion repositorio/Compose | Aprobada, 954 archivos y 38 servicios inspeccionados |

## Evidencia del runtime servido

- Diez rutas publicas y operativas solicitadas respondieron HTTP 200.
- Playwright encontro contenido real, controles interactivos y cero overlays en landing, login de cliente, login del taller, Kanban, caja, bodega, administracion, gerencia y publicidad.
- En la sesion limpia final no hubo errores de consola. Los errores historicos vistos en otras pestanas correspondian al intervalo anterior de recreacion y a descargas sin sesion.
- Portal cliente: Alertas, Cotizaciones, Facturas y Configuracion renderizaron una sola vista principal por seccion; Mi vehiculo cargo Ford Escape, Ford F-150 y Honda Civic con imagenes completas.
- Cotizacion `COT-260814-CBE18`: creada buscando placa/VIN, aprobada, persistida, convertida a OT `82c9878f-dbc1-42c4-a946-0bcecb504c7f`; PDF HTTP 200.
- Evidencia `1976f88d-fa0e-43d9-9341-a3143c9435ad`: cargada en la OT; diagnostico, factura, garantia, pase de salida y cuatro documentos de bodega devolvieron PDF HTTP 200.
- Catalogo: 13 productos activos y cero sin imagen.
- CRM: lead `LEAD-260814-5244C8`, llamada y encuesta persistidas.
- Cita del portal: `CONFIRMED`; notificacion `DELIVERED` visible para el cliente.
- Pedido `WEB-20260814-20B25832`: paso a `CONTACTED`; notificacion `DELIVERED` visible para el cliente.
- Caja: codigo incorrecto devolvio 403. El codigo valido alcanzo la regla de negocio 409 porque ya existe un turno abierto, sin cerrar ni alterar ese turno.

## Limites no certificados

- La entrega interna de notificaciones esta probada. Email, SMS y WhatsApp externos requieren proveedor y credenciales.
- Los documentos HTML/PDF estan probados. No se certifica gaveta, POS o impresora termica fisica sin modelo, controlador, conexion y ancho de papel.
- La imagen generica de repuestos es una referencia de demostracion; las publicaciones comerciales deben usar la foto exacta del numero de parte.

## Correccion de navegacion y marca

Validacion: 2026-08-13 22:46, hora local de trabajo.

- `Mapa de flujos` se retiro como modulo independiente de la barra lateral y quedo como pestaña interna de `Procesos y calidad`.
- La ruta compatible `/tallerv1/flujos` se conserva, abre `Mapa operativo de flujos` y mantiene activo el modulo padre.
- El logo SmartDiag504 usa el recurso oficial, se renderiza a 154 x 54 px, conserva sus colores y no recibe el filtro que lo ocultaba.
- La navegacion lateral tiene desplazamiento interno y mantiene visible el pie de sesion en un viewport de 945 px.
- Operaciones web: 13 pruebas aprobadas y build TypeScript/Vite aprobado.
- Runtime: `ops-web` y `gateway` saludables; `/tallerv1/flujos` HTTP 200; cero errores de consola en la sesion recargada.
- Se recrearon solo `ops-web` y el gateway propio de SmartDiag504. No se reinicio Coolify, Traefik ni otro proyecto.
- Respaldo de fuentes: `/opt/smartdiag504-demo/backups/20260813T224056Z-ui-navigation-brand`.
- Imagen de rollback: `smartdiag504-demo-ops-web:rollback-20260813T224056Z`.

## Centro documental configurable

Despliegue validado: 2026-08-14 05:00 UTC.

- Nueva ruta operativa: `/tallerv1/documentos`.
- El administrador puede crear plantillas HTML/CSS seguras, guardar nuevas versiones, previsualizarlas y publicar una version concreta.
- Tipos disponibles: cotizacion, factura, diagnostico, OT, garantia, pase de salida, picking, entrega, devolucion y entrada de bodega.
- Las cotizaciones, documentos de OT y documentos de bodega consultan primero la plantilla publicada; si no existe una, mantienen el formato de respaldo anterior.
- Cada PDF emitido conserva una copia inmutable del HTML, la version usada, la referencia de negocio, el autor y una huella SHA-256.
- La migracion `0010_document_template_center` creo `document_templates`, `document_template_versions` y `document_renders` en PostgreSQL.
- El seed dejo cuatro plantillas publicadas: `DEFAULT_QUOTE`, `DEFAULT_INVOICE`, `DEFAULT_DIAGNOSIS` y `DEFAULT_PICKING`.
- Pruebas locales: API completa 60/60, operaciones web 14/14 y build TypeScript/Vite aprobado.
- Prueba remota: cotizacion PDF HTTP 200, `application/pdf`, 2915 bytes; el historial guardo una emision `QUOTE` con SHA-256 de 64 caracteres.
- Prueba visual limpia: la pantalla de acceso sirvio las dos imagenes, incluido `/brand/smartdiag504-logo.png` de 959 x 958 px, sin errores ni advertencias de consola.
- Contenedores recreados: `platform-api`, `ops-web`, `public-web` y el gateway propio; todos saludables. Coolify, Traefik y proyectos ajenos no se reiniciaron.
- Respaldo previo: `/opt/smartdiag504-backups/20260814T050030Z`; la restauracion temporal encontro 30 tablas y se elimino al terminar.
- Rollback disponible en las etiquetas `rollback-20260814T050030Z` de API, operaciones, portal publico y gateway.

### Limite importante

Este centro resuelve el diseno, versionado y trazabilidad de los documentos. La validez fiscal hondurena sigue pendiente de configurar RTN, CAI, rango autorizado, fecha limite y reglas SAR reales; no debe confundirse un PDF funcional con una factura fiscal certificada.

## Identidad individual del personal y RBAC

Implementación local terminada el 14 de agosto de 2026.

- Nueva ruta: `/tallerv1/personal`.
- El acceso normal cambió de clave compartida a correo y contraseña individual con cookie segura `HttpOnly`.
- La clave administrativa anterior permanece sólo como recuperación temporal para crear el primer propietario.
- Roles implementados: propietario, administrador, gerente, técnico, caja, bodega, recepción, mercadeo y auditor.
- Los permisos se verifican en el API; ocultar opciones del menú no es el control de seguridad.
- El auditor tiene acceso de lectura y recibe HTTP 403 al intentar modificar datos.
- La administración permite crear empleados, cambiar roles, suspender/reactivar cuentas y consultar la bitácora de accesos.
- Migración: `0011_staff_identity_rbac`.
- Pruebas antes del despliegue: API 61/61, panel web 15/15 y build TypeScript/Vite aprobado.

### Despliegue y validación real

Despliegue completado el 14 de agosto de 2026.

- La migración `0011_staff_identity_rbac` quedó aplicada en PostgreSQL.
- Se recrearon únicamente `platform-api`, `ops-web` y el gateway propio de SmartDiag504; Coolify, Traefik y proyectos ajenos no se reiniciaron.
- Los contenedores recreados quedaron saludables.
- Respaldo previo restaurado de forma aislada: `/opt/smartdiag504-backups/20260814T113309Z-rbac`; la restauración encontró 33 tablas y la base temporal se eliminó.
- Rollback disponible para API y operaciones con la etiqueta `rollback-20260814T113309Z`.
- Se crearon ocho cuentas de demostración separadas por rol: administración, técnico, caja, bodega, recepción, gerencia, mercadeo y auditoría.
- Validación directa del API: técnico pudo consultar Kanban y recibió HTTP 403 en caja; caja pudo consultar caja y recibió HTTP 403 en administración de catálogo; auditor pudo leer Kanban y recibió HTTP 403 al intentar escribir un evento de flujo.
- Validación visual servida: el técnico sólo vio Kanban, Bahías, Catálogo y Documentos; el rol de caja vio Kanban, Cotizaciones, Caja y Documentos.
- La vista de Caja cargó el Kanban de OTs, selección de cotización, métodos POS/efectivo/transferencia, referencia, factura, garantía, pase de salida, movimientos y arqueo.
- El logo SmartDiag504 se mostró correctamente tanto en el acceso como en la barra lateral.
- El cierre de sesión eliminó la sesión y devolvió al formulario de correo y contraseña.
- La cuenta administrativa abrió `/tallerv1/personal`, mostró creación de accesos, listado de empleados y bitácora con las tildes correctas.
