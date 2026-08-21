# Copia portable de SmartDiag504 para una nueva VPS

**Última copia verificada:** `smartdiag504-portable-20260821T211045Z.tar.zst` (`503280375` bytes).  
**SHA-256:** `f9782385dcbcb8099d20418e1b11269bb62a521755b18f5996f363e87bca8916`.

Esta versión incluye migración `0032_payroll_sod`, ERPNext, sesiones seguras, aislamiento por sucursal, protección de importación remota de imágenes, escaneo antivirus fail-closed, separación de funciones de nómina y el gate de instalación `SEED_DEMO_DATA=false`. La suma fue verificada en el VPS. Su PostgreSQL fue restaurado en una base temporal aislada: 62 tablas, revisión `0032_payroll_sod` y cero OTs sin sucursal. La base temporal fue eliminada después de la validación.

## Contenido

La entrega portable contiene:

- código fuente completo y documentación, sin `.env`, claves SSH ni contraseñas;
- Compose standalone, Coolify y scripts de instalación;
- dump PostgreSQL de los datos demo;
- medios privados/públicos del taller;
- objetos privados de Garage en `garage-objects.tar.gz`, sin credenciales del servidor origen;
- ChromaDB, modelo local Ollama y snapshot auxiliar de Valkey;
- código del stack ERP y backup nativo Frappe/MariaDB con archivos; se excluye `site_config_backup.json` para no transportar claves del VPS origen;
- plantilla de variables, inventario y manifiesto SHA-256.

No es una imagen de máquina virtual. Se instala sobre Debian 12 o Ubuntu 24.04 limpio mediante Docker Compose.

## Requisitos recomendados

- 8 vCPU, 16 GB RAM y 80 GB SSD para la plataforma completa con IA local;
- puertos 22, 80 y 443;
- DNS para landing, operaciones, API y ERPNext;
- SMTP si se quieren alertas reales;
- destino externo de backups para producción.

## Instalación limpia

1. Copiar el archivo `smartdiag504-portable-*.tar.zst` y su `.sha256` a la nueva VPS.
2. Verificar: `sha256sum -c smartdiag504-portable-*.tar.zst.sha256`.
3. Extraer: `tar --zstd -xf smartdiag504-portable-*.tar.zst`.
4. Entrar en `source/` y copiar `.env.example` a `.env`.
5. Configurar dominios, ACME, datos de empresa y correo. Mantener `ENVIRONMENT=production` y `SEED_DEMO_DATA=false`. No reutilizar secretos del VPS de prueba.
6. Ejecutar `sudo bash scripts/install-vps.sh --env-file .env --local-ai --observability`.
7. Confirmar salud con `bash scripts/smoke-test.sh .env`.

## Restauración de datos demo

Debe hacerse primero en una VPS o recurso vacío cuyo nombre empiece con `smartdiag504-restore-`.

- PostgreSQL: restaurar `data/platform/platform-demo.pgdump` después de las migraciones y antes de exponer DNS.
- Medios: extraer `platform-media.tar.gz` en el volumen `platform-media`.
- Garage: iniciar un bucket vacío con claves nuevas y reimportar `garage-objects.tar.gz`; nunca copiar `secrets/s3.env` desde el servidor origen.
- IA local: Ollama puede restaurarse desde `ollama-data.tar.gz` o volver a descargar el modelo.
- ERPNext: crear el sitio vacío, instalar ERPNext/HRMS/Beveren/`smartdiag_workshop` y usar `bench restore` con el backup de `data/erpnext/backups/`.
- Ejecutar migraciones y reconciliación ERP antes de habilitar usuarios.

Nunca restaurar esta copia sobre una empresa operativa. Los datos incluidos son de demostración y deben eliminarse antes de producción real.

## Artefactos locales verificados

- Portable: `C:\Users\sammi\OneDrive\Desktop\vps\smartdiag504\portable\smartdiag504-portable-20260821T211045Z.tar.zst`.
- Instalador: `C:\Users\sammi\OneDrive\Desktop\vps\smartdiag504\portable\smartdiag504-platform_0.4.0_all.deb`, `34036000` bytes, SHA-256 `180b501e5044028ab01f3f621722d09a3814c58ea6441e2c9a2153f095347e3b`.
- El instalador no inicia contenedores automáticamente y fue validado con `scripts/validate_deb_artifact.sh`.
- El manifiesto interno pasó completo (1,313 entradas); Garage contiene 21 objetos y los respaldos SQL/archivos de ERP superaron sus comprobaciones estructurales.

## Validaciones obligatorias

1. Todos los checksums internos deben aprobar.
2. Landing, portal, tienda, Kanban, técnico, citas, cotizaciones, mostrador, caja, bodega y ERP deben responder.
3. Ejecutar una operación cita → OT → cotización → aprobación → repuesto → calidad → factura → pago.
4. Comprobar que OT, stock, factura y pago coincidan con ERPNext.
5. Probar descarga privada de fotografías con y sin autorización.
6. Probar impresión HTML/PDF y plantilla personalizada.
7. Crear un segundo backup y restaurarlo nuevamente en un entorno vacío.

## Límites

La copia permite reproducir el entorno de pruebas. No certifica fiscalidad hondureña, POS físico, pagos, WhatsApp/Meta, SMTP, almacenamiento externo, pentest ni alta disponibilidad física.

Las copias anteriores a `20260821T211045Z` quedan revocadas. El exportador antiguo no excluía completamente la carpeta de secretos; la credencial ERP afectada fue rotada. La copia vigente pasó búsqueda de rutas `.env`/`secrets`, manifiesto interno, paquete Garage y restauración PostgreSQL.

Esta evidencia demuestra que el paquete es íntegro y restaurable. Todavía no equivale a una instalación completa en una segunda VPS: esa aceptación debe ejecutarse cuando exista el servidor destino, con secretos y DNS nuevos, siguiendo las validaciones anteriores. Para producción también siguen siendo externos la aprobación CAI/fiscal, el hardware POS y un respaldo fuera de este VPS.
