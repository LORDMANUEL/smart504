# SmartDiag504: seguridad, escala y salida a producción

Fecha de corte: 2026-08-21. Este documento separa explícitamente código existente, validación servida y dependencias externas. Un HTTP 200 o un contenedor saludable no certifica un flujo de negocio.

## Estado ejecutivo

La plataforma es una **candidata de producción**, no una producción certificada todavía. El escaneo de seguridad de todo el monorepo revisó 66 controles/archivos representativos y registró 15 hallazgos: 6 altos, 7 medios y 2 bajos. En esta fase se corrigieron los bloqueadores de admisión pública, asistente interno, re-enrolamiento MFA, doble consumo de devoluciones y lectura de vouchers entre sucursales. La aprobación final exige desplegar esta revisión y obtener evidencia en el VPS.

## Terminado en producto

- Landing, tienda, portal cliente, citas, catálogo por VIN, pedidos web y captura de leads.
- Operaciones de taller: Kanban, bahías, OT, check-in 360, fotos privadas, diagnóstico, cronómetro, repuestos, mano de obra y control de calidad obligatorio.
- Cotizaciones HTML/PDF, aprobación por líneas, conversión a OT y centro de plantillas reemplazables por empresa/sucursal.
- Mostrador, caja, apertura/cierre, arqueo, pagos, factura, devolución/garantía con autorización y sincronización ERP.
- Bodega, múltiples ubicaciones, reservas, picking, entregas, devoluciones, transferencias, fletes y documentos.
- Compras, proveedores, recepción e importación; RRHH, asistencia, permisos, contratos, nómina y vouchers.
- ERPNext/Beveren en español, lanzador SmartDiag504, proyecciones operativas y cola de conciliación.
- CRM, calidad, publicidad, reportes operativos, tutoriales guiados, logs/heatmap y almacenamiento privado Garage/S3.
- Empaque portable y paquete Debian para una nueva VPS.

## Controles de seguridad incorporados

- Límite distribuido y atómico en Valkey para citas, pedidos, leads, creación de chat y mensajes. En producción falla cerrado si Valkey no está disponible.
- Campo honeypot `website` en formularios públicos; nunca se persiste.
- La IP usada para control proviene de `request.client`, después de la validación de proxy de Uvicorn; la aplicación no confía directamente en `X-Forwarded-For` del navegador.
- `/v1/assist` exige token interno; el navegador sólo debe alcanzar el contrato reducido de chat público.
- MFA activo no puede ser reemplazado silenciosamente; debe desactivarse con el TOTP actual y los cambios revocan sesiones.
- Autorizaciones de devolución se bloquean en base de datos antes de consumirse.
- Vouchers de nómina respetan organización y sucursal del usuario.
- Evidencia de OT y comprobantes usan rutas privadas mediadas por autenticación; no son enlaces públicos.
- Prueba k6 reproducible para 1,000 sesiones compradoras, con 100 concurrentes por defecto y umbrales de error <1 %, p95 <1.5 s y p99 <3 s.

## DEMO — mantener ahora, reemplazar antes de producción

No se cambiaron durante esta fase:

- Usuarios, contraseñas, PIN de caja y datos precargados de demostración.
- Empresa fiscal, RTN, CAI, rangos, impuestos, correlativos y plantillas definitivas.
- Remitente/dominio SMTP y reputación DNS; el Postfix local de pruebas no equivale a correo productivo.
- URLs, claves y cuenta de mensajería/redes sociales.
- Proveedor/adquirente de pago y operador logístico; sigue permitido adjuntar comprobante privado.
- Credencial global de recuperación usada por automatizaciones de demo. Para producción debe deshabilitarse o convertirse en acceso break-glass temporal, restringido y auditado.
- Cualquier fixture, imagen, vehículo, precio, proveedor o empleado identificado como demo.

## Pendientes que bloquean la etiqueta PRODUCCIÓN

1. Desplegar la revisión en el VPS de pruebas y ejecutar migraciones sin reiniciar Coolify ni servicios ajenos.
2. Ejecutar suites API, IA y frontend servidas por cada rol; registrar cero fallos y conservar logs.
3. Ejecutar `k6_buyers_1000.js`: primero 100, luego 250 y finalmente 1,000 sesiones. No saltar de inmediato a máxima carga.
4. Confirmar que el rate limiter devuelve 429, el honeypot 422 y que no crea filas ni trabajos.
5. Verificar aislamiento empresa/sucursal con dos organizaciones y dos sucursales reales de prueba.
6. Conciliar una operación completa en ERP: cita -> OT -> diagnóstico -> cotización -> reserva/salida -> factura/pago -> asiento; diferencias deben ser cero.
7. Probar Garage con PUT/GET/DELETE privado y confirmar que la llave sólo accede al bucket asignado.
8. Ejecutar restauración aislada de PostgreSQL/MariaDB/Garage. El respaldo externo se configura en infraestructura distinta a este VPS.
9. Contador: configurar fiscalidad, CAI/rangos o modalidad autoimpresor/preimpreso; certificar notas de crédito y cierres.
10. Hardware: probar impresora térmica/normal, lector, gaveta y datáfono con modelos adquiridos.

