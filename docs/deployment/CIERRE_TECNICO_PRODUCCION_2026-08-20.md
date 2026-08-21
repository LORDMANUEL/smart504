# SmartDiag504 — cierre técnico y salida a producción

**Corte:** 20 de agosto de 2026.  
**Entorno validado:** `taller.nexusmedi.org`, VPS aislada de pruebas.  
**Dictamen actual:** `NO AUTORIZADO PARA PRODUCCIÓN` hasta cerrar los controles externos visibles en Configuración.

## Cambios cerrados en este corte

- ERPNext volvió a ser obligatorio en el runtime efectivo; `/ready` interno informa `frappe: ok` y verificación fiscal estricta.
- La migración `0027_labor_catalog` reemplaza la lista de mano de obra en memoria por catálogo persistente y aislado por empresa.
- El técnico sólo selecciona servicios activos; descripción, duración y precio vienen del catálogo. El costo interno no se expone.
- El catálogo admite reglas por marca, modelo y rango de año, y puede filtrarse por vehículo.
- Empresa, OT y técnico se validan antes de registrar mano de obra.
- El código de caja dejó de estar escrito en Compose y se inyecta desde secretos de Coolify.
- La numeración automática de empleados evita colisiones entre usuarios y contratos de RRHH.
- OTs, clientes, vehículos, caja, mostrador, cotizaciones, bodegas, calidad, CRM y documentos aplican alcance explícito por organización además del filtro ORM global.
- La prueba negativa multiempresa permite el mismo VIN y número de OT en dos empresas, conserva cajas independientes e impide lecturas cruzadas.
- Los workers de ERP y notificaciones seleccionan la cola global de forma controlada, procesan cada registro bajo la organización propietaria y restauran la identidad al finalizar; no conservan el tenant del último trabajo.
- Configuración muestra un tablero protegido de preparación para producción con responsables y estados verificables.
- Recuperación de contraseña del personal ahora genera una entrega SMTP auditable, ofrece pantalla para consumir el enlace temporal y mantiene respuesta indistinguible para correos inexistentes.
- El sondeo de sesión cerrada responde `204`, evitando errores de consola esperados en la pantalla de acceso.
- El gateway SmartDiag entrega HSTS, CSP, Permissions-Policy, protección de MIME, frame y referrer en landing, tienda, Operaciones y API.

## Evidencia ejecutada en el VPS

- respaldo PostgreSQL y archivos previos: `/opt/smartdiag504-backups/pre-labor-catalog-20260820T233304Z`;
- manifiesto SHA-256 del respaldo: aprobado;
- migración efectiva: `0027_labor_catalog`;
- catálogo activo: `SMARTDIAG504 | 5`;
- pruebas enfocadas: 11 aprobadas;
- suite API completa: 94 aprobadas;
- frontend Operaciones: 19 aprobadas; Portal público: 5 aprobadas;
- build TypeScript/Vite de Operaciones: aprobado;
- navegador servido: login individual, recorrido guiado, Configuración y tablero de preparación comprobados;
- HTTP servido: landing `200`, login de operaciones `200`;
- contenedores API, web, PostgreSQL, gateway, Valkey, IA, Chroma y trabajadores: saludables/activos.
- flujo empresarial servido posterior al cambio: proveedor `SYNCED`, compra `RECEIVED:SYNCED`, importación `ALLOCATED:SYNCED`, contrato `SYNCED`, nómina `APPROVED:SYNCED`, horas extra aprobadas y formato HTML importado/exportable.
- regresión multiempresa posterior al endurecimiento: suite API completa nuevamente aprobada con dos tenants, OTs y cajas simultáneas.
- despliegue final del worker multiempresa: suite API `92/92`, API saludable, Frappe `ok`, cola ERP `SYNCED=74`; notificaciones externas `BLOCKED=10` por ausencia deliberada de SMTP/proveedor en la VPS de pruebas.
- regresión contable de medianoche detectada y corregida: Frappe y el worker usaban zonas horarias distintas al crear compra/recepción; las nuevas órdenes usan la fecha del sitio y la recepción/costo heredan una fecha contable válida. Se reparó únicamente la orden demo afectada, sin recepciones ni asientos dependientes y con backup previo.
- repetición servida posterior: proveedor `SYNCED`, compra `RECEIVED:SYNCED`, importación `ALLOCATED:SYNCED`, nómina `APPROVED:SYNCED`; outbox ERP `SYNCED=94`, `FAILED=0`.
- navegador servido posterior a seguridad: login y recuperación renderizados, recursos permitidos por CSP y `0` errores/`0` advertencias de consola; correo inexistente devuelve `202` sin crear entrega ni revelar la cuenta.

