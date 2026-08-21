# Informe aplicado de UX, QA y seguridad — SmartDiag504

Fecha de corte: 21 de agosto de 2026. Entorno validado: VPS de pruebas `taller.nexusmedi.org`.

## Resultado ejecutivo

Esta intervención corrigió hallazgos concretos en autenticación de recuperación, autorizaciones públicas, nómina, documentos PDF/HTML, comprobantes de pago, privacidad de VIN y asistente de IA. También mejoró navegación por teclado, foco visible, áreas táctiles, estados anunciados y respuesta móvil en la tienda y la operación.

El sistema continúa siendo un candidato de pruebas, no una liberación certificada de producción. La brecha de capacidad observada al inicio se corrigió con paginación y caché compartida del catálogo; la repetición de 1,000 compradores cumplió todos los umbrales. Fiscalidad, hardware y respaldo externo todavía requieren aceptación de terceros.

## Correcciones de seguridad aplicadas

- Autorizaciones de devoluciones/garantías: bloqueo de fila, una sola transición desde `PENDING`, actor honesto `public-approval-link` y formulario HTML sin JavaScript inline, compatible con CSP.
- Plantillas HTML/PDF: etiquetas y atributos por lista permitida; rechazo de `file:`, HTTP(S), `url()`, SVG y recursos externos; el render PDF bloquea resolución de archivos externos.
- Comprobantes: imágenes decodificadas y re-codificadas sin metadatos; PDF completo con `%%EOF`, rechazo de funciones activas; descarga privada con `nosniff` y `attachment`.
- Nómina: el preparador no puede revisar; revisión, aprobación y contabilización exigen actores distintos y quedan persistidos.
- Recuperación administrativa: en producción queda deshabilitada por defecto; si se habilita exige red permitida y motivo auditado. En staging conserva el flujo DEMO pendiente de reemplazo.
- VIN público: dejó de confirmar si un VIN privado está registrado. La consulta por VIN se deriva al portal autenticado; la búsqueda pública por nombre/SKU continúa.
- IA pública: filtro de salida contra fragmentos de prompt, configuración y tokens internos, además del filtro de entrada ya existente.

## Mejoras UX y accesibilidad aplicadas

- Enlaces “Saltar al contenido” y “Saltar al catálogo”.
- Foco visible consistente para enlaces, botones, campos, selectores y áreas de texto.
- Altura táctil mínima de 44 px en navegación y acciones principales.
- Alertas globales anunciadas con `role=alert` y `aria-live=assertive`.
- Mensaje útil y accionable cuando el visitante intenta consultar VIN sin iniciar sesión.
- Ajustes a 360 px: buscador VIN apilado, CTA de ancho completo, topbar compacta y contenido sin desplazamiento horizontal.
- Se respeta `prefers-reduced-motion`.

## Evidencia ejecutada en VPS

- Migración Alembic: `0031_client_credit_amount -> 0032_payroll_sod` aplicada.
- API: suite completa finalizada al 100 % sin fallos tras actualizar los controles legítimos.
- AI Gateway: `15 passed in 1.23s`.
- Límites por rol: `PASS`; técnico no escribe documentos/catálogo (403), cajero no escribe OT (403), aislamiento de sucursal confirmado.
- Flujo de taller servido: `PASS`; OT `OT-2026-000025`, ERP `SYNCED`, controles `CHECK_IN_360`, `TIMER_STOPPED`, `QUALITY_PASS`.
- Fallos ERP pendientes reportados: `[]`.
- Navegador servido en 360, 768, 1366 y 1920 px: página no vacía, H1 presente y sin overflow horizontal.
- Consola del navegador en tienda: 0 errores y 0 advertencias.
- Cabeceras servidas: CSP, HSTS, `nosniff` y `SAMEORIGIN` presentes.
- Carga después de la corrección: 1,000 compradores/100 VUs, 2,000 solicitudes, 0 errores, 3,000/3,000 comprobaciones, p95 938.22 ms y p99 1.35 s. Todos los umbrales pasaron.

## Pendientes antes de producción

1. Ejecutar E2E visual autenticado de todos los roles con credenciales de aceptación, no con el token de recuperación.
2. Configurar y certificar CAI/fiscalidad, impresora, gaveta, lector y datáfono con contador/proveedor.
3. Configurar SMTP definitivo y validar entregabilidad SPF, DKIM y DMARC.
4. Configurar respaldo externo en otra infraestructura y demostrar una restauración aislada.
5. Ejecutar escáner de malware para PDFs en producción; la validación estructural actual reduce riesgo, pero no sustituye antivirus/CDR.
6. Realizar auditoría WCAG automatizada con axe sobre sesiones autenticadas y corregir cualquier contraste o nombre accesible residual.

## Regla de liberación

No marcar “producción” mientras alguno de los seis puntos anteriores permanezca abierto. Un HTTP 200 o contenedor saludable no sustituye prueba de flujo, autorización, conciliación ERP, restauración ni capacidad.
