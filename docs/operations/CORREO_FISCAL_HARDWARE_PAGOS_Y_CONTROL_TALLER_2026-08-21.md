# Correo, fiscalidad, hardware, pagos y control de taller

**Corte:** 21 de agosto de 2026  
**Entorno:** VPS de pruebas SmartDiag504

## Estado funcional comprobado

| Bloque | Estado | Evidencia o límite |
|---|---|---|
| Postfix saliente | Funcional en pruebas | El API conecta al Postfix del VPS por la red privada y entregó una prueba a `root@localhost`. No se envió correo a clientes durante la validación. |
| Dovecot / buzones | No habilitado públicamente | El VPS no tiene todavía certificado válido para `mail.nexusmedi.org`; exponer IMAP con el certificado autofirmado actual sería inseguro. Dovecot no es necesario para que SmartDiag envíe alertas. |
| DNS de correo | Parcial | MX, SPF, DKIM y DMARC existen. El PTR y el saludo SMTP aún identifican `vmi3350998.contaboserver.net`; el proveedor del VPS debe cambiar el PTR antes del correo productivo. |
| Pago web alternativo | Funcional | Caja puede adjuntar PDF/JPG/PNG privado al pedido; queda evento auditable, hash y almacenamiento Garage/S3. Prueba servida: anónimo `401`, autorizado `200`. |
| Pasarela bancaria | No configurada | Requiere contrato y credenciales del adquirente. Mientras tanto se usa comprobante y validación humana antes de reservar/despachar. |
| Ingreso 360, tiempo y calidad | Funcional | Una OT no pasa a lista para facturar sin check-in aceptado, QC aprobado por un rol distinto al técnico y cronómetro detenido cuando fue iniciado. |
| Fiscal Honduras | Configurable, no certificado | El contador debe aprobar empresa, RTN, CAI, rango, fecha límite, impuestos y modalidad antes de facturar en producción. |

## Configuración de correo

El runtime lee `secrets/smtp.env`; el archivo nunca debe incluirse en el repositorio ni en la copia portable. Para este VPS de pruebas:

```dotenv
SMTP_HOST=10.0.10.1
SMTP_PORT=25
SMTP_USE_TLS=false
SMTP_FROM_EMAIL=notificaciones@nexusmedi.org
```

Esta conexión sin TLS es exclusivamente contenedor → host dentro del VPS. Para entrega productiva:

1. solicitar a Contabo el PTR de `13.140.138.152` hacia `mail.nexusmedi.org`;
2. configurar `myhostname` y HELO coherentes;
3. emitir y renovar un certificado público para `mail.nexusmedi.org`;
4. habilitar submission `587` con TLS y autenticación SASL;
5. instalar Dovecot sólo si se necesitan buzones IMAP, con TLS obligatorio, cuotas, antispam, fail2ban y respaldos;
6. hacer una prueba autorizada a Gmail/Outlook y revisar SPF, DKIM, DMARC y reputación.

## Flujo de pago sin pasarela

1. El pedido entra a **Pedidos web**.
2. Caja abre la tarjeta, confirma cliente y monto.
3. En **Comprobante de pago** registra referencia, monto y PDF/JPG/PNG.
4. El sistema guarda el objeto privado y un evento `STORE_PAYMENT/PAYMENT_PROOF_UPLOADED`.
5. Caja valida banco y mueve a **Pagado**; bodega reserva después de esa validación.
6. Flete agrega transportista, guía y evidencia; entrega o devolución conserva historial.

No se debe marcar pagado por el simple hecho de cargar un archivo. La validación bancaria sigue siendo responsabilidad de caja hasta integrar una pasarela con webhook firmado e idempotente.

## Configuración fiscal hondureña

El menú **Contador** debe usarse como asistente de configuración, no como sustituto del criterio profesional. Debe pedir y validar:

- razón social, nombre comercial, RTN, dirección y sucursal;
- CAI, tipo de documento, rango autorizado, fecha límite y punto de emisión;
- impuestos y exoneraciones aplicables;
- modalidad: autoimpresor, imprenta/preimpreso o recibo interno no fiscal;
- plantilla activa para carta, A4 o térmica de 80 mm;
- reglas de notas de crédito, anulaciones, cierres y conservación.

