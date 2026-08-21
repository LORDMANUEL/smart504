# Inventario UX/UI de SmartDiag504

## Sistema visual compartido

Fuente: `docs/brand/BRAND_SYSTEM.md` y `packages/design-system`.

Estados obligatorios en cada pantalla: cargando, vacío, error recuperable, sin permiso, offline cuando aplique, éxito, validación y responsive. No usar información financiera de demostración en producción.

## Web pública y tienda

| Ruta/pantalla | Objetivo | Componentes principales | Estado actual |
|---|---|---|---|
| Inicio | Presentar propuesta y confianza | navegación, hero, servicios, proceso, contacto | skeleton funcional |
| Servicios | Explicar diagnóstico/mantenimiento | categorías, detalle, CTA reserva | skeleton |
| Repuestos | Buscar y comprar | búsqueda, filtros, tarjetas, compatibilidad, disponibilidad | skeleton funcional demo/API |
| Detalle de repuesto | Decidir compatibilidad | galería, SKU, precio, fitment, pedido especial | pendiente |
| Carrito | Revisar líneas | cantidades, subtotal, retiro, validaciones | skeleton local |
| Checkout | Dirección/pago | identidad, entrega, impuestos, pasarela | bloqueado hasta adaptadores |
| Reserva | Solicitar cita | cliente, vehículo, servicio, fecha, consentimiento | skeleton conectado a API |
| Confirmación | Mostrar referencia | resumen y siguiente paso | skeleton |
| Legal | Cumplimiento | privacidad, términos, cookies, garantía | pendiente contenido legal |

## Portal del cliente

| Pantalla | Función | Controles críticos |
|---|---|---|
| Acceso/recuperación | autenticar | MFA opcional, rate limit, recuperación segura |
| Inicio | resumen de vehículos/OT | citas, alertas, próximos mantenimientos |
| Mis vehículos | listado e historial | VIN/placa, kilometraje, documentos |
| Estado de OT | seguimiento | etapas, fecha prometida, contacto |
| Cotización | aprobación por línea | evidencia, importe, aprobar/rechazar, firma |
| Evidencias | ver fotos/DTC | autorización por objeto, descarga corta |
| Pagos | iniciar/consultar | estado, recibo, reintento seguro |
| Facturas | descargar | documento fiscal autorizado |
| Citas | crear/reprogramar | capacidad real y política |
| Garantía | solicitar/seguir | OT origen, síntomas, evidencia |
| Perfil/consentimiento | datos personales | edición controlada y privacidad |

## PWA operacional

| Vista | Usuarios | Elementos |
|---|---|---|
| Login/sesión | todos | identidad, sucursal, dispositivo |
| Dashboard | supervisor/asesor | OT abiertas, atrasos, técnicos, bahías, alertas |
| Kanban OT | operación | estados, filtros, prioridad, fecha prometida |
| Detalle OT 360 | autorizado | cliente, vehículo, recepción, diagnóstico, cotización, técnicos, repuestos, QC, factura |
| Recepción | asesor | checklist, combustible, daños, fotos, firma |
| Diagnóstico | técnico | DTC, pruebas, hallazgos, evidencia, recomendaciones |
| Cotización | asesor | líneas, versiones, margen restringido, envío/aprobación |
| Agenda | asesor/supervisor | capacidad, citas, reprogramación |
| Taller/bahías | supervisor | bahía, vehículo, técnico, estado, duración |
| Mi trabajo | técnico | operaciones asignadas, cronómetro, pausas |
| Repuestos | técnico/bodega | solicitar, preparar, entregar, confirmar, devolver |
| Compras especiales | bodega/compras | solicitud, PO, recepción, asignación OT |
| QC/prueba | supervisor | checklist, fallo, corrección, aprobación |
| Entrega | asesor | saldo, documentos, firma, mantenimiento |
| Garantías | supervisor | cobertura, reincidencia, costo, resolución |
| Caja | cajero | apertura, cobro, gastos autorizados, cierre/diferencia |
| Alertas | roles | severidad, reconocimiento, escalamiento, resolución |
| Reportes | gerencia | margen OT, productividad, conversión, retrabajo |
| Configuración | admin | catálogos, estados, roles, sucursales, integraciones |

## ERPNext/Frappe administrativo

- Empresa, plan de cuentas y dimensiones.
- Clientes/proveedores/artículos/listas de precios.
- Bodegas, stock ledger y conteos.
- Compras, recepciones y cuentas por pagar.
- POS, facturas, pagos y cierres.
- Usuarios, roles, logs y configuración técnica.
- DocTypes SmartDiag para soporte/auditoría avanzada.

La operación diaria debe ocurrir mayormente en la PWA; el escritorio ERPNext se reserva para administración y contabilidad especializada.

## Prioridad de diseño

1. Detalle OT 360.
2. Recepción tablet/móvil.
3. Diagnóstico/técnico.
4. Bodega y devolución.
5. Cotización/aprobación portal.
6. QC/entrega.
7. Checkout y pedido.
8. Reportes gerenciales.
