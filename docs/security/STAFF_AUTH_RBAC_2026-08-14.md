# Identidad del personal y permisos RBAC

Fecha: 14 de agosto de 2026.

## Problema corregido

El panel operativo utilizaba una sola clave administrativa guardada en `sessionStorage`. Ese mecanismo se conserva exclusivamente como recuperación temporal del propietario, pero deja de ser el acceso normal del personal.

## Arquitectura aplicada

- Proveedor/biblioteca: FastAPI Users 15.0.5, evitando implementar manualmente hashing, emisión de tokens y validación de credenciales.
- Transporte: cookie `smartdiag_staff_session` con `HttpOnly`, `Secure` en staging/producción, `SameSite=Lax`, ruta `/` y duración máxima configurable de ocho horas.
- Contraseñas: hashing Argon2 administrado por `pwdlib` a través de FastAPI Users.
- Autorización: RBAC centralizado en el servidor. La interfaz oculta módulos no autorizados, pero la decisión final siempre la toma el API.
- Persistencia: tablas `staff_users` y `staff_access_events`, creadas por la migración `0011_staff_identity_rbac`.
- Alcance organizacional: cada usuario conserva `organization_id` y `branch_id` para separar empresas y sucursales en las siguientes migraciones.

## Roles

| Rol | Alcance inicial |
|---|---|
| OWNER | Todos los módulos y administración de usuarios |
| ADMIN | Todos los módulos y administración de usuarios |
| MANAGER | Operación, caja, bodega, CRM, documentos, reportes y configuración |
| TECHNICIAN | OT, bahías, catálogo técnico y documentos |
| CASHIER | OT, cotizaciones, caja y documentos |
| WAREHOUSE | OT, catálogo, bodega y documentos |
| RECEPTION | OT, citas, pedidos, cotizaciones y CRM |
| MARKETING | CRM, publicidad y Hub Social |
| AUDITOR | Lectura de operación, caja, bodega, procesos y reportes |

El auditor no puede ejecutar solicitudes de escritura. Los roles pueden ampliarse con permisos explícitos por usuario sin modificar el código.

## Flujos funcionales

1. El propietario entra temporalmente con la clave de recuperación existente.
2. Abre `/tallerv1/personal`.
3. Crea una cuenta individual con correo, contraseña inicial, código, cargo, teléfono y rol.
4. El empleado inicia sesión con correo y contraseña.
5. El navegador recibe una cookie que JavaScript no puede leer.
6. El menú muestra sólo los módulos del rol y el API rechaza accesos directos no autorizados con HTTP 403.
7. El administrador puede cambiar el rol, suspender o reactivar la cuenta.
8. Cada inicio exitoso queda en la bitácora con usuario, fecha, resultado y acción.

## Endpoints

- `POST /api/v1/staff/auth/login`
- `POST /api/v1/staff/auth/logout`
- `GET /api/v1/staff/me`
- `GET/POST /api/v1/staff/users`
- `PATCH /api/v1/staff/users/{id}`
- `GET /api/v1/staff/access-events`

## Límite pendiente

La columna organizacional ya existe, pero la política PostgreSQL RLS no se activará mientras la aplicación siga conectándose con el mismo usuario de administración de base. Activarla antes de separar un rol de migración y un rol limitado de aplicación produciría una falsa sensación de aislamiento. Esa separación forma parte del bloque multiempresa posterior.
