# Inventario de terceros y estrategia de licencias

> Documento técnico inicial. La distribución comercial y cualquier modificación de software copyleft debe revisarse con asesoría legal competente.

## Componentes principales

| Componente | Uso | Licencia declarada | Tratamiento SmartDiag504 |
|---|---|---|---|
| Frappe Framework v16 | framework ERP, API, permisos, jobs | MIT | dependencia base; conservar avisos |
| ERPNext v16 | inventario, compras, ventas, caja, contabilidad | GPL-3.0 | no ocultar licencia; cambios al programa sujetos a GPL |
| Beveren FSM | workflow de servicio | AGPL-3.0 | fork fijado/parcheado; publicar fuente correspondiente a usuarios de red cuando aplique |
| `smartdiag_workshop` | extensión automotriz Frappe | GPL-3.0-or-later | conservar fuente/licencia; revisar compatibilidad con Beveren AGPL |
| Garage v2.3.0 | almacenamiento S3 | AGPL-3.0 | servicio independiente; conservar fuente/avisos y cumplir AGPL |
| Valkey 8.1.x | caché, colas y streams | BSD-3-Clause | servicio Redis-compatible mantenido por comunidad abierta |
| PostgreSQL 17 | eventos/auditoría | PostgreSQL License | permitido con avisos |
| MariaDB 11.8 | base de Frappe | GPL-2.0 | servicio independiente |
| ChromaDB 1.5.9 | índice vectorial | Apache-2.0 | conservar avisos/NOTICE |
| FastAPI | APIs Python | MIT | conservar avisos |
| Pydantic | validación | MIT | conservar avisos |
| Uvicorn | servidor ASGI | BSD-3-Clause | conservar avisos |
| Caddy 2.10 | TLS/reverse proxy | Apache-2.0 | conservar avisos |
| HAProxy 3.0 | balanceo interno y healthchecks | GPL-2.0-or-later | servicio independiente; conservar avisos |
| React 19 / Vite 7 | interfaces web | MIT | conservar avisos de dependencias |
| Ollama 0.32.5 | LLM local opcional | MIT | perfil opcional; revisar licencia de cada modelo por separado |
| Fotografías Wikimedia Commons | imágenes públicas de landing | dominio público / CC0 1.0 según archivo | conservar `ATTRIBUTION.md` mientras se utilicen |
| Google Programmable Search API | descubrimiento opcional de imágenes | términos de servicio de Google | no concede derechos sobre imágenes; revisión humana obligatoria |
| Nginx 1.29 | frontends estáticos | BSD-2-Clause | conservar avisos |
| rclone 1.74.x | backup/restore S3 | MIT | herramienta efímera |
| Prometheus 3.5 | métricas | Apache-2.0 | perfil privado de observabilidad |
| Blackbox Exporter | probes | Apache-2.0 | perfil privado |
| Grafana 12.1 | dashboards | AGPL-3.0 | servicio independiente; cumplir licencia |
| TypeScript 5.8.3 | compilación frontend | Apache-2.0 | dependencia de desarrollo |
| Playwright | pruebas navegador | Apache-2.0 | dependencia de CI/desarrollo |

## Beveren y AGPL

Beveren se ejecuta como aplicación Frappe accesible por red. El fork SmartDiag debe:

1. conservar copyright/licencia;
2. mantener el repositorio del código fuente correspondiente;
3. documentar cada parche;
4. ofrecer acceso a la fuente cubierta a los usuarios que interactúan con la versión modificada cuando la AGPL lo exija;
5. no presentar Beveren como creación original de SmartDiag504.

La marca, configuración, datos, secretos, infraestructura administrada y servicios separados por APIs deben evaluarse individualmente; la separación técnica no sustituye análisis legal.

## Decisión de almacenamiento

MinIO Community no se utiliza en el Compose productivo de este repositorio. Se reemplazó por Garage/S3 y rclone. Los documentos históricos en `docs/legacy` pueden mencionar MinIO, pero no son la especificación vigente.

## Proceso obligatorio de dependencias

Antes de añadir o actualizar una dependencia:

- verificar repositorio y mantenedor oficial;
- registrar versión/tag/digest;
- revisar licencia y compatibilidad;
- revisar CVE/advisories;
- generar SBOM de imagen;
- ejecutar pruebas y restore;
- documentar migración/rollback;
- evitar `latest` en producción.

## Artefactos que deben acompañar una release

- `THIRD_PARTY.md` actualizado;
- SBOM CycloneDX/SPDX por imagen;
- avisos y textos de licencia;
- fuente/parches de componentes copyleft modificados;
- hashes de imágenes/artefactos;
- informe de vulnerabilidades y excepciones aprobadas.