## Copia portable actual

- VPS: `/opt/smartdiag504-portable/smartdiag504-portable-20260821T010006Z.tar.zst`;
- respaldo local: `C:\Users\sammi\OneDrive\Desktop\vps\smartdiag504\portable\smartdiag504-portable-20260821T010006Z.tar.zst`;
- tamaño: `498956936` bytes;
- SHA-256 remoto y local: `38bdfa9799fd25370fbc6b993edd6ffb9923d3c9f2e04e7e9c789b696c8f3af1`;
- contenido: fuente, PostgreSQL, medios, Chroma, Ollama, Valkey y backup Frappe/ERPNext con archivos, sin `.env`, claves ni `site_config_backup.json`.

La copia anterior queda reemplazada por:

- VPS: `/opt/smartdiag504-portable/smartdiag504-portable-20260821T013235Z.tar.zst`;
- local: `C:\Users\sammi\OneDrive\Desktop\vps\smartdiag504\portable\smartdiag504-portable-20260821T013235Z.tar.zst`;
- tamaño: `499731543` bytes;
- SHA-256 verificado en ambos extremos: `61126c1dcd5237fb193aa29b9d674a50f71c5a4bbf065095bad14ff16b494f93`.

## Tablero de salida

| Control | Estado | Responsable |
|---|---:|---|
| ERPNext obligatorio y modo fiscal estricto | Listo | Sistema |
| Empresa con sucursal activa | Listo | Administrador |
| Código de caja en secretos | Listo | Administrador |
| Plantillas publicadas | Listo | Administrador |
| CAI/rangos aceptados | Pendiente | Contador |
| SMTP transaccional | Pendiente | Proveedor/administrador |
| Evidencias en S3 privado | Listo | Infraestructura |
| Hardware fiscal/POS aceptado | Pendiente | Contador/proveedor |
| Respaldo externo y restauración fuera de la VPS | Pendiente | Infraestructura |

El mismo tablero está en **Operaciones → Configuración → Preparación para producción**. No contiene secretos.

## Acceso de demostración

- URL: `https://taller.nexusmedi.org/tallerv1/login`
- usuario: `demo.admin@smartdiag504.com`
- contraseña temporal de la VPS de pruebas: `Taller504-Personal-2026!`

Este usuario se restableció únicamente para la validación servida. Debe eliminarse antes de una salida real. Cada empleado debe usar una cuenta individual, MFA y permisos mínimos.

## Procedimiento final de autorización

1. El contador abre **Contador**, define RTN, CAI, rangos, vigencia y papel preimpreso o impresión completa; revisa factura, nota de crédito y cierre.
2. El administrador configura SMTP y prueba cita, pedido y autorización hasta que el outbox quede `SENT`.
3. Infraestructura configura un bucket S3 privado y verifica acceso autorizado/no autorizado a fotos de OT.
4. Caja prueba impresora térmica/normal, gaveta, lector y datáfono reales; el contador firma el resultado.
5. Infraestructura configura backup cifrado fuera de esta VPS y restaura en una infraestructura vacía independiente.
6. Se elimina toda cuenta demo, se exige MFA a propietarios/administradores/contador y se rotan secretos.
7. Se repite el flujo cita → OT → fotos → cotización → aprobación → bodega → calidad → factura → pago → asiento y se concilia contra ERPNext.
8. Sólo cuando el tablero indique `9/9`, gerencia firma el acta de salida.

## Seguridad pendiente

El escaneo estándar de Codex Security se creó con ID `e4633fc4-bcf4-479d-863d-baabaf84bb7a`, pero quedó pausado en preflight porque la política activa no autoriza los auditores delegados requeridos por ese proceso. No existe un informe final ni debe interpretarse como “sin hallazgos”. Debe reanudarse con la capacidad autorizada y completar además escaneo de imágenes, SBOM y pentest externo.
# Actualización 2026-08-21 — identidad real del cliente

