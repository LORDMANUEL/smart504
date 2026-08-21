# Portal cliente, caja, pedidos y publicidad

Fecha: 13 de agosto de 2026. Alcance: demo de taller en `taller.nexusmedi.org`.

## Resultado funcional

La navegación del cliente deja de mostrar todos los bloques a la vez. Cada opción del menú controla una vista independiente y conserva una URL con fragmento: `#vehicle`, `#appointments`, `#parts`, `#alerts`, `#quotes`, `#invoices` y `#settings`.

### Portal del cliente

- **Mi vehículo:** fotografía PNG sin fondo, selector de vehículo, kilometraje, próximo servicio, último/próximo cambio de aceite, historial rápido, consejos preventivos y alta de otro vehículo por VIN.
- **Agendar cita:** calendario autenticado ligado al cliente y vehículo. Se mantiene separado de la captación pública de la landing para medir ambos embudos.
- **Alertas:** concentra mantenimiento y cotizaciones con conceptos pendientes de aprobación.
- **Cotizaciones:** orden descendente por fecha, detalle por concepto, aprobación o rechazo individual, impresión HTML y descarga PDF.
- **Facturas:** historial derivado de cobros persistidos y descarga del documento.
- **Configuración:** nombre, correo, usuario, cambio de contraseña con PBKDF2, preferencia MFA, solicitud de crédito y puntos de lealtad cuando el negocio los habilita.

Las imágenes transparentes incluidas son Ford Escape 2020, Ford F-150 2020 y Honda Civic 2008. Se sirven desde `/vehicles/` y también quedan dentro de la imagen Docker del portal.

## Cotización y documentos

El HTML es el documento canónico. Contiene número, OT, cliente, vehículo, fecha, estado, conceptos, cantidades, precios, decisiones, subtotal, descuento, impuesto y total. El mismo HTML se transforma a PDF en el servidor mediante `xhtml2pdf`; así la impresión y el archivo descargable no dependen de una captura del navegador.

Flujo:

1. El asesor abre **Cotizaciones** y selecciona una OT.
2. Puede armar la cotización desde el diagnóstico y los repuestos solicitados en la OT, o agregar conceptos manualmente.
3. El cliente aprueba o rechaza conceptos desde **Alertas** o **Cotizaciones**.
4. Caja ve la OT en su Kanban según estado y únicamente cobra una cotización aprobada.
5. Se registran forma de pago, referencia POS/transferencia, recibo y trazabilidad.
6. Desde la OT se generan factura de operación, garantía y pase de salida en PDF.

La factura generada es operativa para la demo. No se presenta como factura fiscal SAR hasta configurar RTN, CAI, rango autorizado y plantilla legal del taller.

## Caja y POS

El módulo `/tallerv1/caja` contiene:

- Kanban **Validar OT**, **Cobro parcial** y **Pagada**;
- detalle de la cotización seleccionada;
- apertura de turno y fondo inicial;
- efectivo, tarjeta/POS y transferencia;
- referencia obligatoria para métodos electrónicos;
- impresión de factura, garantía y pase de salida;
- arqueo, efectivo esperado, conteo, diferencia, cierre y reporte del último turno.

La integración actual registra el resultado de un POS externo. No almacena número de tarjeta ni simula conexión con un adquirente.

## Kanban de pedidos web

El módulo de pedidos clasifica y conserva los estados solicitados:

| Columna | Estado persistido |
|---|---|
| Entró | `PENDING_CONFIRMATION` |
| Contestado | `CONTACTED` |
| Pagado | `PAID` |
| Enviado | `SHIPPED` |
| Devuelto | `RETURNED` |
| No contestó | `NO_RESPONSE` |
| Venta hecha | `COMPLETED` |
| Venta perdida | `LOST` |

Cada tarjeta abre un panel de trabajo con cliente, contacto, vehículo/VIN, artículos, monto, estado de WhatsApp, cajera asignada, referencia ERP y controles para avanzar. Los cambios se guardan en PostgreSQL; no son movimientos visuales únicamente en memoria.

## Publicidad y enlaces medibles