Si no existe CAI aprobado, SmartDiag puede imprimir **recibo interno/no fiscal** o utilizar hoja preimpresa autorizada, pero debe mostrar esa condición claramente. Nunca debe inventar CAI ni rango. La referencia oficial es el [Reglamento consolidado del Régimen de Facturación del SAR](https://www.sar.gob.hn/download/texto-consolidado-del-reglamento-del-regimen-de-facturacion-otros-documentos-fiscales-y-registro-de-imprentas-segun-acuerdos-609-2017-725-2018-y-817-2018-elaborado-por-la-direccion-nacional-juridc/) y la [Oficina Virtual del SAR](https://www.sar.gob.hn/ovi/), que ofrece inscripción, autorización de impresión y validación de documentos.

## Equipo recomendado para el piloto

Comprar primero una estación, validar y luego replicar:

| Área | Equipo base | Motivo y prueba |
|---|---|---|
| Caja | Epson TM-T20III Ethernet + USB, papel 80 mm | ESC/POS, corte automático y red. Probar recibo, factura, logo, QR, caracteres españoles, reimpresión y corte. Epson documenta USB 2.0 y variantes Ethernet. |
| Escaneo | Zebra DS2208 USB 1D/2D | Funciona como HID/teclado; permite SKU, código de barras y QR. Probar foco en buscador, cantidad, producto inexistente y doble lectura. |
| Gaveta | Gaveta 24 V compatible con el puerto de la impresora elegida | Probar apertura sólo después de cobro autorizado, apertura manual auditada y cierre de caja. Confirmar voltaje/conector con el distribuidor. |
| Documentos | Impresora láser A4/Letter de red con dúplex | Cotización, diagnóstico con fotos, picking, garantías y reportes. Probar márgenes Carta, firma y PDF. |
| Técnico | Teléfono/tablet Android con cámara, funda y Wi-Fi estable | Check-in 360, VIN, firma, fotos y cronómetro. Probar cámara trasera, permisos y carga de 8 MB. |
| Firma opcional | Pad de firma con SDK web o firma táctil en tablet | Comprar sólo después de confirmar compatibilidad del SDK con navegador y sistema operativo. |
| Energía | UPS para router, switch, caja e impresora | Permite cierre seguro y evita corrupción/operaciones partidas. |

Referencias técnicas: [Epson TM-T20III](https://files.support.epson.com/pdf/pos/bulk/tm-t20iii_trg_en_reva.pdf) y [Zebra DS2200](https://www.zebra.com/la/es/products/spec-sheets/scanners/general-purpose-scanners/handheld/ds2200-series.html).

## Prueba por roles del control de taller

1. **Recepción:** crea cliente/vehículo, registra kilometraje, combustible, accesorios, observaciones y aceptación del check-in.
2. **Técnico:** inicia, pausa/reanuda y detiene el cronómetro; adjunta fotos por categoría y agrega diagnóstico/repuestos.
3. **Supervisor/gerencia:** ejecuta checklist, prueba de carretera si aplica y aprueba o rechaza calidad. El técnico no puede autoaprobar.
4. **Asesor:** arma cotización y obtiene aprobación por línea.
5. **Caja:** sólo ve la OT en lista de cobro cuando los controles están completos; factura/cobra y entrega pase.
6. **Auditor:** revisa eventos, actores, tiempos, archivos privados y referencia ERP.

El gate servido `scripts/validate-served-operational-gates.sh` ejecuta este recorrido con datos sintéticos y debe terminar en `READY_TO_INVOICE`, `SYNCED` y los controles `CHECK_IN_360`, `TIMER_STOPPED`, `QUALITY_PASS`.

## MFA del cliente

MFA queda como opción de configuración y no como bloqueo de salida solicitado. La interfaz no debe simular activación: hasta implementar enrolamiento TOTP completo, códigos de recuperación, desafío en login y revocación, debe mostrar **No configurado**. Para clientes con crédito, flotas o datos sensibles se recomienda exigirlo antes de producción real.

## Qué aún requiere terceros

- contador que firme fiscalidad y cierre de prueba;
- proveedor del VPS para PTR;
- certificado público y política de buzones antes de Dovecot;
- adquirente/pasarela y transportistas para webhooks reales;
- hardware físico para certificar impresión, gaveta, escáner y POS;
- almacenamiento/backup externo: Garage protege objetos dentro del VPS, pero no sustituye una copia fuera del servidor.
