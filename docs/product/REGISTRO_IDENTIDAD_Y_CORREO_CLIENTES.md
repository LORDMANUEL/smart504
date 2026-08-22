# Registro, identidad y correo de clientes

## Flujo funcional

1. El cliente abre `/lading/loginclie` y selecciona **Crear cuenta**.
2. Registra nombre, teléfono, correo personal y contraseña. El usuario puede indicarse o se genera automáticamente.
3. La plataforma crea el cliente y su cuenta dentro de la organización `SMARTDIAG504`, registra el evento de auditoría y encola el aviso de bienvenida.
4. El cliente ingresa con su correo personal. La sesión se guarda en una cookie `HttpOnly`, `Secure` y `SameSite=Lax`; no se guarda un token en `localStorage`.
5. Se reserva una dirección única `<usuario>@smartdiag504.com`. El correo personal continúa siendo el destino de recuperación y notificaciones.

## Estados del buzón

- `PENDING_CONFIGURATION`: la identidad quedó reservada, pero el dominio o el servicio de correo todavía no permiten aprovisionar el buzón.
- `QUEUED`: el aprovisionamiento está habilitado y quedó pendiente de ejecución por el conector de correo.
- `ACTIVE`: debe asignarse únicamente después de crear el buzón y verificar envío, recepción, cuota y autenticación.
- `FAILED`: el conector no pudo completar el aprovisionamiento; debe conservar el error en los logs operativos sin guardar contraseñas.

En el VPS actual el dominio está en revisión. No se debe marcar un buzón `ACTIVE` ni prometer entrega externa hasta validar MX, PTR, SPF, DKIM y DMARC.

## Acceso con redes sociales

La configuración se administra en ERPNext/Frappe mediante **Social Login Key**. SmartDiag504 muestra el acceso social solamente cuando `FRAPPE_SOCIAL_LOGIN_ENABLED=true`. Google, Meta u otro proveedor autentican al cliente mediante OAuth/OIDC; SmartDiag504 nunca recibe ni guarda la contraseña de la red social.

Antes de habilitarlo se debe configurar en ERPNext cada proveedor, su URI de retorno HTTPS y las credenciales entregadas por el proveedor. Después se valida vinculación por correo verificado, prevención de cuentas duplicadas, cierre de sesión y revocación.

## Variables

- `MANAGED_MAIL_DOMAIN=smartdiag504.com`
- `MANAGED_MAILBOX_ENABLED=false` mientras no exista aprovisionador verificado.
- `FRAPPE_SOCIAL_LOGIN_ENABLED=false` mientras no existan proveedores OAuth configurados.
- `PUBLIC_CLIENT_REGISTRATION_LIMIT_PER_MINUTE=3`

## Prueba de aceptación

1. Crear una cuenta con correo personal único.
2. Confirmar HTTP 201 y que la respuesta incluya usuario, correo reservado y estado de buzón.
3. Repetir el correo y confirmar HTTP 409.
4. Iniciar sesión con el correo personal y confirmar que `/api/v1/client-auth/session` devuelve la identidad creada.
5. Confirmar que existe `CLIENT_ACCOUNT_CREATED` en el mapa de flujos y una entrega `CLIENT_ACCOUNT_CREATED` en la cola de notificaciones.
6. Confirmar que los botones sociales permanecen ocultos si ERPNext no tiene OAuth habilitado.

## Evidencia VPS de pruebas — 2026-08-22

- Despliegue Coolify: `yiwhnz0e8w9d22oxgtcf3shb`, estado `finished`.
- Imagen API servida: digest `sha256:75619527c06e202f673826c87cadca38681244f62b20ef1a8f6024c6ffc8120d`.
- Esquema PostgreSQL: `0033_client_self_registration (head)`.
- Salud integral: `/ready` respondió HTTP 200.
- Opciones de registro: autorregistro activo; buzón administrado y login social desactivados hasta configurar sus proveedores.
- Alta nueva: HTTP 201; usuario y dirección corporativa únicos; estado `PENDING_CONFIGURATION`.
- Correo duplicado: HTTP 409.
- Inicio de sesión con el correo personal: HTTP 204; lectura de sesión: HTTP 200.
- Auditoría: último evento `CLIENT_ACCOUNT_CREATED|SUCCESS`.
- Notificación: entrega `CLIENT_ACCOUNT_CREATED|PENDING`, pendiente de SMTP definitivo.
- Interfaz pública: el bundle servido contiene **Crear cuenta de cliente**.

Los datos de aceptación son desechables y no constituyen credenciales de entrega. No se registran contraseñas en este documento.
