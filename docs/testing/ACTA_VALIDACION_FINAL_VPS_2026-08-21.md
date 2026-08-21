# Acta de validación funcional servida — SmartDiag504

**Fecha:** 21 de agosto de 2026  
**Entorno:** VPS exclusivo de pruebas `taller.nexusmedi.org` / `erp.nexusmedi.org`  
**Regla:** no se ejecutaron builds, migraciones ni pruebas de aplicación en la computadora local.

## Resultado

El código desplegado queda apto para demostración integral y piloto controlado. No se declara apto para producción fiscal con datos reales hasta completar las dependencias externas enumeradas al final.

## Cierre técnico adicional del 21 de agosto

- Se incorporó ClamAV como servicio privado, con firmas persistentes y política de fallo cerrado. Todas las cargas que pasan por almacenamiento público o privado se analizan antes de escribir. La firma inocua EICAR fue rechazada con HTTP 422 y un archivo seguro fue aceptado.
- El gate visual autenticado se amplió a diez roles internos, móvil 360 px y escritorio 1366 px. Primera ejecución: 262 páginas, 42 violaciones graves. Después de corregir contraste y nombres accesibles: 262 páginas, 0 violaciones y 0 graves.
- La suite completa del repositorio se ejecutó dentro del VPS con Playwright y navegadores reales: 202/202 pruebas. Dos pruebas antiguas dependían de la fecha vencida `2026-08-20`; se cambiaron a una fecha futura estable y se repitió el conjunto completo.
- El flujo final creó `OT-2026-000028` con ingreso 360, cronómetro detenido y calidad aprobada, y terminó `READY_TO_INVOICE:SYNCED`. La prueba independiente de convergencia creó `OT-2026-000029` y su `SVC-ORD-2026-00029` autoritativa en ERPNext.
- Se desactivaron 73 identidades efímeras de aceptación. No quedaron esas credenciales habilitadas.
- El gate de preparación efectivo conserva el resultado `production_ready=false`: fiscalidad aprobada, hardware fiscal y respaldo fuera del VPS siguen pendientes de terceros. El sistema no los sustituye por banderas simuladas.

## Pruebas aprobadas

| Superficie | Evidencia |
|---|---|
| API | 106/106 pruebas |
| Dominio y contratos | 61/61 pruebas |
| Esquema | Alembic 0031 activo; 0030 validado previamente desde vacío y restauración temporal |
| Salud | DB, Valkey, almacenamiento, Frappe, esquema, IA y seguridad `ok` |
| Roles | Marketing/RRHH, contador/social, técnico/documentos-catálogo y caja/OT correctamente separados |
| Sucursales | técnico de sucursal B no ve OTs de A; escritura cruzada rechazada |
| Operación web | 26 menús, Compras, RRHH, Técnico, Documentos, Guía, TV y landing sin blanco ni overlay |
| ERP | 39 enlaces, 0 errores, español, Honduras, escritorio/móvil y botón volver |
| Compras | proveedor → OC → recepciones → importación → landed cost, `SYNCED` |
| RRHH | contrato → asistencia/extra → nómina → voucher HTML, `APPROVED:SYNCED` |
| OT | `OT-2026-000013` ↔ `SVC-ORD-2026-00013`, `SYNCED` |
| Credenciales demo | nueve roles SmartDiag, cliente y administrador ERP verificados |
| Evidencia privada | Garage/S3 interno, carga OT, `401` anónimo, `200` autorizado y persistencia tras reinicio |
| Control de taller | ingreso 360 + cronómetro detenido + QC separado; `OT-2026-000023` llegó a `READY_TO_INVOICE:SYNCED` |
| Pago web alternativo | comprobante PDF privado en Garage; descarga anónima `401` y autenticada `200` |
| Correo | Postfix del VPS aceptó y entregó una alerta de prueba a `root@localhost`; no se contactó a clientes |
| ERP empresarial | proveedor, compra, importación, contrato y nómina sincronizados; cola de fallos ERP final `[]` |

## Prueba de restauración y propiedad por sucursal

- La revisión `0030_require_transaction_branch` hace obligatoria la sucursal en citas, pedidos, OTs, cotizaciones, caja, pagos, compras, contratos y vehículos usados.
- Un ensayo desde una base vacía llegó a `0030` con 62 tablas.
- El respaldo previo `/opt/smartdiag504-backups/20260821T040527Z-pre-0030/platform-pre-0030.dump` se restauró en una base temporal, se migró y terminó con 12 OTs y cero transacciones sin sucursal.
- El dump incluido en la copia portable se restauró nuevamente de forma aislada: 62 tablas, revisión `0030` y cero sucursales nulas. Las bases temporales fueron eliminadas.
- El respaldo ERP `20260820_220818` pasó `gzip -t` para MariaDB y `tar -tf` para archivos públicos y privados. No se hizo una restauración ERP sobre el sitio activo.

## Rutas para el evaluador

- Landing: <https://taller.nexusmedi.org/lading>
- Tienda: <https://taller.nexusmedi.org/lading/repuestos>
- Cliente: <https://taller.nexusmedi.org/lading/loginclie>
- Taller: <https://taller.nexusmedi.org/tallerv1/login>
- Técnico: <https://taller.nexusmedi.org/tallerv1/tecnico>
- Mostrador: <https://taller.nexusmedi.org/tallerv1/mostrador>
- Caja: <https://taller.nexusmedi.org/tallerv1/caja>
- Bodega: <https://taller.nexusmedi.org/tallerv1/bodega>
- Compras: <https://taller.nexusmedi.org/tallerv1/compras>
- RRHH: <https://taller.nexusmedi.org/tallerv1/rrhh>
- Contador: <https://taller.nexusmedi.org/tallerv1/contador>
- Publicidad: <https://taller.nexusmedi.org/tallerv1/publicida>
- TV: <https://taller.nexusmedi.org/tallerv1/publicida/tv>
- Guía: <https://taller.nexusmedi.org/tallerv1/guias>
- ERP: <https://erp.nexusmedi.org/app/smartdiag-workshop>

Las credenciales temporales están en `docs/operations/MANUAL_COMPLETO_SMARTDIAG504_2026-08-17.md`. Deben cambiarse antes de entregar el entorno a usuarios reales.

## Bloqueos externos para producción real

1. contador: empresa, cuentas, impuestos, CAI/rangos, papel preimpreso y cierre de prueba;
2. correo externo: corregir PTR/HELO, certificado de `mail.nexusmedi.org`, entrega/reputación y Dovecot sólo si habrá buzones;
3. política definitiva de retención y antivirus para objetos privados;
4. POS/datáfono, gaveta, lector e impresoras certificados en sitio;
5. respaldo cifrado en infraestructura externa y restauración periódica medida;
6. pentest independiente, firewall, rotación de secretos y aceptación formal por rol.

No se sustituyó ninguno de estos puntos por una simulación.
