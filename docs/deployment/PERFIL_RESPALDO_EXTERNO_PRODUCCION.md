# Perfil de respaldo externo para producción

Este documento es configuración futura. Está prohibido habilitar el cron, credenciales o destino externo en el VPS actual de pruebas.

## Diseño

- PostgreSQL: `pg_dump` diario cifrado.
- ERPNext/MariaDB y archivos: `bench backup --with-files --compress` diario.
- Medios privados: replicación incremental del bucket S3 compatible.
- Destino: cuenta/proyecto externo con Object Lock o retención inmutable.
- Retención propuesta: 7 diarios, 5 semanales, 12 mensuales.
- Cifrado: clave administrada fuera del VPS; nunca escrita en el repo.
- Verificación: checksum, tamaño mínimo, fecha y alerta por atraso.
- Restauración: mensual en entorno aislado, evidencia de conteos y eliminación segura del entorno temporal.

## Variables de producción

`BACKUP_ENABLED=true`, `BACKUP_DESTINATION`, `BACKUP_ENCRYPTION_KEY_ID`, `BACKUP_RETENTION_DAYS`, `BACKUP_ALERT_CHANNEL` y credenciales de mínimo privilegio se inyectan desde el gestor de secretos de producción.

## Criterio de aceptación

Un archivo subido no basta. El respaldo sólo se considera válido después de restaurar PostgreSQL, restaurar el sitio Frappe, verificar documentos/adjuntos y registrar tiempo real de recuperación. El procedimiento no reinicia Coolify ni el proxy compartido.

