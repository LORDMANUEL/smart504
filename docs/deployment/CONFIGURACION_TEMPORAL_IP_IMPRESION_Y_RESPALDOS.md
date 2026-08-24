# Configuración temporal por IP — SmartDiag504

Fecha de corte: 2026-08-23. Servidor de pruebas: `169.58.217.146`.

## Accesos temporales HTTPS

- Taller y tienda: `https://taller.169.58.217.146.sslip.io/lading`
- Portal de clientes: `https://clientes.169.58.217.146.sslip.io/lading/cliente`
- Operaciones: `https://app.169.58.217.146.sslip.io/tallerv1/login`
- ERPNext: `https://erp.169.58.217.146.sslip.io`
- API: `https://api.169.58.217.146.sslip.io/ready`

`sslip.io` resuelve gratuitamente hacia la IP. Es temporal: el correo empresarial y la reputación SMTP requieren el dominio definitivo y sus registros DNS.

## Sucursal y bodegas iniciales

El instalador idempotente crea la sucursal activa `MAIN`, **SmartDiag504 - Taller principal**, junto con:

- Bodega principal.
- Repuestos reservados / proceso.
- Bodega en tránsito.
- Bodega de devoluciones.

## Documentos e impresión

Se incluyen 33 formatos editables: 11 tipos documentales y tres perfiles por tipo.

- Membrete SmartDiag504 para Epson EcoTank L3250.
- Papel preimpreso tamaño carta.
- Archivo PDF desde el navegador.

Tipos cubiertos: cotización, factura, diagnóstico, OT, garantía, pase de salida, picking, entrega, devolución, entrada de bodega y voucher de pago.

La factura predeterminada usa **papel preimpreso**. El sistema imprime el contenido variable y conserva el HTML exacto utilizado. El administrador puede crear versiones, previsualizar, publicar, exportar, importar y reemplazar cada formato desde **Configuración → Centro de documentos**. El logo, colores y pie se obtienen de la configuración de marca de la empresa.

La aplicación no inventa CAI ni rangos. El control del bloque fiscal impreso continúa siendo responsabilidad del contador y del talonario autorizado.

## Epson L3250

1. Instalar el controlador oficial Epson en la computadora de caja.
2. Configurar papel Carta, escala 100 %, orientación vertical y márgenes según el formato.
3. Para factura preimpresa, colocar el talonario en la bandeja y seleccionar el formato **Factura preimpresa · Papel preimpreso**.
4. Ejecutar una hoja de calibración antes de operar y ajustar únicamente los márgenes de la versión; nunca editar el documento histórico.

## POS bancario

El datáfono funciona fuera de SmartDiag504. En Caja se selecciona **Tarjeta / POS**, se procesa el pago físicamente y se registra el número de referencia entregado por el banco. La referencia es obligatoria. SmartDiag504 no solicita ni almacena PAN, CVV, PIN ni datos de banda/chip.

## Snapshots locales

`scripts/vps-local-snapshot.sh` guarda en `/var/backups/smartdiag504-local`:

- PostgreSQL de la plataforma.
- MariaDB de ERPNext.
- Sitios y archivos privados de Frappe.
- Datos de Garage/S3.
- Manifiesto SHA-256.

Cada ejecución restaura PostgreSQL en una base temporal, cuenta las tablas y elimina la base temporal. La retención predeterminada es 14 días.

Este respaldo protege contra errores lógicos y despliegues defectuosos, pero no contra pérdida total, corrupción o secuestro del VPS. Esa limitación queda aceptada temporalmente por el propietario.

## Operación automática

El VPS instala un servicio y temporizador `smartdiag504-local-snapshot.timer` para ejecutar el respaldo diariamente. Revisar:

```bash
systemctl status smartdiag504-local-snapshot.timer
journalctl -u smartdiag504-local-snapshot.service
readlink -f /var/backups/smartdiag504-local/latest
```

No se guardan contraseñas en este documento.
