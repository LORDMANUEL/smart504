# SmartDiag504 Workshop OS

**Blueprint de producto, arquitectura y contratos — versión 0.1**  
**Fecha:** 11 de agosto de 2026  
**Estado:** propuesta de diseño para aprobación antes de programar el producto ejecutable.

## Decisión recomendada

Construir **SmartDiag504 Workshop OS** como producto propio para la operación automotriz, con:

- **FastAPI + PostgreSQL** para órdenes de trabajo, recepción, diagnóstico, tiempos, evidencias, aprobaciones, control de calidad e historial del vehículo.
- **React/TypeScript** para el portal administrativo y la PWA de técnicos.
- **ERPNext v16** como núcleo financiero y logístico: artículos, precios, bodegas, compras, existencias, POS, facturas, pagos, cuentas por cobrar/pagar, libro mayor, flujo de caja y pérdidas/ganancias.
- **Redis** para colas, caché, sesiones, rate limiting y eventos en tiempo real.
- **ChromaDB** para recuperación semántica de manuales, boletines, casos resueltos y políticas; nunca como fuente transaccional.
- **MinIO/S3** para fotografías, videos, escaneos, firmas, cotizaciones y documentos.
- El motor de alertas existente como base para reglas, eventos, notificaciones y observabilidad.

La arquitectura evita dos errores frecuentes: reinventar contabilidad/inventario desde cero y forzar toda la experiencia del taller dentro de un ERP genérico.

## Qué contiene este paquete

- Investigación comparativa de proyectos open source.
- Tres enfoques posibles y decisión recomendada.
- Arquitectura, límites de dominio y matriz de fuentes de verdad.
- Módulos funcionales y flujo completo de una OT.
- Modelo de datos y diagramas Mermaid.
- Mapa UX/UI por rol y canal.
- Diseño de IA, RAG, ChromaDB, Redis y alertas.
- Seguridad, auditoría, calidad, respaldos y operación.
- Estrategia de licencias y localización fiscal para Honduras.
- Roadmap por gates y criterios de aceptación.
- Árbol propuesto del monorepo.
- Contratos preliminares OpenAPI, eventos, permisos y máquina de estados.

## Principio rector

Cada dato tiene **una sola fuente de verdad**:

- SmartDiag504 controla la operación técnica del taller.
- ERPNext controla inventario valorizado, compras, facturación, caja y contabilidad.
- ChromaDB solo indexa conocimiento.
- Redis solo conserva estado temporal, colas y caché.
- El almacenamiento de objetos conserva evidencias y documentos.

## Uso esperado

Este paquete sirve para revisar y aprobar la arquitectura antes de generar el repositorio ejecutable. No contiene un ERP modificado ni una aplicación lista para producción; sí deja definidos los límites, contratos y criterios necesarios para programarla sin improvisar ni crear deuda técnica estructural.
# 00 — Investigación open source y selección tecnológica

## 1. Contexto real de SmartDiag504

La presencia pública encontrada presenta a SmartDiag504 como taller de San Pedro Sula especializado en diagnóstico, programación y reparación automotriz Ford. También comunica servicios de aire acondicionado y reparación de transmisiones Ford. Esto orienta el producto hacia trazabilidad técnica, evidencia del diagnóstico, programación electrónica, historial por VIN y una experiencia de atención especializada, no solo hacia una caja de repuestos.

## 2. Enfoques evaluados

### Enfoque A — Adoptar un sistema automotriz open source completo

**Ventaja:** parece reducir el trabajo inicial.  
**Riesgo:** los proyectos encontrados no cubren con suficiente profundidad contabilidad, compras, valorización de inventario, fiscalidad, conciliación de caja, seguridad y operación sostenida.

**Conclusión:** rechazado como núcleo de producción. Es útil únicamente para estudiar pantallas, flujos y modelos de datos.

### Enfoque B — Construir todo dentro de ERPNext

