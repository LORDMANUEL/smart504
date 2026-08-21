# Validación servida de marca, formatos y empaquetado

Fecha: 2026-08-17. Ambiente: VPS de pruebas `taller.nexusmedi.org`. No se crearon máquinas virtuales ni copias completas del stack. Las compilaciones y pruebas se ejecutaron en contenedores del VPS.

## Resultado

- API: **87/87 pruebas aprobadas**; después del endurecimiento de privacidad pública, **2/2 pruebas específicas de marca** volvieron a pasar.
- Operaciones React: **18/18 pruebas aprobadas**.
- Web pública React: **5/5 pruebas aprobadas**.
- Builds productivos: API, operaciones y web pública aprobados.
- Playwright servido: **37/37 comprobaciones aprobadas**, sin overlays ni errores de consola.
- Vista previa documental real: nombre, `#ED111C` y logo `data:image/png;base64` presentes.
- Artefacto Debian: instalación segura validada y contenido nuevo comprobado.

## Superficies servidas comprobadas

El recorrido autenticado confirmó módulo activo y contenido no vacío en:

- Kanban, bahías, técnico, citas, pedidos web y catálogo;
- cotizaciones, mostrador, caja y bodega;
- compras/importación, RRHH/nómina y usados;
- procesos/calidad, mapa de flujos, CRM y gerencia;
- contador, publicidad, Hub Social y administración;
- personal, documentos, tutoriales, configuración y sistema;
- pestañas de proveedores, órdenes/recepción e importaciones;
- pantalla TV, landing, tienda, acceso y login de cliente.

Esto demuestra que las rutas servidas cargan el módulo esperado y no quedan en blanco. No sustituye la prueba de cada combinación fiscal, dispositivo físico o proveedor externo.

## Marca aplicada

- API pública: `/api/v1/branding`.
- Logo activo: `/media/branding/SMARTDIAG504/logo-bc4be7bb9370a5feba04.png`.
- El mismo activo fue confirmado en administración y landing mediante navegador servido.
- Logo claro, logo oscuro y favicon fueron cargados mediante el endpoint administrador.
- El perfil final quedó con nombre `SmartDiag504`, colores `#ED111C` y `#C3000B` y sitio `https://taller.nexusmedi.org`.

## Documentos

La API servida generó una vista previa `LETTER` con:

- `company.name` resuelto;
- `company.primary_color` resuelto dentro del CSS;
- `company.document_footer` resuelto;
- `company.logo_data_uri` embebido, sin acceso de red del motor PDF.

Los formatos mantienen borrador, versión publicada, alcance por sucursal, exportación e historial SHA-256. Los HTML antiguos de respaldo también reciben nombre, colores, pie y logo antes de crear documentos nuevos; los históricos no se mutan.

## Imágenes desplegadas

- API: `sha256:ccfe42d5c9d5485127d4e8b51f6e490d6a6ee9d983f413dcadfb8087b29430e1`
- Operaciones: `sha256:7a1ea68120aafbff34beb2d43b72d638c1ba08511e3550d9d32e04730f367cd5`
- Web pública: `sha256:8d386daa2e871058976aea3e5b4d2f3c023ca613e45607a116f41ae5c8213663`

Los cuatro contenedores expuestos (API, operaciones, web pública y gateway) terminaron `running healthy`. `/ready` confirmó PostgreSQL, Valkey, almacenamiento, Frappe, esquema, IA y seguridad en `ok`.

## Reversión

Antes de desplegar se etiquetaron:

- `smartdiag504-demo-platform-api:rollback-branding-20260817`
- `smartdiag504-demo-ops-web:rollback-branding-20260817`
- `smartdiag504-demo-public-web:rollback-branding-20260817`

También se exportó únicamente `workshop_settings` a `/opt/smartdiag504-backups/branding-20260817/workshop_settings.sql`. No se reinició Coolify, Traefik ni ERPNext.

## Paquete Debian

- Archivo: `artifacts/debian/smartdiag504-platform_0.4.0_all.deb`
- SHA-256: se entrega en `smartdiag504-platform_0.4.0_all.deb.sha256` para evitar duplicar un valor que cambia al incorporar nueva documentación.
- Verificación: `deb-artifact-safe-ok` y checksum adjunto correcto.
- Contenido comprobado: `BrandingSettings.tsx`, servicio `branding.py` y manual multiempresa.

## Dependencias que siguen siendo externas

No se declaran certificadas en este VPS: CAI/SAR y contador, impresora/datáfono/gaveta, SMTP real, almacenamiento S3 privado y respaldo/restauración en otra infraestructura. El sistema deja configuraciones y contratos preparados, pero la aceptación requiere los proveedores y equipos reales.
