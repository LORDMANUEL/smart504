# Matriz funcional SmartDiag504 — 13 de agosto de 2026

## Objetivo de esta entrega

Completar el circuito operativo que conecta cita, orden de trabajo (OT), cotización, repuestos, cobro y cierre de caja. La cita pública y la cita creada dentro de la cuenta del cliente se guardan como fuentes distintas para poder comparar conversión, abandono y tiempo de atención.

## Flujos implementados

### Cita pública

1. El visitante solicita contacto desde `/lading`.
2. La reserva se guarda con fuente `WEB` y estado `NEW`.
3. Recepción la contacta, confirma o cancela desde `/tallerv1/citas`.
4. Los cambios producen eventos del módulo `RECEPTION`.

### Cita autenticada

1. El cliente inicia sesión en `/lading/loginclie`.
2. Selecciona vehículo, fecha, servicio y uno de los horarios disponibles.
3. La cita se guarda con `customer_id`, `vehicle_id`, `scheduled_at`, fuente `CLIENT_PORTAL` y estado `CONFIRMED`.
4. El horario ocupado deja de estar disponible y el evento `CLIENT_PORTAL/APPOINTMENT_CREATED` alimenta el mapa de flujo.

### Cotización, POS y caja

1. En `/tallerv1/cotizaciones` se selecciona la OT y se agregan líneas de mano de obra, repuesto u otro cargo.
2. Cada línea conserva código, descripción, cantidad, costo y precio de venta. La cotización calcula subtotal, descuento, impuesto y total.
3. El estado avanza `DRAFT → SENT → APPROVED` o `REJECTED` y queda reflejado en la OT.
4. Caja abre un turno con fondo inicial. No se admite un cobro sin turno abierto.
5. El cobro exige OT y cotización aprobada. Tarjeta/POS y transferencia exigen referencia; efectivo no captura datos de tarjeta.
6. El cierre calcula efectivo esperado como fondo inicial más cobros en efectivo y registra conteo y diferencia.
7. El reporte del turno desglosa efectivo, tarjeta/POS, transferencia, total y recibos.

## Estado por módulo

| Módulo | Ruta | Estado verificable en esta entrega | Siguiente dependencia real |
|---|---|---|---|
| Landing promocional | `/lading` | Funcional; formulario público separado | Analítica avanzada de campañas |
| Acceso y portal cliente | `/lading/loginclie`, `/lading/cliente` | Login demo, vehículo, repuestos, documentos y calendario autenticado | Proveedor de identidad social/correo en producción |
| Tienda | `/lading/repuestos` | Catálogo, compatibilidad y solicitud persistida | Pago en línea y sincronización ERP de producción |
| Citas/recepción | `/tallerv1/citas` | Distingue fuente pública y cliente autenticado; cambios persistidos | Reglas de capacidad por técnico/bahía |
| Kanban/OT | `/tallerv1/kanban` | Estados, detalle, diagnóstico y solicitud de repuesto | Firma de aprobación del cliente |
| Cotizaciones | `/tallerv1/cotizaciones` | Configuración completa por OT y aprobación persistida | Plantilla fiscal/legal definitiva |
| Bodega | `/tallerv1/bodega` | Picking, ubicación y entrega cargada a OT | Lotes, series y conteo cíclico |
| Caja/POS | `/tallerv1/caja` | Apertura, pagos, referencias, recibos, cierre, cuadre y reporte | Integración con adquirente/datáfono y facturación SAR |
| Administración | `/tallerv1/3gj` | Directorio de rutas y acceso a módulos | RBAC granular por empleado |
| Personal y accesos | `/tallerv1/personal` | Cuentas por empleado, cookie segura, roles, suspensión y bitácora | MFA y recuperación de contraseña por correo |
| Publicidad/TV | `/tallerv1/publicida`, `/tallerv1/publicida/tv` | Campaña demo y pantalla | Calendario editorial y aprobaciones |
| Mapa de flujos | `/tallerv1/flujos` | Eventos persistidos desde cita hasta cobro | Embudos por periodo, SLA y cohortes |
| Hub Social | `/tallerv1/social` | Inventario de canales y controles humanos | Credenciales/API de Meta y WhatsApp Business |
| Documentos e impresion | `/tallerv1/documentos` | Plantillas HTML/CSS versionadas, publicacion, PDF e historial SHA-256 | Configuracion fiscal SAR y pruebas con impresoras fisicas |
| IA/RAG | API y asistente público | Flujo existente conservado | Medición de calidad y corpus real autorizado |

## Decisiones y límites

- Un estado HTTP saludable no se considera prueba del flujo; se validan llamadas autenticadas, persistencia y vistas servidas.
- El modo POS registra el resultado y referencia de una operación externa. No se simula una conexión bancaria ni se almacenan datos sensibles de tarjetas.
- La facturación fiscal hondureña no se declara completada sin datos de CAI, rangos, RTN y reglas del negocio.
- Meta, WhatsApp, Google u otro acceso social requieren cuentas, consentimiento y credenciales del propietario; no se inventan integraciones ni secretos.
- Los comentarios se concentran en decisiones y reglas no obvias. Comentar literalmente cada línea reduciría legibilidad y no sustituye pruebas, tipos ni documentación de arquitectura.

## Pruebas locales

- API: 55 pruebas aprobadas en la entrega de portal, documentos, pedidos y campañas.
- Operaciones: 12 pruebas aprobadas y compilación de producción aprobada, incluido el reporte visible del último turno cerrado.
- Web pública: 5 pruebas aprobadas y compilación de producción aprobada.
- Casos nuevos cubiertos: reserva autenticada, exclusión de horario ocupado, cotización y aprobación, apertura de caja, pago POS con referencia, resumen y cierre sin diferencia.