**Ventaja:** menor complejidad de sincronización; inventario, compras, ventas, POS y contabilidad ya viven en una sola plataforma.  
**Riesgo:** la experiencia de recepción, bahías, diagnóstico, técnicos, fotografías, aprobaciones y PWA queda muy ligada a Frappe y puede sentirse como un ERP adaptado en vez de un producto automotriz especializado.

**Conclusión:** opción válida para un despliegue interno económico, pero menos flexible como producto comercial diferenciado.

### Enfoque C — SmartDiag504 Workshop OS + ERPNext por adaptador

**Ventaja:** UX automotriz propia, motor de alertas reutilizable, API Python limpia y libertad para vender el producto; ERPNext conserva las áreas en las que un error es más costoso: inventario, compras, caja y contabilidad.  
**Riesgo:** exige integración idempotente, conciliación y límites estrictos para evitar doble fuente de verdad.

**Conclusión:** **recomendado**.

## 3. Proyectos evaluados

| Proyecto | Qué aporta | Limitación relevante | Uso recomendado |
|---|---|---|---|
| **ERPNext v16** | Contabilidad, ventas, compras, existencias, almacenes, POS, pagos, reportes, API y framework Python | No es un DMS/taller automotriz especializado; requiere app e integración propias | Núcleo ERP y fuente de verdad financiera/logística |
| **Odoo Community 19** | ERP amplio, reparación genérica, POS, e-commerce, inventario y reportes | La reparación estándar está orientada a productos devueltos; hay que revisar qué capacidades dependen de Enterprise | Alternativa estratégica a ERPNext, no primera elección |
| **Beveren FSM** | Flujo solicitud → cotización → orden → agenda → ejecución → factura; React/TypeScript sobre ERPNext | Proyecto joven, AGPL y orientado a servicio de campo, no a recepción vehicular | Referencia de arquitectura y experiencia técnica |
| **RepairOS** | Multiempresa, OT, inventario, roles, portal técnico y enfoque SaaS | El repositorio fue archivado el 8 de julio de 2026 y quedó en solo lectura | Referencia de dominio; no adoptar ni depender de él |
| **GarageBuddy** | Usuarios, vehículos e historial de servicio | El propio repositorio marca el seguimiento de servicios como trabajo en progreso | Referencia menor; no base productiva |
| **Dolibarr** | ERP/CRM maduro con cotizaciones, facturas, compras, stock, POS y contabilidad | Stack PHP y sin dominio automotriz profundo | Plan B ligero para empresas pequeñas |
| **Frappe Assistant Core** | MCP/LLM conectado a permisos de ERPNext y auditoría de llamadas | AGPL; incluye herramientas que deben restringirse en un sistema financiero | Referencia para la capa IA y permisos, no copiar sin decidir licencia |

## 4. Matriz de decisión técnica

Puntuación estimada de 1 a 5. Es una evaluación de adecuación a SmartDiag504, no una calificación absoluta de cada proyecto.

| Criterio | Peso | ERPNext | Odoo CE | Beveren FSM | RepairOS | GarageBuddy | Dolibarr |
|---|---:|---:|---:|---:|---:|---:|---:|
| Madurez operativa | 20% | 5 | 5 | 2 | 1 | 2 | 4 |
| Finanzas, compras e inventario | 20% | 5 | 5 | 4 | 2 | 1 | 4 |
| Ajuste al taller automotriz | 20% | 3 | 3 | 4 | 4 | 2 | 2 |
| Python/API/extensibilidad | 15% | 5 | 4 | 5 | 4 | 1 | 2 |
| TypeScript/UX propia | 10% | 3 | 3 | 5 | 2 | 1 | 1 |
| Riesgo de licencia/comercialización | 10% | 3 | 4 | 2 | 5 | 5 | 3 |
| Comunidad y continuidad | 5% | 5 | 5 | 2 | 1 | 2 | 4 |
| **Resultado ponderado** | **100%** | **4.30** | **4.20** | **3.55** | **2.70** | **1.80** | **3.00** |

