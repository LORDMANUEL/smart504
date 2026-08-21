# SmartDiag504 P0 — implementación y evidencia VPS

Fecha de corte: 2026-08-14

## Resultado

Se desplegó una base P0 para que SmartDiag504 sea la capa operativa y ERPNext/Beveren la fuente autoritativa. La demostración dejó de depender únicamente de registros locales para representar la integración ERP.

## Implementado

- aislamiento por organización en modelos y consultas principales;
- empresa, sucursal y actor obtenidos desde sesión autenticada;
- estados de sincronización ERP y outbox con reintentos;
- ocho OTs demo conciliadas con ocho Service Orders ERP;
- ERPNext, Frappe, HRMS, Beveren y la aplicación SmartDiag en el VPS;
- MFA TOTP, bloqueo por intentos y revocación de sesiones;
- fotografías de OT privadas y protegidas, utilizables en diagnóstico PDF;
- cola persistente de notificaciones con estado bloqueado cuando no hay proveedor;
- plantillas HTML/CSS versionables para documentos y salida PDF;
- guía interactiva por rol, accesos y creación de usuarios.

## Evidencia de ejecución

- readiness estricto: base de datos, Valkey, Frappe, esquema, IA y seguridad en estado `ok`;
- migraciones aplicadas hasta `0020`;
- sincronización OT: `8/8` con referencia ERP;
- respaldo nativo Frappe creado y restaurado aisladamente;
- restauración verificó 896 tablas y eliminó después la base temporal;
- navegación servida validada en 19 módulos sin páginas en blanco;
- landing, tienda, filtro VIN, portal cliente, Kanban y detalle OT inspeccionados desde navegador.
- guía interactiva: 18/18 pruebas del frontend y compilación aprobadas en el VPS;
- URL `/tallerv1/guias` validada con sesión real, accesos visibles y progreso persistente de 0% a 25%;
- `ops-web` y `gateway` recreados de forma aislada y saludables, sin reiniciar el proxy compartido.

## Límites que no deben declararse terminados

- certificación fiscal SAR/CAI y rangos productivos;
- hardware real: datáfono, gaveta, lector e impresora térmica/fiscal;
- correo, WhatsApp, SMS, Meta y push sin credenciales/proveedor;
- stock ledger ERP integral para todos los movimientos de bodega;
- contabilidad, compras, importaciones, nómina HRMS y usados completos;
- aislamiento multiempresa certificado por pruebas E2E de todas las rutas;
- alta disponibilidad con conmutación comprobada.

## Regla de validación desde este corte

No se ejecutan pruebas ni compilaciones en la PC local. Todo cambio se sincroniza al VPS de pruebas, se compila dentro de contenedor, ejecuta sus gates allí y se valida sobre la URL servida. No se reinicia la infraestructura compartida de Coolify.
