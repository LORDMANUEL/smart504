# ADR-0011: acceso de cliente administrado

Fecha: 2026-08-13

## Decisión

No construir ni operar un servidor OAuth propio. Para clientes se recomienda Clerk con su pantalla de acceso alojada y componentes preconstruidos. La primera etapa debe habilitar solamente correo con código de un solo uso. Cada persona recibe el identificador único del proveedor y SmartDiag504 lo enlaza con su registro de cliente.

Las redes sociales son opcionales y posteriores. En desarrollo Clerk ofrece conexiones sociales compartidas, pero en producción cada red exige sus credenciales oficiales. Por eso no se presentará Google como requisito ni se mezclará el acceso de clientes con el Hub Social de atención.

## Motivos

- El cliente no debe recordar otra contraseña: recibe un código por correo.
- Recuperación, verificación, sesiones y protección del formulario quedan en un servicio especializado.
- SmartDiag504 almacena el identificador externo estable, no contraseñas de correo o redes.
- Se puede agregar Facebook, Apple u otra conexión después, sin cambiar las tablas de taller.
- El Hub Social continúa siendo para mensajes y atención; no para autenticación.

## Requisitos para activarlo

1. Crear una instancia de Clerk propiedad de SmartDiag504.
2. Entregar `VITE_CLERK_PUBLISHABLE_KEY` y `CLERK_SECRET_KEY` como secretos de Coolify.
3. Configurar `accounts.taller.nexusmedi.org` o usar inicialmente el dominio alojado del proveedor.
4. Añadir `external_identity_id` único al cliente y validar el JWT en la API.
5. Migrar la cuenta demo actual después de probar cierre de sesión, expiración y recuperación.

No se instala el SDK sin esas claves porque dejaría el login actual bloqueado. Referencias oficiales: [opciones de acceso por correo](https://clerk.com/docs/guides/configure/auth-strategies/sign-up-sign-in-options), [conexiones sociales](https://clerk.com/docs/guides/configure/auth-strategies/social-connections/overview) y [vinculación de cuentas](https://clerk.com/docs/guides/configure/auth-strategies/social-connections/account-linking).
