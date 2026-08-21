# SmartDiag504 — runbook de staging en Coolify

Fecha de verificación: 2026-08-13. Alcance: taller y demo en `taller.nexusmedi.org`. La tienda queda fuera de este despliegue.

## Estado observado

- VPS autorizada: `vmi3350998` (`13.140.138.152`).
- Coolify `4.1.2` y `coolify-proxy`/Traefik están activos y son infraestructura compartida.
- No había contenedores SmartDiag504 ni carpetas SmartDiag bajo `/opt` o `/data` durante la auditoría de solo lectura.
- `taller.nexusmedi.org` y `tienda.nexusmedi.org` resolvían mediante Cloudflare y devolvían HTTP 503; no existía backend alcanzable.
- El servidor tenía 102 GB libres y aproximadamente 7.5 GiB de RAM disponible, sin swap.

Estos datos son una fotografía del corte; deben repetirse antes de desplegar.

## Arquitectura del recurso

El recurso nuevo se llama `smartdiag504-staging`. `compose.coolify.yaml`:

- no contiene Caddy;
- no publica puertos del host;
- no declara redes personalizadas;
- no construye imágenes en la VPS;
- usa imágenes fijadas por digest;
- mantiene PostgreSQL/MariaDB/Valkey privados;
- expone a Coolify solamente HAProxy (8080/8081/8082) y Frappe (8080);
- marca migraciones e inicializadores como jobs excluidos del health global de Coolify.

## Gates antes de crear el recurso

1. Rama `fix/coolify-production-hardening` revisada y limpia.
2. CI verde para Python, frontend, Compose, SBOM y análisis de imágenes.
3. Imágenes publicadas en un registry privado, por Git SHA y digest. La imagen Frappe no se construye en la VPS.
4. Vulnerabilidades críticas resueltas o aceptadas por escrito. No usar `npm audit fix --force` sin revisar el cambio mayor.
5. Restore probado en un staging vacío.
6. Ningún secreto guardado en Git, Compose o documentación.

## Creación manual en Coolify

No ejecutar `docker compose up` por SSH.

1. En Coolify, crear proyecto `SmartDiag504` y entorno `staging`.
2. Crear un recurso nuevo desde el repositorio privado y seleccionar la rama aprobada.
3. Build pack: Docker Compose. Archivo: `/compose.coolify.yaml`.
4. Nombre del recurso: `smartdiag504-staging`. No reutilizar ningún recurso, volumen o base existente.
5. Registrar todas las variables del inventario de secretos. Marcar como secretas las credenciales y tokens.
6. Configurar dominios en el recurso:

   | Dominio | Servicio | Puerto | Uso |
   |---|---|---:|---|
   | `taller.nexusmedi.org` | `haproxy` | 8081 | Operación del taller |
   | `taller.nexusmedi.org/api` | `haproxy` | 8082 | API, con PathPrefix `/api` |
   | `taller.nexusmedi.org/erp` | `frappe-frontend` | 8080 | ERP/Frappe, acceso administrativo |

   Si Coolify no elimina el prefijo de `/api` o `/erp`, usar subdominios separados antes de desplegar; no editar Traefik global.
7. Confirmar que Coolify creará volúmenes nuevos con el UUID del recurso.
8. Hacer el primer despliegue desde imágenes ya publicadas. No habilitar `tienda.nexusmedi.org` ni AI.
9. Observar jobs `frappe-configurator`, `frappe-site-init` y `platform-migrate`: deben terminar con código 0.
10. Ejecutar `scripts/coolify/post-deploy-smoke.sh https://taller.nexusmedi.org` desde un runner externo.

## Validación funcional obligatoria

- `/live`, `/startup` y `/ready` responden según su contrato.
- Login individual/RBAC (cuando esté implementado), no token compartido.
- Crear vehículo y Service Order Beveren; comprobar que no se crea una OT paralela.
- Descargar plantilla Excel, cargar una muestra, revisar errores y confirmar.
- Elegir el vehículo de la muestra y comprobar que solo aparecen sus manos de obra y repuestos.
- Recorrer los seis estados oficiales y verificar factura ERPNext.
- Probar Kanban; bahías sigue siendo opcional.
- Probar respaldo y restauración en otro staging vacío.

Un HTTP 200 o un contenedor healthy no certifica estos flujos.

## Rollback

1. Detener la promoción y conservar evidencia/logs.
2. En Coolify, redeploy del digest anterior aprobado. No reconstruir con el mismo tag.
3. Si la migración es compatible hacia atrás, validar `/ready` y flujos.
4. Si exige restauración de datos, crear otro recurso staging vacío y restaurar allí; nunca ejecutar `restore.sh` sobre el recurso afectado.
5. Cambiar dominio al staging restaurado solo después de QA y aprobación humana.

No reiniciar `coolify-proxy`, Docker ni ningún servicio ajeno.
