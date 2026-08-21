# Recorrido guiado y venta de mostrador por bodega

## Alcance funcional

Esta entrega añade dos controles operativos:

1. Al iniciar sesión, cada empleado recibe un recorrido emergente acorde con su rol. Puede avanzar, retroceder, omitirlo y volver a abrirlo con el botón **Abrir recorrido guiado** de la barra superior.
2. Mostrador sólo permite seleccionar artículos existentes del catálogo y con saldo disponible en la bodega elegida. No existe creación libre de artículos ni edición manual del precio desde caja.

## Flujo de mostrador

1. Ingrese en [Mostrador](https://taller.nexusmedi.org/tallerv1/mostrador).
2. Seleccione sucursal y bodega en el carrito.
3. Opcionalmente consulte el VIN para filtrar compatibilidad.
4. Busque por nombre, SKU u OEM.
5. Revise la fotografía, código, compatibilidad, saldo de la bodega, precio y precio mínimo.
6. Sólo el botón **Agregar** habilitado puede llevar una pieza al carrito.
7. El servidor vuelve a comprobar artículo, precio exacto de catálogo y saldo bloqueado de la bodega al cobrar. La interfaz no es la autoridad final.

Un artículo queda bloqueado con una explicación visible cuando:

- no tiene código de artículo;
- no tiene precio de venta mayor que cero;
- no tiene saldo disponible en la bodega seleccionada;
- la cantidad solicitada supera la existencia disponible.

## Solicitud de un artículo faltante

1. Escriba lo solicitado en **Búsqueda solicitada**.
2. Complete cantidad y, si aplica, cliente, teléfono, VIN y observación.
3. Pulse **Solicitar a Compras**.
4. El sistema genera un número `SOL-MOST-*`, conserva usuario, empresa, sucursal y fecha, y registra el evento `COUNTER_SALES.ITEM_REQUESTED`.
5. Compras abre [Compras e importación](https://taller.nexusmedi.org/tallerv1/compras) y entra en **Solicitudes de clientes**.
6. Compras valida proveedor, código, costo y precio antes de crear formalmente el artículo en Catálogo/ERPNext. La solicitud nunca crea inventario automáticamente.

## Evidencia de validación en el VPS

Fecha de corte: 2026-08-17, zona `America/Tegucigalpa`.

- Compose validado.
- Build de `platform-api` aprobado.
- Build TypeScript/Vite de `ops-web` aprobado: 1,614 módulos transformados.
- Pruebas backend focalizadas: 11 aprobadas.
- Pruebas de guía interactiva: 3 aprobadas.
- Migración aplicada al PostgreSQL activo: `0026_counter_item_requests`.
- Datos preservados después del despliegue: 15 usuarios, 125 artículos y 8 OTs.
- Navegación servida: `/tallerv1/mostrador` respondió HTTP 200.
- API sin sesión respondió 401, como corresponde.
- Navegador autenticado comprobó una pieza con saldo 23 habilitada y piezas con saldo 0 deshabilitadas.
- Solicitud real de demostración creada con HTTP 201 y visible en Compras con estado `NEW`.
- GET de solicitudes respondió HTTP 200 tanto en mostrador como en Compras.

## Respaldo y reversión

- Fuente previa: `/opt/smartdiag504-backups/20260817-181909/counter-tour-source.tgz`.
- Base previa: `/opt/smartdiag504-backups/20260817-182600/pre-counter-tour.dump`.
- No se reinició Coolify, Traefik, gateway, ERPNext ni servicios ajenos.

## Observaciones de prueba

- Durante la prueba se intentaron dos credenciales antiguas de caja y generaron respuestas 400; después se usó el propietario de demostración y el flujo quedó validado. Los errores de consola registrados corresponden a esos intentos y al 401 inicial usado por la pantalla para detectar una sesión inexistente; no aparecieron errores nuevos al consultar inventario, agregar al carrito o crear la solicitud.
- SMTP continúa siendo una configuración externa: las autorizaciones muestran correctamente `PENDING_EMAIL_CONFIGURATION` mientras no se definan las credenciales de correo.
