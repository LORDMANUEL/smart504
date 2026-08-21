# Validación servida: RR. HH., nómina y documentos

Fecha: 17 de agosto de 2026  
Entorno: VPS de pruebas `taller.nexusmedi.org`  
Regla: no se ejecutaron builds, migraciones ni pruebas en la PC local.

## Resultado

La migración activa es `0025_hn_payroll`. La API, operaciones, gateway y ERPNext/HRMS quedaron saludables después del despliegue.

### Pruebas automatizadas

- API completa antes del cierre: 89 pruebas aprobadas.
- Frontend de operaciones: 18 pruebas aprobadas.
- Prueba focalizada de políticas Honduras, prestaciones, código automático, autoservicio y privacidad: 2 pruebas aprobadas.
- Build de producción API y operaciones: aprobado; Vite transformó 1,613 módulos.
- Navegación servida: 26 rutas operativas, 5 submódulos RRHH, 4 submódulos del técnico, centro documental, guía, TV y 4 rutas públicas; todas sin página blanca, overlay ni error de consola.

### Operación empresarial servida

Se creó información de prueba equivalente a una operación administrativa:

1. proveedor sincronizado;
2. orden de compra aprobada;
3. recepción parcial y final;
4. importación con flete y aduana asignados;
5. empleado y contrato sincronizados;
6. asistencia y hora extra aprobada;
7. nómina aprobada y sincronizada con ERPNext/HRMS;
8. voucher HTML privado e imprimible;
9. entrada, salida y solicitud de permiso desde autoservicio;
10. plantilla HTML importada y exportada.

Resultado final del autoservicio: código del acceso y contrato iguales; nómina `APPROVED:SYNCED`; voucher `HTML_PRINT_OK`; asistencia registrada; permiso `PENDING` para revisión.

### Contador, impresión y seguridad

- Inicio de sesión con rol contador: aprobado.
- Activar fiscalidad sin confirmación del contador: rechazado con `422`.
- Serie fiscal de prueba: activada y luego restaurada a su estado anterior.
- PDF de factura: válido.
- vista térmica de 80 mm: válida.
- evidencia OT: anónimo `401`, contador `403`, usuario autorizado `200`, con `Cache-Control: private, no-store`.
- transporte SMTP contra servidor efímero: un mensaje recibido.
- archivo SQL local más reciente: integridad gzip aprobada.

## Correcciones encontradas durante la prueba

1. Una edición salarial mensual no actualizaba la base de pago: corregido.
2. El autoservicio podía seleccionar un contrato coincidente antes que el contrato enlazado: corregido; se prioriza `staff_user_id`.
3. Acceso y contrato podían generar códigos automáticos distintos: corregido; el contrato reutiliza el código del usuario enlazado.
4. El botón del voucher imprimía toda la pantalla: corregido; ahora abre un documento HTML privado individual.
5. La prueba visual necesitaba esperar la carga real de la guía: corregido el test para validar el contenido servido y no un estado transitorio.

## Límites que no deben declararse certificados

- No había impresora, gaveta, lector ni datáfono físicos conectados; sólo se validó la salida de software.
- Las tasas y techos IHSS/RAP/seguro deben cargarlos y aprobarlos el contador/RRHH con fuente y vigencia; no se inventaron valores.
- SMTP quedó validado como transporte, pero el proveedor y dominio reales deben configurarse como secretos.
- Este VPS conserva respaldo local de reversión. El respaldo externo pertenece a la infraestructura futura de producción.
- La prueba fiscal no sustituye certificación SAR ni autorización de CAI/rangos.
