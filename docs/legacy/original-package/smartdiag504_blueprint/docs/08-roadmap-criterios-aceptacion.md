# 08 — Roadmap por gates y criterios de aceptación

No se organiza por promesas de fechas sino por gates verificables. Cada gate debe cerrar sus criterios antes de expandir el alcance.

## Gate 0 — Decisiones y procesos

Entregables:

- arquitectura aprobada;
- mapa real del proceso de SmartDiag504;
- catálogo de sucursales, talleres, bodegas, cajas y roles;
- política de precios, descuentos, garantías y anticipos;
- decisión de licencia del producto;
- validación fiscal hondureña con contador/especialista;
- decisión de ERPNext v16 y estrategia de despliegue.

Criterio de salida: no quedan dos fuentes de verdad ni responsabilidades ambiguas.

## Gate 1 — Fundación técnica

- monorepo, CI, entornos y gestión de secretos;
- autenticación, roles, auditoría y aislamiento;
- PostgreSQL, Redis, almacenamiento y observabilidad;
- contratos OpenAPI/eventos;
- migraciones y datos demo;
- adaptador ERP con sandbox y pruebas de idempotencia.

Criterio de salida: crear una organización, sucursal, usuario y conexión ERP sin intervención manual en base de datos.

## Gate 2 — Operación mínima del taller

- cliente y vehículo;
- cita y recepción;
- inspección y evidencia;
- OT y estados;
- diagnóstico;
- cotización versionada y aprobación;
- asignación y tiempos;
- solicitud/entrega de repuestos;
- control de calidad y entrega;
- historial del vehículo.

Criterio de salida: una OT demo recorre todo el flujo con auditoría y sin editar datos históricos.

## Gate 3 — ERP, bodega, caja y rentabilidad

- sincronización de artículos, precios, impuestos y disponibilidad;
- cotización aprobada a documento comercial;
- compras y recepciones ligadas a OT;
- consumo/devolución de repuestos;
- facturación, pagos, POS y cierres;
- conciliación diaria;
- margen por OT y reportes gerenciales.

Criterio de salida: los totales de OT, stock, factura, pago y libro mayor coinciden en escenarios normales, parciales, anulaciones y devoluciones.

## Gate 4 — Cliente, landing y e-commerce

- landing pública;
- reserva online;
- portal de cliente;
- aprobación por línea;
- documentos y estado;
- catálogo, compatibilidad, carrito/reserva y pedido especial;
- integración de pago/mensajería elegida;
- SEO, privacidad y analítica.

Criterio de salida: un cliente reserva, aprueba y compra sin acceder a datos ajenos ni generar promesas falsas de stock.

## Gate 5 — Alertas e IA

- catálogo de eventos;
- reglas operativas y escalamiento;
- ingesta documental y ACL;
- RAG con fuentes;
- asistente de técnico, asesor y gerente;
- evaluación de respuestas y costo;
- herramientas de solo lectura y aprobaciones.

Criterio de salida: la IA responde con fuentes, respeta permisos y no puede ejecutar acciones financieras o de inventario fuera del flujo autorizado.

## Gate 6 — Producto comercial

- instalación automatizada por cliente;
- backup/restore y actualización;
- licenciamiento y planes;
- telemetría técnica opt-in;
- documentación, onboarding y soporte;
- hardening y pentest;
- carga, recuperación y continuidad;
- SLA y matriz de soporte.

Criterio de salida: una instalación limpia puede desplegarse, configurarse, probarse, respaldarse, restaurarse y actualizarse de forma repetible.

## Primer backlog de epics

1. Identidad, organización y permisos.
2. Cliente/vehículo/historial.
3. Citas y recepción.
4. OT y máquina de estados.
5. Diagnóstico/evidencia.
6. Cotización/aprobación.
7. Técnicos/tiempos/bahías.
8. Repuestos/bodega/compras.
9. QC/entrega/garantía.
10. ERP/caja/fiscalidad.
11. Portal/landing/e-commerce.
12. Alertas/IA/reportes.
13. Seguridad/observabilidad/operación.

## Criterios globales de aceptación

- No hay duplicados por reintento.
- Toda transición tiene actor, hora y motivo.
- Todo total monetario es reproducible.
- Toda existencia mostrada indica fuente y frescura.
- Toda aprobación conserva la versión exacta.
- Todo consumo se vincula a entrega y movimiento ERP.
- Todo documento fiscal se vincula a la OT o venta.
- Toda respuesta IA muestra fuentes o declara ausencia de evidencia.
- Toda acción crítica exige permiso y queda auditada.