## 5. Decisión final

1. **ERPNext v16** como back office de negocio y contabilidad.
2. **SmartDiag504 Workshop OS** como operación técnica, experiencia de usuario, portal, PWA, IA y alertas.
3. **Beveren FSM, Odoo Repairs, RepairOS y GarageBuddy** solo como referencias funcionales; no como dependencia central.
4. Integración por API y eventos, con adaptadores reemplazables para permitir Odoo u otro ERP en el futuro.
5. Revisión legal de GPL/AGPL/LGPL antes de incorporar código de terceros al producto comercial.
# 01 — Visión y alcance del producto

## Visión

SmartDiag504 Workshop OS será una plataforma integral para administrar el ciclo completo de servicio automotriz: desde la reserva y recepción del vehículo hasta su diagnóstico, cotización, reparación, facturación, pago, entrega, garantía, mantenimiento futuro y venta de repuestos.

La diferencia comercial no será “tener una OT digital”. Será ofrecer:

- trazabilidad técnica completa por vehículo y VIN;
- evidencia verificable de qué fallaba, qué se autorizó, qué se instaló y quién lo ejecutó;
- control de tiempos y productividad por técnico;
- integración real entre taller, bodega, compras, caja y contabilidad;
- comunicación transparente con el cliente;
- conocimiento técnico asistido por IA con fuentes y permisos;
- operación multi-sucursal y capacidad de vender la plataforma a otros talleres.

## Usuarios principales

- Propietario o gerente general.
- Gerente de taller y jefe técnico.
- Asesor de servicio o recepción.
- Técnico, ayudante y especialista.
- Inspector de calidad.
- Encargado de repuestos y bodega.
- Comprador.
- Cajero.
- Contador y auditor.
- Encargado de e-commerce.
- Cliente final.

## Propuesta de valor para SmartDiag504

La identidad pública de SmartDiag504 se enfoca en diagnóstico, programación y reparación Ford. La plataforma debe convertir esa especialización en una experiencia visible:

- recepción basada en síntomas, historial, kilometraje y VIN;
- carga de escáneres, DTC, módulos y evidencias;
- comparación con casos similares resueltos;
- explicación clara de la causa probable y del trabajo aprobado;
- historial de programación, calibraciones, transmisión, aire acondicionado y reparaciones;
- catálogo de repuestos con compatibilidad por VIN y validación humana.

## Alcance obligatorio de la primera versión operativa

1. Empresas, sucursales, talleres, bahías, usuarios y roles.
2. Clientes, vehículos, VIN, placa, kilometraje e historial.
3. Reserva, cita, recepción, inventario visual y firma.
4. Orden de trabajo y máquina de estados auditable.
5. Diagnóstico, DTC, hallazgos, fotografías y documentos.
6. Cotización versionada de mano de obra, repuestos, cargos, descuentos e impuestos.
7. Aprobación o rechazo por línea y autorización digital.
8. Asignación de uno o varios técnicos; registro de tiempo real y pausas.
9. Solicitud, reserva, entrega, consumo y devolución de repuestos.
10. Control de calidad, prueba de carretera, retrabajo y liberación.
11. Factura, pagos, caja y documentos fiscales por integración con ERPNext.
12. Historial 360 del vehículo y garantía de trabajos.
13. Alertas operativas y tablero gerencial.
14. Portal del cliente para aprobar, consultar, pagar y reservar.
15. Landing page, catálogo y venta/reserva online de repuestos.

## Fuera del núcleo inicial

- Nómina completa y recursos humanos legalmente localizados.
- Diagnóstico automático sin revisión de un técnico.
- Telemetría en tiempo real desde vehículos.
- Marketplace abierto de terceros.
- Gestión de aseguradoras y siniestros complejos.
- Contabilidad escrita directamente por el microservicio de taller.

