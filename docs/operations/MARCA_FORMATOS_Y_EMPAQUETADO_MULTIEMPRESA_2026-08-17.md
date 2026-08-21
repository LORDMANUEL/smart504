# Marca, formatos y empaquetado por empresa

Este documento describe la implementación operativa de personalización de SmartDiag504. El VPS actual es de pruebas; fiscalidad, hardware y respaldo externo se certifican únicamente en el ambiente productivo correspondiente.

## Centro de marca

Ruta: `https://taller.nexusmedi.org/tallerv1/configuracion`

En **Marca de la empresa**, un propietario o administrador puede configurar:

- nombre visible y razón social;
- RTN, dirección, teléfono, correo y sitio web;
- color principal, acento, superficie y texto;
- pie legal u operativo de los documentos;
- logo para fondo claro, logo para fondo oscuro y favicon.

Los archivos admitidos son PNG, JPG y WebP, hasta 4 MB y entre 32 y 6000 píxeles por lado. El servidor valida el contenido real de la imagen; no acepta SVG ni scripts. Cada sustitución se conserva en `asset_history` con actor, fecha y URL, y genera el evento auditado `SETTINGS.BRAND_ASSET_REPLACED`.

La configuración se guarda bajo la clave de la organización autenticada. La landing pública usa por ahora la organización asociada al dominio de pruebas. En un despliegue multiempresa, cada dominio se resuelve a una organización antes de responder `/api/v1/branding`; no se debe compartir una marca global entre clientes.

## Dónde se aplica

- landing, tienda y pie de contacto;
- logo de navegación y favicon;
- panel operativo y nombre visible en la conexión;
- pantalla TV de publicidad;
- vista previa y documentos HTML/PDF;
- colores CSS mediante variables de marca.

El frontend carga la marca una vez, conserva la promesa en memoria y muestra una marca de respaldo mientras responde la API. Guardar desde administración actualiza la interfaz sin recargar toda la aplicación.

## Centro único de documentos

Ruta: `https://taller.nexusmedi.org/tallerv1/documentos`

Tipos disponibles: cotización, factura, diagnóstico, OT, garantía, pase de salida, picking, entrega, devolución y recepción de bodega. El flujo correcto es:

1. Crear una plantilla para toda la empresa o para una sucursal.
2. Editar HTML/CSS o subir un HTML UTF-8 con CSS opcional.
3. Generar vista previa con los datos y marca actuales.
4. Guardar una nueva versión con nota de cambio.
5. Publicar explícitamente la versión aprobada.
6. Descargar el respaldo de la plantilla.

Reemplazar no sobrescribe documentos emitidos. Cada render conserva el HTML final, la versión y una huella SHA-256. Las plantillas bloquean scripts, eventos, formularios, iframes y recursos HTTP externos.

### Variables de empresa

- `{{ company.name }}` y `{{ company.legal_name }}`
- `{{ company.tax_id }}`, `{{ company.address }}`, `{{ company.phone }}`
- `{{ company.email }}` y `{{ company.website }}`
- `{{ company.logo_url }}` para HTML servido
- `{{ company.logo_data_uri }}` para PDF sin dependencia de red
- `{{ company.primary_color }}` y `{{ company.accent_color }}` en HTML o CSS
- `{{ company.document_footer }}`

El logo subido a almacenamiento local se transforma en `data URI` sólo durante el render del documento. En producción, los originales deben residir en almacenamiento privado compatible con S3 y políticas de respaldo.

## Fiscalidad e impresión

La apariencia de una factura no autoriza su uso fiscal. En **Contador** se define por sucursal si ERPNext emite el número fiscal o si se usa hoja preimpresa con rango CAI. El contador debe aprobar RTN, CAI, vigencia, impuestos, correlativos y notas de crédito.

Para térmica se elige `THERMAL_80` o `THERMAL_58`; para impresora normal, `LETTER` o `A4`. La certificación final debe hacerse con la impresora, gaveta y datáfono reales. El sistema no afirma compatibilidad fiscal sólo porque el navegador genere un PDF.

## Empaquetado Debian

El artefacto `smartdiag504-platform_0.4.0_all.deb` incluye fuente versionada, Compose, infraestructura, scripts, contratos y manuales. Instalar el paquete no inicia contenedores ni modifica Coolify automáticamente. El operador debe:

1. instalar el `.deb` y verificar su SHA-256;
2. copiar y completar el archivo de entorno fuera del paquete;
3. configurar secretos, dominios, volúmenes y red administrada;
4. ejecutar `smartdiag504 preflight`;
5. desplegar por etapas y conservar etiquetas de imágenes para reversión;
6. validar migraciones, salud, flujos servidos y conciliación ERP.

El paquete es un controlador reproducible, no una máquina virtual ni una copia de datos. PostgreSQL, ERPNext, archivos privados y respaldos permanecen fuera del `.deb`.

## Criterios de aceptación

- un cambio de nombre/color aparece en landing y operaciones sin recompilar;
- logo y favicon subidos responden desde `/media` y se ven en la UI;
- la vista previa contiene nombre, colores, pie y logo embebido;
- una plantilla publicada rige documentos nuevos y no altera históricos;
- cada URL profunda abre su módulo, no una página en blanco ni el Kanban equivocado;
- pruebas API, builds frontend y prueba Playwright servida finalizan sin errores de consola;
- el `.deb` reconstruido contiene esta versión y pasa validación de instalación segura.

## Límites antes de producción

Siguen requiriendo validación externa: aprobación fiscal del contador, dispositivos POS reales, SMTP real, almacenamiento privado S3, respaldo externo y restauración en otra infraestructura. Estas dependencias no deben simularse como certificadas en el VPS de pruebas.
