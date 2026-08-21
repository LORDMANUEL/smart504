# 05 — UX/UI y mapa de pantallas

## Principios de experiencia

- Interfaz de trabajo, no un conjunto de formularios genéricos.
- La OT es el centro; no se obliga al usuario a saltar entre módulos para entender el caso.
- Acciones críticas visibles según el rol y el estado.
- Evidencia antes que texto libre cuando corresponda.
- Teclado, escáner, cámara y móvil como entradas de primera clase.
- Estados, bloqueos y pendientes inequívocos.
- Diseño accesible, con contraste, foco, tamaños táctiles y uso sin depender solo del color.
- Tokens de marca configurables; la paleta definitiva debe tomarse del logo y manual real de SmartDiag504.

## Navegación interna

1. Inicio operativo.
2. Agenda y recepción.
3. Órdenes de trabajo.
4. Taller y bahías.
5. Técnicos.
6. Repuestos y bodega.
7. Compras pendientes.
8. Caja/POS.
9. Clientes y vehículos.
10. Garantías.
11. Alertas.
12. Reportes.
13. Administración.

El menú se reduce por rol: un técnico no ve contabilidad; un cajero no ve configuración técnica; un cliente solo ve su portal.

## Pantalla de recepción rápida

Objetivo operativo: completar un ingreso estándar en pocos minutos sin perder controles.

- Buscar por placa, VIN, teléfono o QR.
- Confirmar cliente y vehículo.
- Registrar kilometraje, combustible y motivo.
- Checklist visual de daños/accesorios.
- Fotografías guiadas.
- Autorizar diagnóstico y firmar.
- Generar OT y etiqueta.

## Lista de OT

- Tabla densa con filtros guardables.
- Estado, vehículo, cliente, asesor, técnico, bahía, fecha prometida, espera, total y alerta principal.
- Vistas Kanban y calendario cuando aporten valor; la tabla sigue siendo la herramienta principal de control.
- Acciones masivas limitadas y auditadas.

## Workspace de OT

Cabecera fija con número, vehículo, cliente, estado, fecha prometida, saldo, última actividad y acciones permitidas.

Secciones:

1. Resumen y línea de tiempo.
2. Recepción e inspección.
3. Diagnóstico y DTC.
4. Cotización y aprobaciones.
5. Operaciones y técnicos.
6. Repuestos.
7. Evidencias y documentos.
8. Control de calidad.
9. Factura y pago.
10. Entrega, garantía e historial.

## Tablero de taller

- Bahías como carriles o plano 2D.
- Vehículo, OT, técnico, operación actual, tiempo transcurrido, bloqueo y próxima acción.
- Técnicos sin trabajo y trabajos sin técnico.
- Riesgo sobre fecha prometida.
- Arrastre solo para acciones válidas; las transiciones se confirman y auditan.

## PWA de técnico

- “Mis trabajos” y prioridad.
- Iniciar, pausar, reanudar y terminar operación.
- Checklist, DTC, mediciones, fotos, audio transcrito y notas.
- Solicitar repuestos y confirmar recepción.
- Informar trabajo adicional.
- Enviar a control de calidad.
- Offline limitado a tareas previamente descargadas; conflicto visible al sincronizar.

## Bodega

- Cola de solicitudes por prioridad y ubicación.
- Disponibilidad, reserva y sustitutos.
- Picking por código de barras/QR.
- Entrega y confirmación del receptor.
- Devolución, core, garantía y faltante.
- Compras vinculadas a OT.

## Caja y POS

- Apertura y saldo inicial.
- Cobro de OT o venta de mostrador.
- Métodos múltiples y pagos parciales.
- Factura/ticket, impresión y envío digital.
- Retiros, gastos autorizados y cierre.
- Diferencia visible y flujo de aprobación.

## Gerencia

- Ingreso, costo y margen por OT, servicio, técnico, sucursal y período.
- Mano de obra vendida, disponible y real.
- Utilización, eficiencia y productividad.
- Conversión de cotizaciones.
- Tiempo de ciclo y cumplimiento de promesa.
- Ventas y margen de repuestos.
- Inventario lento, faltantes y rotación.
- Combacks, garantías y retrabajos.
- Flujo de caja, cuentas por cobrar y resultado contable desde ERPNext.

## Portal del cliente

- Reservar o reprogramar.
- Ver ingreso, fotografías y estado comprensible.
- Aprobar/rechazar cotización por línea.
- Consultar trabajo adicional.
- Pagar por canal habilitado.
- Descargar factura, informe y garantía.
- Ver historial y próximo mantenimiento.
- Autorizar comunicaciones.

## Landing page y tienda

Estructura recomendada:

1. Hero directo: diagnóstico, programación y reparación Ford con evidencia técnica.
2. Servicios: diagnóstico/programación, transmisión, aire acondicionado, mantenimiento, frenos/suspensión/electrónica y repuestos.
3. Cómo funciona: reservar, diagnosticar, aprobar, reparar y recibir evidencia.
4. Casos o testimonios verificables.
5. Reserva con disponibilidad.
6. Catálogo de repuestos y validación por VIN.
7. Ubicación, horario, contacto y WhatsApp.
8. Preguntas frecuentes, políticas, privacidad y garantía.

No se publicarán certificaciones, garantías, tiempos ni porcentajes que la empresa no pueda demostrar.