Estos elementos pueden incorporarse después, pero no deben contaminar el primer núcleo.

## Modelo comercial recomendado

- Una instalación aislada por cliente o grupo empresarial.
- Varias sucursales y talleres dentro de la instalación.
- Planes comerciales por número de sucursales, usuarios, técnicos, almacenamiento, funciones de IA y volumen de transacciones.
- Actualizaciones controladas por versión y migraciones reproducibles.
- Servicios adicionales: implementación, migración, personalización, soporte, formación y conocimiento técnico.

## Indicadores de éxito del producto

- Cero OT sin historial de estado y responsable.
- Cero consumo de repuesto sin documento y usuario trazable.
- Cero edición silenciosa de una cotización ya enviada.
- Cero factura duplicada por reintentos de integración.
- Conciliación diaria entre OT, existencias, facturas, pagos y caja.
- Reducción de tiempos muertos y de espera por repuestos.
- Medición de conversión de cotizaciones, margen por OT, utilización técnica y reincidencia.
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
# 04 — Modelo de datos

## Convenciones

- Identificadores UUID ordenables.
- `tenant_id`, `branch_id`, `created_at`, `created_by`, `updated_at` y versión de concurrencia en toda entidad aplicable.
- Dinero almacenado en unidades menores enteras y código de moneda; nunca `float`.
- Cantidades técnicas con decimal y unidad de medida explícita.
- VIN normalizado en mayúsculas, sin espacios y con índice único por cliente.
- Odómetro entero no decreciente, salvo corrección auditada.
- Estados mediante enumeraciones y tabla de historial.
- Documentos enviados, aprobados o contabilizados no se sobrescriben.
- Eliminación lógica únicamente para maestros permitidos; eventos, aprobaciones y movimientos son inmutables.

## Entidades de organización

- `Organization`
- `Branch`
- `Workshop`
- `Bay`
- `WarehouseReference`
- `CashRegisterReference`
- `User`
- `Role`
- `Permission`
- `TechnicianProfile`
- `Skill`
- `Certification`
- `TechnicianSkill`

## Clientes y vehículos

### Customer

- tipo, nombre legal, nombre comercial;
- RTN y datos fiscales referenciados;
- teléfonos, correos, direcciones;
- canal preferido y consentimientos;
- ID externo en ERPNext.

### Vehicle

- VIN, placa, marca, modelo, versión y año;
- motor, transmisión, combustible y color;
- propietario/contactos autorizados;
- kilometraje actual y fecha;
- estado activo, vendido o transferido.

### VehicleOdometer

- valor, unidad, origen, OT, usuario, fecha y evidencia.

## Agenda y recepción

- `Appointment`
- `AppointmentResource`
- `Intake`
- `IntakeDamage`
- `IntakeAccessory`
- `InspectionTemplate`
- `Inspection`
- `InspectionItemResult`
- `CustomerAuthorization`

## Orden y diagnóstico

### WorkOrder

- número interno y referencia externa;
- cliente, vehículo, sucursal, taller, bahía;
- asesor, prioridad, fecha prometida;
- motivo de visita y síntoma del cliente;
- estado, bloqueo y versión;
- totales estimados, aprobados, facturados y pagados reflejados;
- IDs de documentos ERP.

### WorkOrderStatusHistory

- estado anterior/nuevo, motivo, usuario, fecha, correlación y metadatos.

### DiagnosticFinding

- síntoma reproducido;
- sistema/módulo;
- prueba, valor esperado, valor real;
- hallazgo, causa probable/confirmada;
- severidad y riesgo;
- evidencia y fuente técnica.

### DtcObservation

- código, módulo, descripción, estado, freeze frame, origen y archivo.

## Cotización y aprobación

- `Estimate`
- `EstimateVersion`
- `EstimateLine`
- `EstimateLineAlternative`
- `EstimateApproval`
- `EstimateApprovalLine`
- `ChangeOrder`