- Se reemplazó el bearer demostrativo guardado en `sessionStorage` por FastAPI Users con cookie `HttpOnly`, `Secure` y `SameSite=Lax`.
- `client_users` enlaza obligatoriamente cuenta, organización y `Customer`; la migración aplicada es `0028_client_identity`.
- El acceso admite bloqueo temporal por intentos, recuperación de contraseña mediante el outbox SMTP y revocación inmediata por versión de sesión.
- Portal, citas, vehículos, cotizaciones y documentos resuelven el cliente por `customer_id`; se retiraron las búsquedas alternativas por correo/teléfono demo.
- Las citas validan que el vehículo pertenezca al cliente y guardan el ID verdadero del cliente.
- Las facturas del portal sólo se generan para una OT facturada perteneciente al cliente. Se retiró `FAC-DEMO-0245` como sustituto visual.
- Evidencia VPS: API `96/96`, frontend público `5/5`, build productivo correcto, `/ready` con DB/Valkey/Frappe/esquema/IA/seguridad en `ok`, y revocación `200 -> 401`.

## Actualización 2026-08-21 — catálogo privado compatible por vehículo

- El portal dejó de importar `demoParts` y `demoVehicles` para la vista de repuestos.
- `GET /api/v1/client-portal/vehicles/{vehicle_id}/compatible-parts` valida cuenta, cliente, organización y propiedad del vehículo antes de consultar fitment persistido.
- La vista muestra fotografía publicada, SKU, precio, existencia, carga, error y estado vacío; un producto sin existencia no puede agregarse.
- Se añadió una prueba negativa contra un vehículo de otra organización.
- Evidencia VPS: suite API completa aprobada, frontend público `6/6`, login `204`, consulta privada `200` con tres productos persistidos, bundle servido `200` y `/ready` íntegro.

## Límite de producción que permanece abierto

El software no debe declararse totalmente productivo mientras falten credenciales SMTP, almacenamiento privado S3, configuración fiscal validada por contador, certificación del hardware POS, respaldo externo con restauración aislada y auditoría de seguridad independiente. Estos elementos no se simulan en el VPS de pruebas.

## Actualización 2026-08-21 — OT autoritativa y reconciliación ERP

- La imagen ERP `smartdiag504-erpnext-workshop:34` fue migrada y desplegada sin reiniciar MariaDB, Redis, Coolify ni Traefik.
- `Service Order` conserva diagnóstico, técnicos, bahía, repuestos, mano de obra y evidencia mediante campos `sd_platform_*` instalados por `after_migrate`.
- Crear o editar una OT, registrar mano de obra/evidencia o cambiar solicitudes de repuesto genera un UPSERT idempotente. En runtime estricto, la API sólo responde éxito después de obtener la referencia Beveren.
- Se añadió reconciliación explícita ERP → PostgreSQL con evento auditable y rechazo de estados desconocidos.
- Respaldo ERP previo con base y archivos: `20260820_201018`; respaldo PostgreSQL previo: `/opt/smartdiag504-backups/20260821T020549Z/platform/pre_erp_authority.dump`.
- Recorrido servido aprobado: `OT-2026-000009` creó `SVC-ORD-2026-00009`, sincronizó diagnóstico/bahía y volvió a leerlos con estado `SYNCED`.
- Suite API completa aprobada; Operaciones `19/19`, portal público `6/6`, ambos builds productivos aprobados; validación de repositorio/Compose aprobada.
- El host no incluye `make`, Node ni npm. Por ello los comandos equivalentes del Makefile se ejecutaron en contenedores reproducibles sobre el VPS; no se ejecutaron pruebas locales.
- Copia portable posterior a esta convergencia: `/opt/smartdiag504-portable/smartdiag504-portable-20260821T022305Z.tar.zst` y respaldo local `C:\Users\sammi\OneDrive\Desktop\vps\smartdiag504\portable\smartdiag504-portable-20260821T022305Z.tar.zst`; tamaño `495815325` bytes y SHA-256 remoto/local `b6c397ecb7751d3eafe4934d05b5ca8dfd2b9347fa265c035c533586875a4883`.

## Actualización 2026-08-21 — seguridad, sucursales y gates finales

