# Versionado, actualización y reversión

SmartDiag504 usa versionado semántico `MAJOR.MINOR.PATCH`: `PATCH` corrige,
`MINOR` agrega funciones compatibles y `MAJOR` introduce cambios que requieren
migración o capacitación. Producción debe usar una etiqueta estable, nunca una
rama de trabajo. `.env` y los volúmenes de Docker no forman parte de Git.

## Actualizar

1. Confirme un respaldo válido de PostgreSQL, MariaDB/Frappe y almacenamiento.
2. Compruebe que el árbol Git no tenga cambios locales.
3. Ejecute:

```bash
cd /ruta/smart504
sudo bash scripts/update-smartdiag.sh v1.1.0
```

El script respalda `.env`, descarga la etiqueta, exige un avance seguro y vuelve
a ejecutar el instalador idempotente.

## Revertir

Revertir código no revierte automáticamente el esquema de datos:

```bash
cd /ruta/smart504
git checkout v1.0.0
sudo bash scripts/install-vps.sh --env-file .env --observability --local-ai
```

Si hubo migraciones incompatibles, restaure el respaldo en un entorno aislado,
valide conteos y conciliación, y sólo entonces cambie producción. Consulte
`docs/deployment/VPS_RUNBOOK.md` y `docs/backup-restore-runbook.md`.

## Publicar una versión

1. Ejecute todos los gates en el VPS de pruebas.
2. Actualice changelog y manuales.
3. Cree una etiqueta anotada: `git tag -a vX.Y.Z`.
4. Publíquela: `git push origin vX.Y.Z`.
5. Instale la etiqueta en un VPS limpio y complete aceptación por roles.

No se debe llamar “producción” a una versión sin restauración probada,
conciliación ERP, aceptación por roles y configuración fiscal aprobada.