## Hallazgos que siguen como endurecimiento significativo

- Separación maker-checker de nómina con actores distintos al crear, revisar, aprobar y contabilizar.
- Token de recuperación temporal, con caducidad, restricción de origen y alerta; nunca estático en producción.
- Consumo atómico y atribución correcta de links públicos de aprobación.
- Separar catálogo público de VIN del registro privado de vehículos de clientes.
- Parser allowlist para HTML/CSS y callback cerrado de recursos al renderizar PDF.
- Política de salida de IA contra extracción obfuscada/multiturno; los prompts nunca contienen secretos.
- Decodificar/re-encodear imágenes de comprobantes, parser PDF endurecido y análisis antimalware.
- Unificar CSP y encabezados en Caddy, HAProxy y Nginx, con smoke test del borde efectivo.

## Comando de carga en el VPS de pruebas

```bash
docker run --rm -i -e BASE_URL=https://taller.nexusmedi.org -e VUS=100 -e BUYERS=1000 grafana/k6 run - < tests/load/k6_buyers_1000.js
```

La prueba representa 1,000 recorridos compradores y 100 usuarios virtuales concurrentes, no 1,000 escrituras simultáneas. Las compras reales se prueban aparte con datos sintéticos etiquetados y se eliminan de forma controlada.

## Criterio de liberación

Se marca PRODUCCIÓN solamente cuando: pruebas servidas y de seguridad pasan; conciliación ERP da cero diferencias; aislamiento multiempresa/sucursal está demostrado; restauración aislada funciona; fiscalidad y hardware cuentan con aceptación externa; secretos demo se reemplazan; y existe rollback verificado. Hasta entonces la versión visible debe decir **DEMO / CANDIDATA DE PRODUCCIÓN**.

## Evidencia ejecutada en el VPS de pruebas

- API: 108/108 pruebas pasaron.
- Gateway IA: 15/15 pruebas pasaron; `/v1/assist` sin token interno devuelve 401.
- Honeypot de cita: payload con `website` no vacío devuelve 422 y no entra al flujo.
- Límite distribuido de chat: seis creaciones permitidas y la séptima devuelve 429 dentro de la ventana.
- ERP: el reporte de trabajos fallidos devolvió `[]` después del despliegue.
- Recuperación: API, gateway, IA, PostgreSQL, Valkey y Garage quedaron saludables; catálogo volvió a 200 en 0.119 s al terminar la carga.
- Carga externa: se completaron 1,000 iteraciones con 100 VUs y 2,000 solicitudes. La landing pasó, pero el catálogo sólo obtuvo 159/1,000 respuestas válidas; 841 expiraron/fallaron, error global 42.05 %, p95 4.77 s y p99 60 s. **Resultado: NO APROBADO para 100 compradores concurrentes.**

### Revalidación posterior a la corrección

Se añadió caché compartida de 30 segundos en Valkey con bloqueo anti-estampida y encabezado `stale-while-revalidate`, conservando paginación y filtros en la clave. La misma prueba, sin relajar umbrales, se repitió el 21 de agosto de 2026:

- 1,000/1,000 recorridos terminados con 100 VUs.
- 2,000 solicitudes HTTP; 0 errores.
- 3,000/3,000 comprobaciones aprobadas.
- p95 938.22 ms y p99 1.35 s.
- Resultado: **APROBADO** para este perfil de lectura comprador.

También se aplicaron los endurecimientos antes listados de maker-checker de nómina, recuperación restringida en producción, aprobación pública atómica, privacidad de VIN, allowlist de plantillas, política de salida IA y validación de comprobantes. El análisis antimalware/CDR de PDFs y la expiración criptográfica del token break-glass siguen como defensa adicional de producción.
# Actualización de cierre — escaneo y aceptación por rol

El runtime de prueba incorpora `clamav/clamav:stable` dentro de la red privada. `platform-api` usa el protocolo `INSTREAM`, analiza bytes antes de la escritura y, con `MALWARE_SCANNER_REQUIRED=true`, responde 503 si el escáner no está disponible. Esta propiedad evita que una caída silenciosa convierta la carga en un bypass. La prueba EICAR confirmó rechazo y la prueba segura confirmó disponibilidad.

La aceptación autenticada cubrió OWNER, ADMIN, MANAGER, RECEPTION, TECHNICIAN, WAREHOUSE, CASHIER, ACCOUNTANT, MARKETING y AUDITOR. El resultado final fue 262 páginas con cero violaciones axe. Las cuentas generadas para el ensayo fueron desactivadas.

Esto endurece la aplicación, pero no convierte un único VPS en una plataforma para un millón de solicitudes concurrentes. Ese objetivo requiere WAF/CDN, origen no público, límites por identidad y operación, réplicas horizontales, pool de conexiones, cola con backpressure, observabilidad y una prueba distribuida con SLO acordado. Hasta ejecutar esa arquitectura y medirla, la capacidad confirmada sigue siendo la carga documentada del piloto, no un millón de transacciones.
