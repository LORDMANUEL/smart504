# Validación servida: compras, RRHH, formatos e instalador Debian

Fecha: 17 de agosto de 2026. Entorno: VPS de pruebas `taller.nexusmedi.org` y ERPNext `erp.nexusmedi.org`.

Esta evidencia corresponde al sistema publicado. No es una certificación fiscal ni una autorización para producción.

## Resultado funcional

El flujo servido `scripts/validate_enterprise_served.sh` terminó sin error y comprobó:

| Flujo | Resultado SmartDiag | Conciliación ERP |
|---|---|---|
| Proveedor | activo | `SYNCED` |
| Orden de compra con recepción parcial y final | `RECEIVED` | `SYNCED` |
| Expediente de importación y distribución de costos | `ALLOCATED` | `SYNCED` |
| Contrato y horario | vigente | `SYNCED` |
| Horas extra | `APPROVED` | incluidas únicamente después de aprobación |
| Nómina con ajuste de comisión | `APPROVED` | `SYNCED` |
| Formato HTML/CSS cargado y exportado | versión `v1` | hash y versión conservados |

El reporte `scripts/report_erp_failures.sh` devolvió `[]`: no quedaron comandos ERP fallidos al cierre. Alembic reportó `0024_procurement_hr_operations (head)`.

## Prueba visual servida

Chromium abrió la aplicación publicada con sesión administrativa y validó estas superficies:

- `/tallerv1/compras`, incluyendo las pestañas **Proveedores**, **Órdenes y recepción** e **Importaciones**.
- `/tallerv1/rrhh`.
- `/tallerv1/documentos` con carga o reemplazo de HTML/CSS.
- `/tallerv1/tecnico`.
- `/tallerv1/guias`.
- `/tallerv1/usados` y `/tallerv1/social`.
- `/tallerv1/publicida/tv`.

Las once comprobaciones devolvieron contenido útil, cero overlays de error y cero errores de consola. Las capturas quedaron en `/opt/smartdiag504-demo/evidence/enterprise-20260817` dentro del VPS de pruebas.

## Gates de código ejecutados en el VPS

- Suite completa de API: aprobada.
- Compilación de producción de `ops-web`: aprobada, 1,610 módulos transformados.
- Compilación sintáctica del adaptador Frappe de compras/importación: aprobada.
- Migración PostgreSQL `0024`: aplicada.
- Migración Frappe del sitio ERP: aplicada.

No se ejecutó Python, Node, una compilación ni una migración en la computadora local.

## Paquete Debian

- Artefacto: `artifacts/debian/smartdiag504-platform_0.4.0_all.deb`.
- Tamaño y huella: registrados en el artefacto y su archivo `.sha256`; deben comprobarse antes de instalar.
- Arquitectura: `all`.
- Dependencias: certificados, `curl`, Docker y Docker Compose.
- Verificación SHA-256: aprobada.
- Validación por extracción: aprobada.
- El `postinst` crea directorios/configuración, pero no inicia servicios, no abre puertos y no altera Coolify o Traefik.

El paquete se construyó y se extrajo en un contenedor desechable del VPS. No fue instalado sobre el host de pruebas.

## Límites pendientes antes de producción

- Certificación fiscal SAR/CAI y prueba con impresora, gaveta, lector y datáfono reales.
- Proveedor real de correo/WhatsApp/SMS y consentimiento de comunicaciones.
- Almacenamiento privado de evidencias con antivirus y política de retención.
- Respaldo externo cifrado y restauración en infraestructura distinta al VPS de pruebas.
- Pruebas negativas multiempresa y conciliación contable de cierre con el contador.