En `/tallerv1/publicida` el personal puede crear una campaña con título, texto, audiencia, vigencia y precio, cargar JPG, PNG, WebP, MP4 o WebM hasta 25 MB y publicarla. Al publicar se entrega una ruta única `/c/{slug}`. Cada visita registra un evento `MARKETING/CAMPAIGN_CLICK` y redirige a la landing con el identificador de campaña, permitiendo mostrar el total de clics.

El uso de imagen o video no publica automáticamente en Meta. Esa integración exige una cuenta Business, permisos, consentimiento y credenciales reales del propietario.

## Decisiones de seguridad y datos

- Portal y documentos del cliente exigen sesión firmada; una cotización solo puede leerse si pertenece a ese cliente.
- Operaciones, caja y publicidad exigen acceso del personal.
- Contraseñas modificadas desde el portal se guardan con PBKDF2, sal aleatoria y 310 000 iteraciones.
- Las campañas usan tipos MIME permitidos, límite de tamaño y nombres calculados; no se acepta HTML ejecutable.
- Las imágenes se abren y verifican con Pillow; MP4 y WebM deben tener la firma binaria del formato. Cambiar solo el MIME no permite guardar un archivo falso.
- La persistencia JSON de campañas trabaja sobre copias nuevas para que SQLAlchemy detecte cada publicación y archivo. Una prueba automatizada detectó y evitó una pérdida silenciosa de estado.
- Los efectos visuales son moderados, respetan `prefers-reduced-motion` y el portal incluye adaptación al modo oscuro del sistema.

## Pruebas locales antes del VPS

- Platform API: **55 aprobadas**. Incluyen sesión de cliente, vehículo persistido, cotización HTML/PDF, documentos de caja, campaña con archivo, publicación y conteo de clic.
- Contratos generales del repositorio: **52 aprobados**.
- Portal público: **5 aprobadas** y build Vite de producción aprobado.
- Operaciones: **12 aprobadas** y build Vite de producción aprobado.

Las pruebas no sustituyen la verificación servida. La evidencia de contenedores, rutas y recorridos en navegador se agrega al documento de validación al terminar el despliegue.

## Evidencia servida

- Login de cliente real, panel con 3 vehículos, 2 alertas, 1 cotización y 1 factura.
- Cotización servida como HTML (2 764 bytes) y PDF real (3 245 bytes), ambas HTTP 200.
- Navegador: las siete secciones del portal renderizaron por separado; Mi vehículo mostró imagen, aceite, historial y consejos; Alertas mostró aprobaciones; Cotizaciones mostró decisiones y botones HTML/PDF; Configuración mostró datos, MFA, crédito y lealtad.
- Caja mostró Kanban de validación, detalle de cobro, factura, garantía, pase de salida, arqueo y cierre.
- Pedidos mostró las ocho columnas y una tarjeta abrió contacto, artículos y todos los estados persistibles.
- Kanban principal abrió `OT-DEMO-001`; dentro funcionaron Resumen, Repuestos, Historial y Manuales.
- Se corrigió durante QA el filtro del catálogo interno: una OT de Ford Escape muestra `ESC-FIL-2020` y excluye `F150-FIL-2020` y `CIV-FIL-2008`.
- Campaña `Validacion portal 20260813 2249` creada con PNG real, publicada y accesible por una ruta única. La ruta devolvió 302 y el contador pasó a 1 clic.
- Consola del portal cliente y de operaciones: sin errores.
- Backup previo: `/opt/smartdiag504-demo/backups/20260813T223600Z-pre-client-commerce-deploy`, checksums aprobados y restauración aislada de 30 tablas; la base temporal fue eliminada.

## Límites explícitos

- MFA se configura como preferencia funcional; el segundo factor real requiere proveedor/canal de entrega y recuperación.
- Crédito queda como solicitud y estado revisable; no ejecuta evaluación financiera automática.
- Lealtad se muestra cuando está habilitada, pero las reglas de acumulación/canje deben ser aprobadas por el dueño.
- POS bancario, fiscalización SAR, Meta/WhatsApp, correo corporativo y redundancia física entre dos VPS siguen dependiendo de proveedores y credenciales externas.