- Se desplegó Alembic `0029_transaction_branch_scope` después del respaldo PostgreSQL `/opt/smartdiag504-backups/20260821T030918Z-branch-security/platform.pgdump`.
- Empresa y sucursal salen de la sesión; el personal operacional no puede leer o escribir transacciones de otra sucursal.
- La importación de imágenes quedó protegida contra DNS rebinding mediante conexión fijada a la IP pública validada.
- API: 104/104; contratos: 61/61; migración desde vacío: `head`; validación servida de roles/sucursal: `PASS`.
- Los 26 menús operativos y todos los submódulos críticos pasaron Playwright sin blanco, overlay ni error de consola.
- ERPNext imagen `smartdiag504-erpnext-workshop:36`: 39 enlaces visibles, 0 fallos, español/Honduras, escritorio/móvil, botón de regreso. La OT final `OT-2026-000012` quedó `SYNCED` con `SVC-ORD-2026-00012`.
- Compras/importación, RRHH/nómina y OT↔ERP se repitieron contra los dominios servidos y terminaron `SYNCED`.
- Las nueve cuentas demo SmartDiag, el cliente demo y el administrador ERP fueron verificados el mismo día.
- El detalle de seguridad está en `docs/security/SECURITY_REMEDIATION_2026-08-21.md` y el acta funcional en `docs/testing/ACTA_VALIDACION_FINAL_VPS_2026-08-21.md`.
- Paquete Debian final: `smartdiag504-platform_0.4.0_all.deb`, `33969340` bytes, SHA-256 `7231f106db1a29858c17a194104a945e028fab4c6d2b25046491294ed873c323`.
- Copia portable final: `smartdiag504-portable-20260821T033645Z.tar.zst`, `500262195` bytes, SHA-256 `f87dcfe974112b93f887adb0705989d5b7817597da29c6585c50eca1d6195a27`.

## Actualización 2026-08-21 — restauración y sucursal obligatoria

- Alembic `0030_require_transaction_branch` rellena y hace obligatoria la sucursal en todos los documentos transaccionales; los usuarios corporativos pueden conservar alcance multi-sucursal.
- La creación inicial de una empresa genera una sucursal `MAIN`; el personal operacional sin selección explícita queda asignado a ella y una sesión de otra sucursal no puede forzarla.
- Suite API completa aprobada en el VPS. La migración desde vacío creó 62 tablas.
- El respaldo previo `20260821T040527Z-pre-0030/platform-pre-0030.dump` se restauró y migró aisladamente: 12 OTs, revisión `0030`, cero sucursales nulas.
- Runtime servido: DB, Valkey, Frappe, esquema, IA y seguridad en `ok`; validación por rol `PASS`; `OT-2026-000013` ↔ `SVC-ORD-2026-00013`, `SYNCED`; outbox ERP sin fallos.
- Respaldo ERP `20260820_220818`: base comprimida y archivos públicos/privados íntegros.
- Paquete Debian actualizado: `smartdiag504-platform_0.4.0_all.deb`, `33973642` bytes, SHA-256 `968af9969fd8cc36450fbac06b88f90f130db8cf9487023dd5f400b6a28fd444`.
- Copia portable vigente: `smartdiag504-portable-20260821T041925Z.tar.zst`, `503713300` bytes, SHA-256 remoto/local `c3456e2ece3797a703deb57f18ebf7b282646653debf6e97b9276cb5012e044a`.

## Actualización 2026-08-21 — Garage/S3 privado

- Garage `v2.3.0` quedó desplegado sin puertos públicos, con credenciales exclusivas fuera del repositorio y bucket `smartdiag-evidence`.
- Las evidencias nuevas de OTs se guardan como objetos privados por empresa y OT; sólo se leen mediante la API autenticada. Los logos, campañas, catálogo y evidencias históricas mantienen compatibilidad con `/media` y el volumen privado anterior.
- Se aprobaron CRUD S3, carga desde OT, rechazo anónimo `401`, lectura autorizada `200`, persistencia tras reinicio y compatibilidad con evidencia histórica.
- `/ready` informa `object_storage: ok`. El manual técnico está en `docs/deployment/ALMACENAMIENTO_PRIVADO_S3_GARAGE_2026-08-21.md`.
- Este cierre no convierte el almacenamiento del mismo VPS en respaldo externo. La réplica cifrada y restauración fuera del servidor continúan pendientes.
- Artefacto portable limpio posterior a Garage: `smartdiag504-portable-20260821T140434Z.tar.zst`, `502893910` bytes, SHA-256 `b6f2c107ab2cf01018cc2c5a1b75d868342fe18dcf04e7bbc9869e2d83467b6a`.
- Instalador Debian posterior a Garage: `33977860` bytes, SHA-256 `7cb99e465c616c9be9f9f395977168d027e34b49e33dacbc124cb47545d57525`.
- Las copias portables anteriores quedan revocadas por una exclusión incompleta de `secrets/`; la credencial ERP afectada fue rotada y la entrega vigente pasó escaneo de secretos.
