# ERPNext y Frappe HR para SmartDiag504

Este stack separado proporciona la fuente canónica de contabilidad, compras, inventario valorizado, POS, activos, empleados, asistencia y planilla. El API de SmartDiag504 conserva flujos, proyecciones y referencias, pero no sustituye el libro mayor ni el Stock Ledger.

## Aplicaciones

- Frappe/ERPNext `version-16`.
- Frappe HRMS `version-16`, incorporado en la imagen durante el build; no se instala manualmente dentro de un contenedor efímero.
- MariaDB y Redis en volúmenes exclusivos del proyecto `smartdiag504-erp`.

## Acceso

- Sitio: `https://erp.nexusmedi.org`.
- La contraseña administrativa y la contraseña de MariaDB se generan durante el despliegue y se guardan únicamente en `/opt/smartdiag504-erpnext/.env` con permisos `600`.
- La integración debe utilizar un usuario API de mínimo privilegio; nunca la cuenta `Administrator`.

## Despliegue

1. Clonar el repositorio oficial `frappe/frappe_docker` en `/opt/smartdiag504-erpnext/frappe_docker`.
2. Construir `smartdiag504-erpnext-hrms:16` usando `apps.json` como secreto BuildKit.
3. Generar el Compose desde `compose.yaml`, los overrides oficiales de MariaDB y Redis, y `compose.coolify.override.yml`.
4. Crear el sitio `erp.nexusmedi.org` e instalar `erpnext` y `hrms`.
5. Completar el asistente de empresa, moneda, plan contable e impuestos con el contador responsable.

## Recuperación

Los volúmenes ERP son independientes de SmartDiag504. Antes de actualizar se ejecuta `bench --site erp.nexusmedi.org backup --with-files`, se conserva la imagen anterior y se prueba restauración en un sitio temporal. No se eliminan volúmenes durante un rollback.

## Límite legal

Tener ERPNext operativo no certifica por sí mismo facturas SAR, CAI, rangos, impuestos, planilla ni libros legales de Honduras. Esos datos requieren configuración y aceptación del contador, responsable de RRHH y propietario.
