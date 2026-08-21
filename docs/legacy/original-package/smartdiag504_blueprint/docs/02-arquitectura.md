# 02 — Arquitectura objetivo

## 1. Estilo arquitectónico

Arquitectura modular orientada a dominio, desplegada inicialmente como **monolito modular** para la operación del taller y separada del ERP por adaptadores. Esto evita crear microservicios prematuros, pero conserva límites que permiten separar componentes cuando el volumen lo justifique.

## 2. Componentes

### SmartDiag Core API — FastAPI/Python

Responsable de clientes operativos, vehículos, citas, recepción, inspecciones, OT, diagnóstico, cotizaciones técnicas, aprobaciones, asignación, tiempos, evidencias, control de calidad, entrega, garantía, alertas y portal.

### SmartDiag Web — React/TypeScript

Portal interno responsivo para recepción, taller, bodega, caja de consulta, gerencia y administración.

### Technician PWA — React/TypeScript

Interfaz móvil optimizada para tareas asignadas, cronómetro, checklist, fotografías, notas, solicitud de repuestos, pausas y cierre técnico. Tendrá capacidad offline limitada con sincronización controlada; no ejecutará movimientos financieros offline.

### Storefront/Portal — TypeScript

Landing page, reserva de citas, catálogo de servicios, catálogo de repuestos, compatibilidad, carrito/reserva, cuenta del cliente, aprobaciones, pagos y estado de la OT.

### ERPNext v16

Fuente de verdad para artículos, listas de precios, proveedores, compras, bodegas, disponibilidad valorizada, movimientos de stock, POS, facturas, notas de crédito, pagos, cuentas por cobrar/pagar y contabilidad.

### Integration Worker

Consume la bandeja de salida transaccional, publica documentos en ERPNext con claves idempotentes, recibe webhooks o consulta estados, actualiza mapeos y ejecuta conciliaciones.

### Alert Engine

Evolución del sistema de alertas existente. Consume eventos de dominio, aplica reglas, deduplica alertas, asigna severidad, notifica por UI, correo, WhatsApp u otros canales y conserva acuse/resolución.

### AI/RAG Service

Ingesta documentos aprobados, genera embeddings, consulta ChromaDB y llama al LLM configurado. Devuelve respuestas con fuentes, nivel de confianza operativo y límites de acción.

### PostgreSQL

Fuente transaccional de SmartDiag Core. Usa claves estables, restricciones, historial inmutable y outbox.

### Redis

Colas, caché, locks distribuidos, rate limiting, sesiones efímeras, presencia y pub/sub. No almacena la única copia de ningún dato de negocio.

### ChromaDB

Índice vectorial por cliente y nivel de acceso. No guarda saldos, existencias, precios oficiales ni estados de OT como fuente primaria.

### MinIO/S3

Evidencias, fotografías, videos, firmas, PDFs, escáneres y anexos, con URL firmada, checksum, versión y política de retención.

## 3. Matriz de fuente de verdad

| Dato | Fuente principal | Réplica/uso secundario |
|---|---|---|
| Cliente: identidad y contacto operativo | SmartDiag | ERPNext recibe el cliente mapeado |
| Cliente: RTN, crédito, términos contables | ERPNext | SmartDiag muestra una copia de consulta |
| Vehículo, VIN, placa, odómetro e historial | SmartDiag | ERPNext conserva referencia externa |
| Catálogo de servicios técnicos | SmartDiag | ERPNext tiene ítems de servicio equivalentes |
| SKU, costo, precio, impuesto y existencias | ERPNext | SmartDiag mantiene caché con fecha de actualización |
| OT, diagnóstico, evidencias y tiempos | SmartDiag | ERPNext recibe referencias y documentos comerciales |
| Cotización técnica antes de aprobar | SmartDiag | No se contabiliza |
| Cotización aprobada/orden comercial | ERPNext | SmartDiag conserva ID y estado sincronizado |
| Consumo físico de repuesto | ERPNext | SmartDiag inicia la solicitud y registra vínculo |
| Factura, nota de crédito, pago y caja | ERPNext | SmartDiag muestra estado y documentos |
| Conocimiento técnico y embeddings | ChromaDB + objeto fuente | SmartDiag conserva metadatos y ACL |
| Cola/caché | Redis | Siempre regenerable |

## 4. Integración segura

### Patrón outbox

Toda acción que deba llegar a ERPNext crea, en la misma transacción local, un evento en `outbox_event`. El worker lo procesa fuera de la solicitud HTTP. Si ERPNext no está disponible, el evento permanece pendiente y se reintenta sin duplicar documentos.

### Idempotencia

Cada documento publicado usa una clave estable, por ejemplo:

`tenant_id + document_type + smartdiag_document_id + version`

ERPNext conservará esa referencia externa en un campo personalizado. Un reintento consulta primero la referencia antes de crear un nuevo documento.

### Conciliación

Jobs programados comparan:

- cotizaciones aprobadas contra documentos comerciales;
- repuestos entregados contra movimientos de stock;
- facturas contra OT listas para facturar;
- pagos contra saldos;
- cierres de caja contra documentos del período.

Las diferencias crean alertas de conciliación; nunca se corrigen silenciosamente.

## 5. Modelo de despliegue

### SmartDiag504 interno

Una instalación con varias sucursales, talleres, bodegas y cajas.

### Producto comercial

Una pila aislada por cliente, con sitio ERPNext y base SmartDiag independientes. Un control plane central puede administrar licencias, versiones y telemetría técnica mínima, pero no debe concentrar los datos operativos de todos los talleres.

## 6. Principios no negociables

- No hacer escrituras contables directas desde la base SmartDiag.
- No usar Redis o ChromaDB como base de negocio.
- No ejecutar doble escritura síncrona entre PostgreSQL y ERPNext.
- No permitir cambios de estado fuera de la máquina autorizada.
- No modificar cotizaciones enviadas; se crea una versión o enmienda.
- No borrar documentos financieros ni evidencias de auditoría.
- No permitir que un LLM ejecute movimientos de inventario, pagos o facturas sin una acción determinística y aprobación humana.

## 7. Diagrama

Ver `../diagrams/architecture.mmd`.
