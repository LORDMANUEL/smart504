# Manual operativo completo SmartDiag504

> Actualización 2026-08-17: proveedores/compras/importación, RRHH operacional y el centro único de formatos se detallan en `docs/product/CIERRE_COMPRAS_RRHH_FORMATOS_Y_SIGUIENTES_MODULOS_2026-08-17.md`. El instalador Debian y su límite frente a Coolify se documentan en `docs/operations/INSTALADOR_DEBIAN.md`.

> La personalización central de logos, colores, datos empresariales, PDFs y empaquetado está documentada en `docs/operations/MARCA_FORMATOS_Y_EMPAQUETADO_MULTIEMPRESA_2026-08-17.md`.

Versión de trabajo para el VPS de pruebas. No equivale a certificación fiscal ni autorización de producción.

## Accesos

- Landing y tienda: `https://taller.nexusmedi.org/lading`
- Portal cliente: `https://taller.nexusmedi.org/lading/loginclie`
- Operaciones: `https://taller.nexusmedi.org/tallerv1/login`
- Portal técnico: `https://taller.nexusmedi.org/tallerv1/tecnico`
- Caja: `https://taller.nexusmedi.org/tallerv1/caja`
- Mostrador: `https://taller.nexusmedi.org/tallerv1/mostrador`
- Bodega: `https://taller.nexusmedi.org/tallerv1/bodega`
- Contador: `https://taller.nexusmedi.org/tallerv1/contador`
- Publicidad: `https://taller.nexusmedi.org/tallerv1/publicida`
- Pantalla TV: `https://taller.nexusmedi.org/tallerv1/publicida/tv`
- Administración: `https://taller.nexusmedi.org/tallerv1/3gj`
- Compras e importaciones: `https://taller.nexusmedi.org/tallerv1/compras`
- RRHH y nómina: `https://taller.nexusmedi.org/tallerv1/rrhh`
- Vehículos usados: `https://taller.nexusmedi.org/tallerv1/usados`
- Hub Social: `https://taller.nexusmedi.org/tallerv1/social`
- ERPNext administrativo: `https://erp.nexusmedi.org`

El administrador crea empleados desde **Personal y accesos**. Cada persona debe tener usuario propio, rol y sucursal; no se comparten cuentas. Los actores enviados por la pantalla no tienen autoridad: API obtiene empleado, empresa y sucursal desde la sesión.

### Accesos de demostración

La contraseña temporal común en este VPS de pruebas es `SmartDiag504-Demo!2026`. Debe cambiarse al crear un entorno nuevo.

| Rol | Usuario |
|---|---|
| Propietario | `demo.admin@smartdiag504.com` |
| Recepción | `recepcion.demo@taller.nexusmedi.org` |
| Técnico | `tecnico.demo@taller.nexusmedi.org` |
| Caja | `caja.demo@taller.nexusmedi.org` |
| Bodega | `bodega.demo@taller.nexusmedi.org` |
| Gerencia | `gerencia.demo@taller.nexusmedi.org` |
| Marketing | `mercadeo.demo@taller.nexusmedi.org` |
| Auditoría | `auditor.demo@taller.nexusmedi.org` |
| Contador | `contador.demo@taller.nexusmedi.org` |

El código privado de caja del demo es `5040`. En producción no se guarda en el repositorio: se configura como secreto, se rota por sucursal y se entrega únicamente al personal autorizado.

## Flujo eficiente del taller

1. Recepción confirma cita, identifica cliente y VIN.
2. Se crea OT; la cola crea/actualiza el `Service Order` en ERPNext.
3. El técnico abre **Mi trabajo técnico**, entra a la tarjeta de OT y registra diagnóstico, fotografías, tiempo normal o especializado y repuestos solicitados.
4. Bodega recibe la solicitud en Kanban, ubica, prepara y entrega; picking, entrega, devolución y recepción generan PDF.
5. Cotizaciones arma líneas desde la OT o busca por VIN/placa/cliente. Cada línea se aprueba o rechaza y el HTML versionado genera PDF.
6. La cotización se sincroniza como `Service Quotation`; una precotización aprobada puede convertirse en OT.
7. Procesos y calidad registra control, evidencia y resolución antes de facturar.
8. Caja abre turno, ve el Kanban de OTs aprobadas, cobra por método, imprime factura/garantía/pase y hace arqueo.
9. ERPNext conserva la factura, pago e impacto contable. Gerencia consulta la proyección conciliada y no un libro paralelo.

Si ERP muestra `FAILED` o `BLOCKED`, no repetir manualmente el documento: corregir la causa y reintentar la misma operación idempotente.

## Portal del técnico

La ruta `/tallerv1/tecnico` muestra únicamente OTs asignadas al técnico o todavía sin asignar. Cada tarjeta abre el detalle existente para:

- tomar fotografías privadas de piezas, daños y diagnóstico;
- registrar mano de obra normal o especializada con costo salarial y tarifa de venta;
- solicitar repuestos y ver su estado;
- consultar historial, cotización y eventos;
- imprimir diagnóstico con evidencia autorizada;
- avanzar sólo por transiciones válidas.

Las fotos reales requieren almacenamiento privado compatible S3 en producción; el volumen local del demo no es suficiente.

## Contador, CAI y documentos

