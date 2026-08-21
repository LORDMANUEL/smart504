# Cierre de seguridad aplicado — 21 de agosto de 2026

## Alcance

Se ejecutó Codex Security en modo estándar sobre el repositorio completo. El escaneo `c3fb5c15-d9d7-43a5-b0af-f97d5d6c1786` encontró dos rutas explotables: falta de aislamiento transaccional por sucursal y una ventana de DNS rebinding al importar imágenes remotas. Ambas se corrigieron, probaron y desplegaron en el VPS de pruebas.

## Correcciones

### Aislamiento por empresa, sucursal y sesión

- `RequestIdentity` ahora distingue acceso corporativo de acceso obligado a una sucursal.
- Dueño y administrador pueden consolidar sucursales; cualquier usuario operacional con sucursal asignada queda filtrado en el servidor.
- El filtro cubre sucursales, personal, citas, pedidos, OTs, cotizaciones, caja, pagos, bodegas, mostrador, documentos fiscales, compras, contratos y usados.
- Una escritura sin sucursal hereda la sucursal de la sesión; una escritura dirigida a otra sucursal se rechaza.
- La migración `0029_transaction_branch_scope` agrega y rellena `branch_id` en citas, OTs, cotizaciones, sesiones de caja y pagos.
- Las citas públicas y del portal se asignan a la sucursal principal activa.

La prueba negativa crea dos sucursales: una cajera de A sólo obtiene transacciones de A y no puede insertar en B. La prueba servida asigna un técnico a una sucursal aislada y confirma que no recibe ninguna OT de la principal.

### Importación segura de imágenes

- La URL sólo admite HTTP(S), sin credenciales embebidas.
- Todas las respuestas DNS deben ser direcciones públicas.
- La descarga usa una URL fijada a una de las IP verificadas; `Host` y TLS SNI conservan el dominio original.
- No existe una segunda resolución DNS entre validación y conexión.
- Puede configurarse una lista exacta con `REMOTE_IMAGE_ALLOWED_HOSTS`.
- Se mantienen límites de bytes, MIME, formato, dimensiones y píxeles.

## Evidencia ejecutada sólo en el VPS

- Suite API: 104 pruebas aprobadas.
- Contratos de dominio/repositorio/Frappe/Compose/operación: 61 pruebas aprobadas.
- Migración completa desde base vacía: revisión `0029_transaction_branch_scope (head)`.
- Prueba servida de rol y sucursal: `PASS`, incluyendo 403 en escrituras indebidas.
- Interfaz operativa: 26 rutas principales y sus submódulos, cero páginas blancas, overlays o errores de consola.
- ERPNext: 39 enlaces visibles, cero errores de permisos/rutas, escritorio y móvil sin desbordamiento.

## Límites que requieren terceros

Este cierre no sustituye un pentest independiente, escaneo de imágenes de contenedor, S3 privado, gestión corporativa de secretos ni configuración de firewall del VPS de producción. Esos controles siguen siendo obligatorios antes de operar datos reales.