`EstimateLine.type` será uno de: `LABOR`, `PART`, `CONSUMABLE`, `SUBLET`, `FEE`, `DISCOUNT`.

## Ejecución

- `JobOperation`
- `TechnicianAssignment`
- `TimeEntry`
- `PauseReason`
- `TechnicianNote`
- `PartRequest`
- `PartRequestLine`
- `PartReservationReference`
- `PartIssueReference`
- `PartConsumptionReference`
- `PartReturnReference`

## Calidad y entrega

- `QualityInspection`
- `QualityInspectionItem`
- `RoadTest`
- `Rework`
- `Delivery`
- `DeliveryRecommendation`
- `WarrantyPolicy`
- `WarrantyCoverage`
- `WarrantyClaim`

## Documentos y comunicaciones

- `Attachment`
- `AttachmentVersion`
- `Signature`
- `Conversation`
- `Message`
- `NotificationDelivery`
- `CustomerPortalToken`

## Integración y auditoría

- `ExternalMapping`
- `OutboxEvent`
- `InboxEvent`
- `IntegrationAttempt`
- `ReconciliationRun`
- `ReconciliationDifference`
- `AuditLog`
- `AlertRule`
- `AlertInstance`
- `AlertAcknowledgement`

## E-commerce

- `CatalogFitmentOverride`
- `CartReservation`
- `EcommerceOrderReference`
- `PickupSlot`
- `SpecialOrderRequest`

Los maestros y movimientos de artículo, precio, costo, lote, serie, proveedor, compra, recepción, factura, pago y asiento no se duplican como tablas transaccionales completas: se consultan o sincronizan como referencias desde ERPNext.

## Índices mínimos

- VIN, placa, teléfono y correo normalizados.
- OT por estado, sucursal, técnico, fecha prometida y última actividad.
- citas por recurso y rango de tiempo.
- outbox por estado y próxima ejecución.
- alertas por estado, severidad, responsable y fecha.
- auditoría por entidad, ID, usuario y correlación.

Ver `../diagrams/erd.mmd`.
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
# 07 — Seguridad, calidad y operación

## Identidad y acceso

- OIDC/OAuth2 con MFA para roles sensibles.
- Sesiones cortas, refresh tokens rotativos y revocación.
- RBAC por rol, sucursal, taller y ámbito de datos.
- Permisos de campo/acción para precios, descuentos, cancelaciones y datos fiscales.
- Cuentas de servicio separadas para integración.

## Segregación de funciones

- Técnico no modifica precio, descuento ni factura.
- Bodega no aprueba su propia compra.
- Cajero no anula documentos ni perdona diferencias sin autorización.
- Asesor no libera un vehículo con bloqueo financiero sin aprobador.
- Administrador técnico no accede por defecto a secretos de infraestructura.
- Auditor tiene lectura y exportación controlada, sin escritura.

## Protección de datos

- TLS en tránsito.
- Cifrado de discos, respaldos y objetos sensibles.
- Secretos en gestor dedicado; nunca en repositorio o imagen.
- URL firmadas y expirables para evidencias.
- Antivirus en cargas.
- Checksums y versiones de archivos.
- Políticas de retención y purga legalmente aprobadas.
- Bitácora inmutable de accesos y acciones críticas.

## Aislamiento comercial

- Una base o esquema aislado por cliente; preferencia por pila separada.
- Colecciones Chroma por cliente.
- Buckets o prefijos de objetos aislados.
- Pruebas automáticas contra fuga entre clientes.
- Backups y restauración por cliente.

## Auditoría

El audit log captura:

- actor humano o servicio;
- rol y organización;
- acción y entidad;
- valores relevantes antes/después;
- fecha, IP, dispositivo y correlación;
- resultado, motivo y aprobador;
- hash o referencia de evidencia.

No se registran contraseñas, tokens ni datos secretos.

## Resiliencia

