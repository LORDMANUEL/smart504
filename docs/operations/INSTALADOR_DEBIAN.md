# Instalador Debian de SmartDiag504

## Alcance

El paquete `smartdiag504-platform` instala el código versionado, un archivo de configuración de ejemplo y el comando `smartdiag504`. No inicia contenedores, no abre puertos, no modifica Traefik/Coolify y no elimina datos al desinstalarse.

## Construcción

La construcción se realiza en Linux con `scripts/build-deb.sh`. En este proyecto se valida dentro de un contenedor del VPS de pruebas, nunca con Python ni máquinas virtuales en la PC local.

## Instalación en un servidor nuevo

```bash
sudo apt install ./smartdiag504-platform_0.4.0_all.deb
sudo editor /etc/smartdiag504/platform.env
sudo smartdiag504 validate
sudo smartdiag504 deploy
```

`validate` rechaza secretos con el marcador `__GENERATE__`. `deploy` es la única acción que construye e inicia contenedores, y requiere root explícitamente.

## Actualización y reversión

Antes de actualizar deben respaldarse PostgreSQL, MariaDB/ERPNext y objetos privados. Instalar una versión anterior restaura el código, pero no revierte migraciones ni datos. La reversión de datos exige el runbook de restauración y una prueba aislada.

## Relación con Coolify

El instalador es para servidores Debian independientes. En el VPS de prueba administrado por Coolify sólo se construye y extrae en un contenedor desechable para verificar su contenido; no se instala sobre el host ni controla el proyecto activo.
