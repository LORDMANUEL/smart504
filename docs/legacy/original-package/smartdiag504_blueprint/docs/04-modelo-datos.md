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
