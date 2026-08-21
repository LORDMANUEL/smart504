# SmartDiag504: estado del demo administrado por Coolify

Fecha de verificación: 2026-08-13. Entorno: VPS de pruebas. Dominio: `taller.nexusmedi.org`.

## Propiedad y aislamiento

- Proyecto Coolify: `SmartDiag504` (`l1318y3i6f74qs098bmngp7p`).
- Recurso Compose: `smartdiag504-demo` (`eeylxzuvyicq5i5lelcrcda9`).
- Los contenedores administrados terminan en el UUID del recurso.
- PostgreSQL, Valkey, API y frontends no publican puertos del host. Sólo `gateway` se conecta a la entrada administrada por Coolify.
- Los volúmenes externos conservados son `smartdiag504-demo_postgres-data`, `smartdiag504-demo_redis-data` y `smartdiag504-demo_platform-media`.
- No se reinició ni modificó `coolify-proxy`; tampoco se recrearon contenedores de otros proyectos.

## Rutas desplegadas

- `/lading`: página promocional limpia del taller.
- `/lading/repuestos`: tienda separada con catálogo y solicitud de pedido.
- `/lading/loginclie`: autenticación de cliente validada por el servidor.
- `/lading/cliente`: portal del cliente; redirige al login sin sesión vigente.
- `/tallerv1/login`, `/tallerv1/kanban`, `/tallerv1/caja`, `/tallerv1/bodega`, `/tallerv1/3gj`, `/tallerv1/publicida` y `/tallerv1/publicida/tv`: superficies de operación.

## Secretos requeridos

Los valores viven en el entorno del recurso de Coolify y en el archivo raíz restringido del VPS; no se guardan aquí. Variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `ADMIN_API_TOKEN`, `EVENT_HMAC_SECRET`, `CHAT_SESSION_SECRET`, `AI_GATEWAY_INTERNAL_TOKEN`, `CLIENT_DEMO_EMAIL` y `CLIENT_DEMO_PASSWORD`.

La credencial de cliente se entrega separadamente. El frontend no la contiene, muestra ni precarga. La API rechaza credenciales arbitrarias y firma una sesión temporal.

## Backup y rollback

Backup verificado: `/opt/smartdiag504-demo/backups/20260813T152423Z`. Incluye dump PostgreSQL, configuraciones, suma SHA-256 y evidencia de restauración aislada. La restauración temporal se eliminó al finalizar la prueba.

Rollback: detener el recurso `smartdiag504-demo` desde Coolify; comprobar que ningún contenedor con sufijo `eeylxzuvyicq5i5lelcrcda9` siga activo; arrancar `/opt/smartdiag504-demo/compose.demo.yaml` con su `.env`. Nunca ejecute ambos gateways a la vez ni elimine los tres volúmenes externos.

## Evidencia ejecutada

- Build TypeScript/Vite público correcto y 11 pruebas API enfocadas correctas.
- Las 11 rutas externas obligatorias respondieron HTTP 200 y validación TLS 0.
- Navegador real: landing, tienda, redirección del portal sin sesión, ausencia de contraseña visible, diseño móvil sin desbordamiento y consola sin errores.
- Login válido: HTTP 200; login arbitrario: HTTP 401.
- Recreación exclusiva de `public-web-eeylxzuvyicq5i5lelcrcda9`: conteos antes/después `13 productos | 6 OT | 1 vehículo`.
- Catálogo cliente de demostración: exactamente tres piezas para Ford Escape 2020, Ford F-150 2020 y Honda Civic 2008; los costos internos no forman parte del contrato público.

## Límites conocidos

- Es un demo de staging, no una liberación productiva. El portal usa datos cliente de demostración en el bundle; la sesión bloquea la ruta visible, pero la autorización de cada futuro endpoint de datos del cliente debe implementarse antes de datos reales.
- El taller usa por ahora un único token administrativo. La separación real de roles para técnico, caja, bodega, administrador y publicidad mediante SSO/Frappe sigue pendiente.
- Las vistas de caja, picking y publicidad demuestran el flujo visual; todavía no todas persisten sus acciones en la API. No se consideran flujos transaccionales completos.
- El catálogo público contiene 13 artículos existentes: nueve corresponden a los tres vehículos solicitados y cuatro son artículos base. El portal del cliente sí filtra exactamente tres por vehículo.
- La tienda separada quedó dentro de `taller.nexusmedi.org/lading/repuestos`; `tienda.nexusmedi.org` no se desplegó, conforme al alcance actual.
