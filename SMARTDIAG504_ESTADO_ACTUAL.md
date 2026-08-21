# SmartDiag504 — estado actual verificable

**Corte:** 2026-08-13  
**Rama:** `fix/coolify-production-hardening`  
**Alcance:** taller/staging en `taller.nexusmedi.org`; tienda no desplegada.

## Validado

- VPS y Coolify auditados por SSH en modo lectura; no existía despliegue SmartDiag504.
- DNS de taller y tienda existe vía Cloudflare; ambos devolvían 503 al corte.
- `compose.coolify.yaml` no contiene Caddy, puertos host, redes custom ni builds en VPS.
- El validador estándar, después de retirar únicamente la clave especial `exclude_from_hc` que Coolify procesa, pasa `docker compose config --quiet`.
- Error Frappe `WorkOrderState/can_transition` eliminado y los seis estados oficiales unificados.
- Plantilla XLSX generada desde Configuración con hojas de instrucciones, mano de obra y repuestos.
- Validación por fila/columna, vista previa y confirmación separadas.
- Compatibilidad por marca, modelo, rango de año y motor.
- Aplicación confirmada escribe Item, Item Price, Labor Operation y Vehicle Fitment en ERPNext/Frappe.
- Pruebas focalizadas: 15 verdes para health, Excel, API, Frappe y Compose; prueba de UI específica verde; build de `ops-web` verde.

## Parcial

- La consulta Frappe `compatible_catalog` filtra datos; falta conectarla al formulario real de Service Order/OT y certificarla dentro de un sitio Frappe ejecutándose.
- El endpoint de aplicación exige ERPNext real y no se ha ejecutado contra staging.
- `/ready` comprueba DB, Valkey, storage, Frappe, schema opcional y AI si se habilita, pero aún no hay evidencia dentro de contenedores reales.
- El Compose Coolify está diseñado y validado estáticamente; no se ha creado el recurso.

## Bloqueos antes de staging

- Identidad individual/OIDC, RBAC y MFA no están implementados; el token maestro legado sigue presente.
- La segunda OT en PostgreSQL no está eliminada completamente.
- Catálogo local transaccional/precios/stock todavía existe en código legado.
- S3 seguro (URL firmada, EXIF, cuarentena y SSRF) está pendiente.
- Build CI de todas las imágenes, SBOM, scan y firma no se ejecutaron.
- `npm audit` reportó 1 vulnerabilidad alta y 1 crítica en `ops-web`.
- Suite completa de `ops-web`: tres fallos antiguos por selectores ambiguos; la prueba nueva de importación pasa.
- No existe certificación Frappe/Beveren real, restore drill ni QA funcional de navegador contra contenedores.

## Gates

| Gate | Resultado |
|---|---|
| Repositorio focalizado | Parcial, pruebas nuevas verdes |
| Compose Coolify | Estático aprobado; runtime pendiente |
| Imágenes/registry/SBOM/firma | Pendiente |
| Coolify staging | No creado |
| Flujo funcional taller | Pendiente en runtime |
| Backup/restore | Runbook/guards creados; drill pendiente |

No se debe desplegar producción ni afirmar que la plataforma está lista. El siguiente paso seguro es resolver los bloqueos P0, construir imágenes en CI y recién entonces crear `smartdiag504-staging` en Coolify con aprobación humana.