- Outbox/inbox para entrega al menos una vez con idempotencia.
- Circuit breaker y backoff para ERP, pagos y mensajería.
- Dead-letter queue visible y operable.
- Jobs de conciliación.
- Migraciones versionadas y reversibles cuando sea viable.
- Modo degradado: el taller puede consultar y trabajar en funciones no financieras cuando ERP no responde; facturación y movimientos se bloquean o quedan claramente pendientes.

## Objetivos operativos iniciales

- Disponibilidad objetivo mensual: 99.5% para la instalación productiva.
- RPO objetivo: 15 minutos.
- RTO objetivo: 2 horas.
- Lecturas comunes p95 inferiores a 500 ms dentro de la red normal.
- Acciones de UI con respuesta visible inmediata y procesamiento asíncrono cuando corresponda.

Son objetivos de ingeniería y deben ajustarse al presupuesto e infraestructura contratados.

## Backups

- PostgreSQL: respaldo completo + WAL/PITR.
- ERPNext/MariaDB: respaldo consistente de base y archivos.
- MinIO/S3: versionado y réplica o copia externa.
- ChromaDB: reconstruible desde fuentes, pero respaldado para acelerar recuperación.
- Redis: no se considera respaldo de negocio.
- Prueba de restauración periódica con evidencia.

## Observabilidad

- Logs JSON con correlación.
- Métricas de API, worker, colas, base, integración y alertas.
- Trazas distribuidas para OT → outbox → ERP.
- Dashboards y alertas técnicas.
- Monitoreo de expiración de certificados, respaldos y espacio.
- Registro de costo/latencia/error por modelo LLM.

## Estrategia de pruebas

### Unitarias

- cálculo monetario;
- descuentos e impuestos;
- transiciones de estado;
- permisos;
- reglas de alertas;
- idempotencia.

### Integración

- PostgreSQL real;
- Redis;
- API mock/real de ERPNext en sandbox;
- almacenamiento de objetos;
- webhooks y reintentos.

### Contrato

- OpenAPI;
- eventos versionados;
- adaptador ERP;
- pagos y mensajería.

### End-to-end

- cita → ingreso → diagnóstico → aprobación → repuestos → ejecución → QC → factura → pago → entrega;
- venta POS;
- pedido online;
- garantía;
- caída y recuperación del ERP;
- aislamiento entre clientes.

### Seguridad

- SAST, dependencias, secretos, imágenes y IaC.
- pruebas de autorización horizontal/vertical.
- rate limiting y abuso.
- carga maliciosa de archivos.
- prompt injection y exfiltración por herramientas LLM.

## Definition of Done

Una función no está terminada hasta tener:

- criterios de aceptación;
- permisos y auditoría;
- validaciones e invariantes;
- migración;
- pruebas;
- observabilidad;
- documentación de usuario/operación;
- manejo de errores y reintentos;
- revisión de seguridad;
- compatibilidad con actualización.
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
# 09 — Licencias y localización fiscal de Honduras

## 1. Licencias open source

### ERPNext — GPLv3

Puede usarse, modificarse y ofrecerse como servicio. La distribución de una versión modificada exige respetar las obligaciones de GPL. Las personalizaciones, módulos y forma de distribución deben revisarse antes de vender un producto cerrado.

### Odoo Community — LGPLv3

La edición Community usa LGPLv3. La edición Enterprise usa una licencia propia que requiere suscripción válida. No se debe asumir que una función documentada o mostrada comercialmente está disponible en Community sin verificar el módulo concreto.

### Beveren FSM y Frappe Assistant Core — AGPLv3

AGPL extiende obligaciones de disponibilidad de código al uso a través de red. Si SmartDiag504 desea mantener módulos propietarios, no debe copiar o incorporar código AGPL sin aceptar esas obligaciones o negociar otra licencia.

### RepairOS y GarageBuddy — MIT

La licencia es permisiva, pero la licencia no resuelve el riesgo de madurez, mantenimiento o calidad. RepairOS está archivado y GarageBuddy reconoce funciones centrales aún en progreso.

