# 03 — Módulos y flujos operativos

## 1. Organización y seguridad

- Empresas, sucursales, talleres, bahías, bodegas, cajas y centros de costo.
- Usuarios, roles, equipos, turnos y sustituciones.
- Técnicos con especialidades, certificaciones, nivel y costo/hora.
- Matriz de segregación de funciones.

## 2. Clientes y vehículos

- Persona natural o jurídica, contactos, RTN y preferencias de comunicación.
- Vehículo con VIN, placa, marca, modelo, versión, año, motor, transmisión, color y combustible.
- Kilometraje histórico con origen y fotografía opcional.
- Propietario actual e historial de propietarios autorizados.
- Alertas por duplicidad de VIN, placa o teléfono.

## 3. Reservas y citas

- Reserva por portal, teléfono, WhatsApp o recepción.
- Motivo de visita, síntomas, servicio solicitado, vehículo y disponibilidad.
- Capacidad por taller, bahía, especialidad y técnico.
- Confirmación, recordatorio, reprogramación, no-show y lista de espera.

## 4. Recepción e ingreso

- Búsqueda por VIN, placa, teléfono o cliente.
- Lectura de kilometraje, combustible, accesorios/llaves y daños visibles.
- Checklist configurable, fotografías con hora y usuario.
- Síntoma en palabras del cliente, condición de llegada y autorización de diagnóstico.
- Firma y aceptación de términos.
- Etiqueta QR de la OT/vehículo.

## 5. Orden de trabajo

La OT es el expediente operativo central. Debe mostrar en una sola línea de tiempo:

- por qué llegó el vehículo;
- inspección inicial;
- diagnóstico y DTC;
- cotizaciones y aprobaciones;
- responsables y tiempos;
- repuestos solicitados, entregados, consumidos y devueltos;
- actividades realizadas;
- control de calidad y prueba;
- factura, pago y entrega;
- garantías o reincidencias posteriores.

## 6. Diagnóstico técnico

- Problema reportado, síntoma reproducido y condiciones de prueba.
- DTC con módulo, estado, captura, freeze frame y archivo de escáner.
- Pruebas efectuadas, mediciones y valores esperados/reales.
- Hallazgos, causa probable, causa confirmada y riesgo de seguridad.
- Trabajo recomendado, trabajo urgente y trabajo diferible.
- Casos similares recuperados por IA, siempre con fuentes.

## 7. Cotización

- Versiones inmutables.
- Líneas de mano de obra, repuesto, consumible, servicio externo, cargo y descuento.
- Cantidad, tarifa, impuesto, costo estimado, precio y margen.
- Repuesto original, alternativo o suministrado por cliente.
- Aprobación total o por línea.
- Enmienda obligatoria cuando cambia el alcance aprobado.
- Firma, fecha, canal, IP/dispositivo y evidencia de aprobación.

## 8. Planificación y técnicos

- Una OT puede tener varios trabajos y varios técnicos.
- Asignación por habilidad, disponibilidad, bahía y prioridad.
- Tiempo planificado, reloj real, pausas justificadas y tiempo no productivo.
- Mano de obra vendida frente a horas reales y costo técnico.
- Traspaso controlado entre técnicos.
- Trabajo paralelo con bloqueo para actividades incompatibles.

## 9. Repuestos y bodega

Flujo normal:

`Solicitud → validación → reserva → picking → entrega → recibido por técnico → consumo o devolución → movimiento ERP`

Reglas:

- El técnico solicita; bodega entrega; quien recibe confirma.
- No se consume una cantidad mayor a la entregada.
- La devolución referencia la entrega original.
- Repuesto especial no disponible genera requisición de compra.
- Sustituciones requieren aprobación técnica y comercial cuando cambian precio o especificación.
- Toda pieza retirada puede marcarse como devuelta al cliente, desechada, enviada a garantía o retenida como core.

## 10. Compras

- Solicitud de compra originada por OT, mínimos o reposición.
- Comparación de proveedores, plazo, costo, disponibilidad y garantía.
- Orden de compra y recepción en ERPNext.
- Asignación de la recepción a la OT pendiente.
- Control de pedido especial y anticipo del cliente.

## 11. Control de calidad

- Checklist por tipo de servicio.
- Verificación de torque, fugas, DTC, funciones, niveles y limpieza.
- Prueba de carretera con ruta, kilometraje inicial/final y resultado.
- Fallo de QC crea retrabajo y no permite pasar a entrega.
- Firma del inspector y liberación independiente cuando aplique.

## 12. Facturación, caja y pagos

- La OT aprobada genera documentos comerciales en ERPNext.
- Caja usa apertura, movimientos, pagos por método, retiros, gastos autorizados y cierre.
- Diferencia de caja requiere explicación y aprobación.
- Factura, ticket, notas de crédito y otros documentos se generan conforme a la configuración fiscal validada.
- Pagos parciales, anticipos, crédito autorizado y saldo pendiente.
- No entregar vehículo con saldo vencido salvo autorización registrada.

## 13. Venta de repuestos y e-commerce

- Venta de mostrador por POS.
- Catálogo online con precio y disponibilidad actualizados desde ERPNext.
- Búsqueda por número de parte, descripción, marca, modelo, año y compatibilidad.
- Compatibilidad por VIN marcada como confirmada, probable o requiere validación.
- Reserva para recoger, envío, pedido especial o solicitud de cotización.
- No prometer existencia con caché vencida; se valida al confirmar la orden.

## 14. Mantenimiento y retención

- Planes por fecha, kilometraje, horas o condición.
- Próximo mantenimiento calculado desde la entrega y odómetro.
- Recordatorios con consentimiento y trazabilidad.
- Campañas por modelo, VIN, servicio o cliente.
- Recomendaciones rechazadas quedan visibles para la próxima visita.

## 15. Garantía y comeback

- Garantía ligada a líneas de mano de obra y repuestos.
- Reclamo identifica OT original, síntoma y causal.
- Clasificación: falla de pieza, instalación, diagnóstico, uso, evento no relacionado o cortesía.
- Costo de retrabajo separado del ingreso original.
- Indicador de reincidencia por técnico, servicio, pieza y vehículo.

## 16. Flujo completo de la OT

1. Reserva o llegada sin cita.
2. Recepción e inspección.
3. Apertura de OT y autorización de diagnóstico.
4. Diagnóstico y evidencia.
5. Cotización versión N.
6. Aprobación/rechazo por línea.
7. Reserva o compra de repuestos.
8. Planificación de bahía y técnicos.
9. Ejecución, tiempos y consumo.
10. Enmienda si aparece trabajo adicional.
11. Control de calidad y prueba.
12. Facturación y pago.
13. Entrega con firma y recomendaciones.
14. Cierre, garantía y próximo mantenimiento.

Ver `../diagrams/work-order-flow.mmd` y `../contracts/work-order-state-machine.yaml`.
