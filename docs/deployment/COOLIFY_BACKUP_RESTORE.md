# Backup y restauración de SmartDiag504 en Coolify

## Frontera

El backup de Coolify y el backup de SmartDiag504 son independientes. El primero protege la configuración de la plataforma; el segundo debe cubrir PostgreSQL, MariaDB/Frappe, sitios/archivos y objetos S3.

Objetivos iniciales de staging, pendientes de medición: RPO 24 horas y RTO 4 horas. No se publican como cumplidos hasta completar un restore drill cronometrado.

## Paquete de aplicación

Cada ejecución produce un directorio fechado con:

- dump lógico de una sola base PostgreSQL;
- backup nativo del sitio Frappe/MariaDB y archivos públicos/privados;
- export/copia versionada del bucket S3;
- metadatos de imagen y digest desplegado;
- `manifest.sha256`;
- registro de inicio, fin, tamaño y resultado.

El paquete se cifra antes de salir del servidor y se copia a un destino offsite con retención: 7 diarios, 5 semanales y 12 mensuales. La clave de cifrado no vive en el mismo destino.

## Verificación

1. `scripts/coolify/backup-verify.sh /ruta/al/paquete` verifica manifiesto y estructura sin restaurar.
2. Crear un recurso nuevo `smartdiag504-restore-YYYYMMDD` con volúmenes vacíos.
3. Confirmar explícitamente nombre de entorno y base destino.
4. Restaurar únicamente la base nombrada; nunca `--all-databases`.
5. Restaurar sitio/archivos con herramientas Frappe y objetos en un bucket nuevo.
6. Ejecutar migraciones desde el mismo digest de aplicación del backup.
7. Validar conteos, archivos, una OT, catálogo, compatibilidad y login.
8. Registrar tiempo real y eliminar el recurso temporal desde Coolify después de aprobar la evidencia.

`scripts/restore.sh` pertenece al modo standalone y está prohibido para producción Coolify.

## Doble confirmación

`restore-staging-only.sh` solo acepta un entorno cuyo nombre empiece con `smartdiag504-restore-` y exige repetir el nombre exacto. El script prepara y valida; la conexión y destino deben ser credenciales exclusivas del staging vacío. Nunca se reutilizan URLs o secretos de producción.
