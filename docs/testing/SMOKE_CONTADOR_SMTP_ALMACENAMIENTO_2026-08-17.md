# Smoke test de contador, impresión, SMTP y almacenamiento

Fecha: 17 de agosto de 2026. Entorno: VPS de pruebas publicado. No se creó un clon del sistema ni se instaló una máquina virtual.

## Prueba como contador

Se inició sesión con el usuario demo de rol `ACCOUNTANT` y se ejecutó una prueba fiscal controlada:

1. Se creó un borrador marcado `PRUEBA-SIN-VALIDEZ-FISCAL`.
2. Intentar activarlo sin confirmación del contador devolvió HTTP `422`.
3. Con confirmación explícita pasó a `ACTIVE`.
4. Al finalizar se cerró el registro de prueba y se restauró la configuración activa anterior.

La prueba no crea ni simula una autorización SAR. Verifica el control de estados, autorización, auditoría y restauración de la configuración previa.

## Conciliación y reporte

El reporte operativo respondió con fuente `ERPNext`:

- ventas brutas: L 960.00;
- ventas netas: L 0.00;
- utilidad bruta: L 0.00.

El neto cero es coherente con los datos actuales de demostración: las ventas fueron completamente devueltas. La consulta directa de sólo lectura a ERPNext confirmó:

- facturas y devoluciones con `docstatus = 1` y saldo pendiente L 0.00;
- pagos `Receive` y reembolsos `Pay` por L 320.00;
- cuatro asientos por factura/devolución;
- débitos L 512.00 y créditos L 512.00 en cada documento consultado.

Por tanto, los documentos consultados están contabilizados y balanceados. Esto no sustituye un cierre mensual ni una revisión profesional del plan de cuentas, impuestos o SAR.

## Impresión y POS

- Factura PDF: HTTP 200, cabecera `%PDF`, tipo `application/pdf`, 2,739 bytes.
- Vista previa térmica de 80 mm: HTTP 200 y HTML renderizado.
- El sistema puede producir PDF/HTML para impresora normal o térmica.
- No hay impresora, gaveta, lector ni datáfono conectados al VPS; la prueba física sigue pendiente del modelo que compre el taller.

## Alertas por SMTP

No se configuró Facebook, Meta, WhatsApp, SMS ni push porque no son prioridad en esta fase.

El mismo transporte SMTP de SmartDiag se ejecutó contra un buzón SMTP temporal aislado y entregó un mensaje. Después se eliminó el contenedor y su imagen. Esto prueba que para activar las alertas inmediatas sólo hacen falta:

- `SMTP_HOST`;
- `SMTP_PORT`;
- `SMTP_FROM_EMAIL`;
- `SMTP_USE_TLS`;
- `SMTP_USERNAME` y `SMTP_PASSWORD` cuando el servidor exija autenticación.

El VPS publicado todavía no tiene esos valores. Mientras sigan vacíos, los mensajes se conservan como bloqueados/pendientes y no se marcan falsamente como enviados.

## Evidencias privadas

Se consultó una fotografía existente de OT mediante tres perfiles:

- sin sesión: HTTP `401`;
- contador, que no tiene permiso técnico: HTTP `403`;
- acceso operativo autorizado: HTTP `200`.

La descarga autorizada incluyó `Cache-Control: private, no-store`. En este VPS las evidencias viven en un volumen Docker persistente, no en S3 externo. Esto es adecuado para pruebas, pero no elimina el requisito de almacenamiento privado externo para producción.

## Respaldo

Se verificó con `gzip -t` el archivo SQL local más reciente y no se generó una copia completa adicional. El resultado fue `LOCAL_ARCHIVE_OK`.

El respaldo externo no está configurado en este VPS de pruebas, conforme a la regla del proyecto. Debe apuntarse a otro proveedor/servidor y validarse allí antes de producción.

## Resultado resumido

| Área | Resultado |
|---|---|
| Rol contador y control fiscal | Aprobado en modo prueba |
| Facturas, pagos y asientos ERP | Aprobado para los documentos consultados |
| PDF y formato térmico | Aprobado en software |
| Hardware físico | No conectado; no probado |
| Transporte SMTP | Aprobado con servidor temporal |
| SMTP publicado | Pendiente de credenciales |
| Privacidad de evidencia | Aprobada para los perfiles consultados |
| Respaldo local existente | Integridad gzip aprobada |
| Respaldo externo | Pendiente fuera del VPS de pruebas |