### Dolibarr — GPLv3+

Es viable como ERP abierto, pero su stack y dominio no coinciden con la arquitectura seleccionada.

## 2. Estrategia recomendada de propiedad intelectual

- Código propio de SmartDiag504 en repositorio separado.
- Integración con ERPNext por API, campos personalizados y una app claramente delimitada.
- Registro de dependencias, licencia, versión y avisos.
- No copiar pantallas, textos, marcas ni código de proyectos de referencia.
- Revisión legal antes de distribuir imágenes que contengan ERP modificado.
- Política de contribuciones y cesión/licencia del código creado por terceros.
- Decidir explícitamente si el producto será propietario, open core o AGPL comercial con servicios.

## 3. Facturación en Honduras

El SAR establece que quienes transfieren bienes o prestan servicios deben emitir comprobante fiscal. Reconoce, entre otros, factura, ticket, notas de crédito y notas de débito. La Oficina Virtual permite solicitar inscripción al Régimen de Facturación y el SAR mantiene procedimientos específicos actualizados.

Por ello el producto requiere un **módulo de localización fiscal hondureña** validado por un contador y especialista del SAR antes de producción.

Capacidades mínimas a validar:

- RTN y datos legales del emisor/cliente;
- establecimiento y punto de emisión;
- tipo de documento fiscal;
- CAI, rango autorizado, correlativo y fecha límite;
- impuestos, exoneraciones y descuentos;
- factura, ticket, nota de crédito/débito y anulaciones;
- impresión y representación digital;
- cierre de caja y conservación cronológica;
- auditoría de documentos emitidos, anulados y no utilizados;
- exportes necesarios para declaraciones y revisión contable.

## 4. Regla de implementación

No se programará una “factura bonita” como sustituto de un comprobante válido. La factura se generará en ERPNext mediante una localización o integración fiscal que haya pasado:

1. revisión funcional del contador;
2. prueba con escenarios reales;
3. validación de numeración/rangos/vencimiento;
4. prueba de notas de crédito, anulaciones y devoluciones;
5. respaldo, auditoría y cierre.

Este documento es una guía técnica y no sustituye asesoría legal o tributaria.
# 10 — Esqueleto propuesto del repositorio

```text
smartdiag504/
├── apps/
│   ├── api/                     # FastAPI: dominio del taller y API pública/interna
│   ├── web/                     # React/TypeScript: operación administrativa
│   ├── technician-pwa/          # React/TypeScript: técnicos y bahías
│   ├── storefront/              # Landing, portal y e-commerce
│   └── worker/                  # Outbox, integración, alertas y tareas programadas
├── packages/
│   ├── domain-contracts/        # Tipos, estados, eventos y validaciones compartidas
│   ├── api-client/              # Cliente TypeScript generado desde OpenAPI
│   ├── ui/                      # Design system y componentes accesibles
│   ├── auth/                    # OIDC, permisos y sesión
│   └── observability/           # Logs, métricas y trazas
├── services/
│   ├── ai-rag/                  # Ingesta, ChromaDB, retrieval y gateway LLM
│   ├── notifications/           # Email, WhatsApp/SMS/push por adaptadores
│   └── control-plane/           # Licencias/versiones; sin datos operativos del cliente
├── integrations/
│   ├── erpnext/                 # Adaptador, mapeos, webhooks y conciliación
│   ├── fiscal-hn/               # Localización validada para Honduras
│   ├── payments/                # Proveedor configurable
│   └── messaging/               # Proveedor configurable
├── db/
│   ├── migrations/              # Migraciones PostgreSQL
│   ├── seeds/                   # Datos demo reproducibles
│   └── policies/                # RLS/aislamiento cuando aplique
├── contracts/
│   ├── openapi-outline.yaml
│   ├── events.yaml
│   ├── permissions.yaml
│   └── work-order-state-machine.yaml
├── infra/
│   ├── compose/                 # Desarrollo y despliegue sencillo
│   ├── kubernetes/              # Solo cuando el volumen lo justifique
│   ├── terraform/               # Infraestructura reproducible
│   └── monitoring/              # Métricas, logs, trazas y alertas
├── tests/
│   ├── contract/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   └── performance/
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── runbooks/
│   ├── decisions/
│   └── user-guides/
├── scripts/                     # Instalación, backup, restore, seed y diagnóstico
├── .github/workflows/           # CI, seguridad, build y releases
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
└── README.md
```

