# 06 — IA, ChromaDB, Redis y sistema de alertas

## Objetivo de la IA

La IA debe reducir tiempo de búsqueda, ordenar evidencia y explicar información; no reemplazar el criterio técnico ni ejecutar movimientos comerciales críticos.

## Casos de uso permitidos

- Resumir el motivo de ingreso y el historial del vehículo.
- Sugerir un checklist de diagnóstico a partir de síntomas y documentación aprobada.
- Recuperar casos similares, manuales, boletines y procedimientos.
- Estructurar notas de voz del técnico.
- Generar borradores de explicación al cliente.
- Comparar cotización actual con trabajos previos.
- Detectar datos faltantes o contradicciones en la OT.
- Consultar KPIs gerenciales con herramientas de solo lectura.
- Proponer próximos mantenimientos basados en reglas configuradas.

## Acciones prohibidas sin aprobación determinística

- Confirmar un diagnóstico como hecho sin evidencia y técnico responsable.
- Aprobar o rechazar una cotización.
- Cambiar precios, costos, impuestos o descuentos.
- Reservar/consumir inventario, emitir factura o registrar pago.
- Cerrar una OT o liberar un vehículo.
- Presentar una recomendación de seguridad como certeza cuando la fuente no lo respalda.

## Arquitectura RAG

1. Documento fuente aprobado.
2. Antivirus, extracción y normalización.
3. Clasificación por fabricante, modelo, año, motor, sistema, idioma y versión.
4. División en fragmentos con metadatos y checksum.
5. Embedding por proveedor configurable.
6. Colección ChromaDB aislada por cliente y ACL.
7. Recuperación híbrida: filtros estructurados + similitud semántica.
8. Respuesta del LLM con citas a documentos y advertencias.
9. Registro de pregunta, fuentes, modelo, versión, latencia y resultado.

## Fuentes de conocimiento

- Manuales y procedimientos con derecho de uso.
- Boletines técnicos y campañas autorizadas.
- Catálogo de servicios y políticas de SmartDiag504.
- Casos cerrados y anonimizados con calidad confirmada.
- DTC y notas internas validadas.
- Políticas de garantía, recepción y seguridad.

Los casos de una empresa no se mezclan con otra sin consentimiento y anonimización expresa.

## Gateway de modelos

Interfaz agnóstica para modelos locales o externos. Cada proveedor define:

- credenciales secretas;
- modelos permitidos;
- límites de costo y tokens;
- regiones y retención;
- herramientas disponibles;
- política de datos sensibles.

## Seguridad de herramientas

- Identidad del usuario propagada al LLM.
- Herramientas filtradas por rol.
- Lectura por defecto.
- Escrituras como comandos explícitos, validados y confirmados.
- Argumentos y resultados auditados.
- Prevención de prompt injection en documentos recuperados.
- Redacción de secretos y datos innecesarios.

## Redis

Usos:

- cola de workers;
- caché de catálogo/disponibilidad con TTL;
- rate limiting;
- locks cortos;
- pub/sub o streams para tiempo real;
- sesiones efímeras;
- deduplicación temporal de eventos.

Nunca será la única copia de una OT, aprobación, movimiento, factura o pago.

## Catálogo inicial de eventos

- `APPOINTMENT_CREATED`
- `VEHICLE_CHECKED_IN`
- `WORK_ORDER_CREATED`
- `INSPECTION_COMPLETED`
- `DIAGNOSIS_RECORDED`
- `CRITICAL_SAFETY_FINDING_RECORDED`
- `ESTIMATE_SENT`
- `ESTIMATE_APPROVED`
- `ESTIMATE_REJECTED`
- `CHANGE_ORDER_REQUIRED`
- `PART_REQUEST_CREATED`
- `PART_RESERVED`
- `PART_ISSUED`
- `PART_RECEIPT_CONFIRMED`
- `PART_SHORTAGE_DETECTED`
- `TECHNICIAN_ASSIGNED`
- `WORK_STARTED`
- `WORK_PAUSED`
- `TECHNICIAN_IDLE_DETECTED`
- `QUALITY_CHECK_FAILED`
- `QUALITY_CHECK_PASSED`
- `INVOICE_POSTED`
- `PAYMENT_RECEIVED`
- `VEHICLE_READY`
- `VEHICLE_DELIVERED`
- `WARRANTY_CLAIM_OPENED`
- `MAINTENANCE_DUE`
- `INTEGRATION_RECONCILIATION_FAILED`

## Reglas de alerta prioritarias

- OT sin actividad más allá del umbral por estado.
- Fecha prometida en riesgo.
- Cotización pendiente de aprobación.
- Trabajo adicional realizado sin enmienda aprobada.
- Repuesto solicitado sin reserva o entrega.
- Técnico sin trabajo durante horario operativo.
- Vehículo en bahía sin operación activa.
- Control de calidad fallido o pendiente.
- Factura pendiente para vehículo listo.
- Pago pendiente para entrega.
- Diferencia de caja.
- Bajo stock o pedido especial atrasado.
- Reincidencia dentro de garantía.
- Evento de integración agotó reintentos.

Cada alerta tendrá `event_key` estable, severidad, propietario, SLA, acuse, escalamiento, resolución y evidencia.
