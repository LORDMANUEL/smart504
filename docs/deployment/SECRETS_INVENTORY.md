# Inventario de secretos — nombres, no valores

| Variable | Consumidor | Rotación/nota |
|---|---|---|
| `POSTGRES_PASSWORD` | Platform API/PostgreSQL | distinta de otros proyectos |
| `REDIS_PASSWORD` | API/Frappe/Valkey | distinta de otros proyectos |
| `MARIADB_ROOT_PASSWORD` | inicialización Frappe | no usar en runtime normal |
| `ERP_ADMIN_PASSWORD` | administrador inicial staging | rotar tras primera entrada |
| `FRAPPE_API_KEY` / `FRAPPE_API_SECRET` | adaptador API | usuario mínimo privilegio |
| `ADMIN_API_TOKEN` | legado temporal | debe desaparecer al terminar OIDC/RBAC |
| `EVENT_HMAC_SECRET` | eventos | rotación coordinada |
| `CHAT_SESSION_SECRET` | sesiones chat | AI está deshabilitada en el staging inicial |
| `AI_GATEWAY_INTERNAL_TOKEN` | API/AI | reservado; AI privado |
| `S3_ACCESS_KEY_ID` / `S3_SECRET_ACCESS_KEY` | objetos | bucket exclusivo de staging |
| credencial registry | Coolify | lectura, repositorio privado |
| clave cifrado backup | backup runner | fuera de Git y del paquete |

Coolify guarda los valores. Este repositorio solo conserva nombres y requisitos.