## Límites de módulos del backend

```text
app/
├── identity/
├── organizations/
├── customers/
├── vehicles/
├── appointments/
├── intake/
├── work_orders/
├── diagnostics/
├── estimates/
├── technicians/
├── parts/
├── quality/
├── delivery/
├── warranties/
├── alerts/
├── documents/
├── integrations/
├── assistant/
└── audit/
```

Cada módulo contiene:

- modelo de dominio;
- comandos y consultas;
- reglas/invariantes;
- repositorio o puerto;
- endpoints;
- eventos;
- pruebas.

## Contratos antes de código

1. Máquina de estados de OT.
2. Esquema de eventos versionados.
3. OpenAPI inicial.
4. Matriz de permisos.
5. Mapeo SmartDiag ↔ ERPNext.
6. Formato de idempotencia y correlación.
7. Política de errores y reintentos.

## Flujo de ramas y releases

- rama principal protegida;
- cambios por pull request;
- pruebas y escaneo obligatorios;
- migración junto al cambio de dominio;
- versionado semántico del producto y contratos;
- changelog generado por release;
- despliegue primero en staging con datos anonimizados/demo;
- rollback o forward-fix documentado.

## Configuración

- `.env.example` sin secretos.
- configuración validada al inicio.
- secretos por gestor del entorno.
- flags de función por cliente/plan.
- separación estricta de desarrollo, staging y producción.

## Orden recomendado de construcción

1. contratos y modelo de dominio;
2. identidad, organización y auditoría;
3. cliente/vehículo;
4. OT y estados;
5. recepción/diagnóstico/cotización;
6. técnicos/repuestos/QC;
7. adaptador ERP;
8. portal/tienda;
9. IA/alertas avanzadas;
10. comercialización y operación multi-cliente.
# 11 — Fuentes consultadas

Consultadas el 11 de agosto de 2026.

## SmartDiag504

- https://www.autoyas.com/HN/San-Pedro-Sula/100345348985381/SmartDiag504

## ERPNext y Frappe

- https://github.com/frappe/erpnext
- https://github.com/frappe/erpnext/wiki/Supported-Versions
- https://docs.frappe.io/erpnext/quotation
- https://docs.frappe.io/erpnext/selling
- https://docs.frappe.io/erpnext/pos-workflows
- https://docs.frappe.io/framework/user/en/basics/architecture
- https://docs.frappe.io/framework/user/en/api/background_jobs

## Alternativas y referencias

- https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/repairs/repair_orders.html
- https://www.odoo.com/documentation/19.0/applications/sales/point_of_sale.html
- https://www.odoo.com/documentation/19.0/applications/websites/ecommerce.html
- https://www.odoo.com/documentation/19.0/legal/licenses.html
- https://github.com/Beveren-Software-Inc/Field_Service_Management
- https://github.com/ChanMeng666/Automotive-Repair-Management-System
- https://github.com/dimitar-grigorov/GarageBuddy
- https://github.com/Dolibarr/dolibarr
- https://github.com/buildswithpaul/Frappe_Assistant_Core
- https://github.com/frappe/mcp

## Honduras — SAR

- https://www.sar.gob.hn/facturacion/
- https://www.sar.gob.hn/tramitesfacturacion/
- https://www.sar.gob.hn/ovi/
- https://www.sar.gob.hn/faqs/
