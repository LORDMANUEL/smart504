# Almacenamiento privado S3 — Garage

**Entorno:** VPS de pruebas SmartDiag504  
**Fecha:** 21 de agosto de 2026

## Diseño aplicado

- Garage `v2.3.0` corre como contenedor interno sin puertos publicados al host.
- El bucket privado es `smartdiag-evidence` y usa tres volúmenes independientes: configuración, metadatos y objetos.
- Las credenciales se generan en el VPS, con permisos `0600`, en `secrets/s3.env`; no se guardan en Git, documentación ni frontend.
- Logo, publicidad e imágenes públicas del catálogo continúan en `/media`. Sólo las evidencias privadas de OTs usan S3.
- La clave del objeto incluye empresa y OT: `evidence/{organización}/{ot}/{archivo}`.
- El navegador nunca recibe credenciales S3 ni una URL pública. Descarga siempre por el endpoint autenticado de la OT, que vuelve a validar empresa, sucursal y permisos.
- Evidencias locales anteriores siguen disponibles; las nuevas registran `storage_backend=s3`.

## Validación ejecutada

1. Garage saludable y sin puertos publicados.
2. CRUD interno S3 `HEAD → PUT → GET → DELETE`: aprobado.
3. Carga servida desde una OT real: aprobada.
4. Descarga sin autenticación: HTTP `401`.
5. Descarga autorizada: HTTP `200` y `Cache-Control: private, no-store`.
6. Objeto confirmado dentro de `evidence/` en el bucket privado.
7. Reinicio aislado del contenedor y nueva lectura del mismo objeto: aprobada.
8. Lectura de evidencia histórica del volumen local: HTTP `200`.
9. `/ready`: `object_storage=ok`.
10. Suite API completa en el VPS: aprobada.

## Operación y recuperación

- Arranque: usar el Compose de Coolify junto con `infra/coolify/runtime-upgrade.override.yaml`.
- No exponer los puertos 3900, 3901 ni 3903 a Internet.
- El respaldo local debe incluir `smartdiag504-demo_garage-config`, `smartdiag504-demo_garage-meta` y `smartdiag504-demo_garage-data` de forma consistente.
- Restaurar siempre en una instancia vacía, comprobar el bucket y después habilitar la API.

## Límite deliberado

Garage protege y separa los objetos, pero está en el mismo VPS. Si se pierde el servidor completo, se pierden aplicación y copia local simultáneamente. Para producción real sigue siendo obligatorio replicar respaldos cifrados a otra infraestructura y probar su restauración periódicamente.