En `/tallerv1/contador` el contador crea un borrador por sucursal y tipo documental. Debe completar razón social, RTN, CAI, vigencia, plantilla y elegir:

- **ERPNext**: ERP emite el número fiscal. No se escribe un segundo número en SmartDiag.
- **Hoja preimpresa**: se registra prefijo y rango físico autorizado. La impresión respeta el papel y SmartDiag registra el número consumido.

Después de revisar impuestos, rango, fechas y formato, el contador marca la confirmación y activa. El sistema cierra la serie anterior. Las plantillas se editan en **Documentos** y se publican por versión; el PDF conserva una huella SHA-256 del HTML renderizado.

Antes de producción el contador debe validar SAR/CAI, notas de crédito, exenciones, cierres, P&G, balance, libro diario/mayor y retenciones.

## Alertas por correo

Para la primera salida operativa sólo se exige SMTP. Meta, Facebook, WhatsApp, SMS y push son ampliaciones posteriores y no bloquean el funcionamiento del taller.

El administrador configura `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` y, si el servidor lo exige, `SMTP_USERNAME` y `SMTP_PASSWORD` como secretos del despliegue. Después debe provocar una cita o cambio de pedido y confirmar que el mensaje pase a `SENT`. Sin SMTP, la alerta queda registrada como bloqueada o pendiente; nunca se presenta como enviada.

## Publicidad y TV

En `/tallerv1/publicida`:

1. Crear campaña con título, descripción, público, vigencia, precio y llamado a la acción.
2. Indicar si aparecerá en TV y los segundos de rotación.
3. Cargar JPG/PNG/WebP o MP4/WebM.
4. Publicar y copiar el enlace medible.
5. Abrir `/tallerv1/publicida/tv` en el televisor a pantalla completa.

La TV consulta campañas publicadas vigentes, rota automáticamente y se refresca cada minuto. Una campaña sin contenido muestra diseño de marca; una campaña vencida no aparece.

## Bodega autoritativa

Una transferencia se crea como solicitada y puede prepararse y ponerse en tránsito. Al marcarla recibida, SmartDiag la deja temporalmente en `ERP_PENDING`; sólo después de que ERPNext envía el `Stock Entry` pasa a `RECEIVED`. Entonces se actualiza la proyección de cantidades local una sola vez. Si ERP falla, el movimiento conserva el error y no simula una recepción.

Las bodegas operativas recomendadas son: principal, procesos/reservado, tránsito y devoluciones. Cada una se mapea a una bodega ERPNext de la misma compañía.

## Devoluciones y garantías

Caja selecciona la venta y las unidades, explica el motivo y solicita autorización. El propietario recibe un enlace de un solo uso con vencimiento para aprobar o rechazar. Sin aprobación vigente no se permite devolver. Si cambian unidades, motivo o método de reembolso, debe solicitarse una nueva autorización.

Al confirmar una devolución, ERPNext crea una nota de crédito vinculada a la factura original, el reembolso y la entrada de inventario. SmartDiag conserva las referencias y la auditoría. Si el correo saliente no está configurado, la solicitud muestra `PENDING_EMAIL_CONFIGURATION`; nunca se debe afirmar que el propietario recibió el enlace.

## ERPNext en español

ERPNext queda detrás de la capa visual de SmartDiag para operación diaria. El administrador contable todavía puede ingresar al ERP para configuración avanzada, catálogo maestro, compañía, bodegas, impuestos, plan de cuentas y cierres. El 17 de agosto de 2026 se configuraron el idioma global y el usuario Administrator en `es`; una sesión que ya estaba abierta debe cerrar sesión e ingresar de nuevo para recargar las traducciones. Cada usuario nuevo debe conservar **Language = Español**. El idioma no altera nombres internos de DocTypes ni integraciones.

No crear empleados u OTs por duplicado en ambos sistemas. La interfaz SmartDiag es el punto de captura; ERPNext es la autoridad y devuelve referencias.

## Criterio de producción

No declarar listo hasta cumplir todos:

- migraciones y pruebas automáticas verdes en un stack servido;
- E2E por administrador, técnico, recepción, bodega, cajero, contador, marketing y cliente;
- operación cita → OT → evidencia → cotización → aprobación → bodega → calidad → factura → pago conciliada contra ERP;
- fiscalidad aprobada por contador e impresión validada en hardware real;
- MFA, recuperación, bloqueo y sesiones probados;
- fotos privadas en almacenamiento externo con URLs firmadas;
- correo/WhatsApp/SMS configurados y consentimiento documentado;
- aislamiento multiempresa probado con casos negativos;
- respaldo externo diario y restauración periódica en la infraestructura productiva;
- monitoreo, alertas, capacidad y plan de rollback aprobados.

La evidencia real de esta versión está en `docs/testing/E2E_ROLES_CONCILIACION_2026-08-17.md`. El diseño de respaldo externo, que deliberadamente no se programa en este VPS de pruebas, está en `docs/deployment/PERFIL_RESPALDO_EXTERNO_PRODUCCION.md`.

Los flujos de compras, importación, RRHH, nómina, usados y Hub Social están detallados en `docs/operations/MODULOS_EMPRESARIALES_IMPLEMENTADOS_2026-08-17.md`.
