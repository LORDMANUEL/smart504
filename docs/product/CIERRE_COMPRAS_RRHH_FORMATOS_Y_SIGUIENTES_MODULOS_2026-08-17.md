# Cierre de compras, RRHH, formatos y próximos módulos

## Resultado de esta fase

### Proveedores y compras

- Directorio por empresa con creación, activación/desactivación, datos fiscales, contacto, moneda y días de crédito.
- Orden de compra con múltiples líneas, tipo de cambio, fecha esperada, total y estados controlados.
- Recepción parcial o total por SKU, referencia única y observación.
- Cada recepción crea un comando idempotente para que ERPNext emita el `Purchase Receipt`; PostgreSQL conserva sólo la proyección operativa.
- El flujo visible queda: borrador → enviada → aprobada → recepción parcial/total → cerrada.

### Importaciones

- Expediente ligado a una orden aprobada.
- Incoterm, origen, puerto, ETA y método de distribución.
- Múltiples costos de flete, seguro, aduana, impuestos, manejo u otros.
- Registro de enlaces a BL, póliza, DUA, factura y soportes.
- Al asignar costos, ERPNext crea el `Landed Cost Voucher`; no se crea contabilidad local paralela.

### RRHH operacional

- Contrato con cargo, tipo, salario, horas semanales, horario y beneficios.
- Edición controlada y terminación con sincronización HRMS.
- Jornadas y horas regulares/extra.
- Las horas extra empiezan pendientes y sólo entran a nómina cuando RRHH las aprueba.
- Permisos con aprobación/rechazo.
- Borrador de nómina con salario, horas extra aprobadas, comisiones, bonos, asignaciones y deducciones.
- La aprobación envía el borrador a HRMS; asiento y pago siguen siendo autoritativos en ERPNext.

### Centro único de formatos

Ruta operativa: `/tallerv1/documentos`.

- Formatos por organización y opcionalmente por sucursal.
- Tipos: cotización, factura, diagnóstico, OT, garantía, pase de salida, picking, entrega, devolución y entrada de bodega.
- Carga de HTML UTF-8 y CSS opcional.
- Reemplazar genera una versión en borrador; publicar archiva la versión anterior.
- Vista previa aislada, variables permitidas, historial SHA-256 y descarga de respaldo JSON.
- Los documentos ya emitidos conservan la versión y hash usados.

## Módulos siguientes para completar el producto

### Prioridad 0: integridad antes de producción

1. Conciliación ERP integral de OT, existencias, facturas, pagos y compras.
2. Aislamiento multiempresa automatizado en cada endpoint y pruebas negativas entre empresas.
3. Fiscalidad hondureña validada por contador: CAI, rangos, exentos/gravados, nota de crédito y papel preimpreso.
4. Evidencia privada S3/Garage, antivirus, autorización por OT y retención.
5. Backup externo cifrado y restauración periódica en infraestructura diferente al VPS de pruebas.

### Prioridad 1: operación diaria

1. Solicitud interna de compra → RFQ → comparación de proveedores → orden aprobada.
2. Devolución a proveedor, discrepancias de recepción y cuentas por pagar visibles desde ERP.
3. Inventario con códigos de barras, conteos cíclicos, lotes/series y reposición ABC/XYZ.
4. Turnos y marcación física, vacaciones acumuladas, incapacidades documentadas y horas extra por supervisor.
5. Productividad del técnico ligada a horas vendidas, ejecutadas y calidad, sin usarla como única medida laboral.

### Prioridad 2: crecimiento

1. Flotas y contratos empresariales con tarifas, límites de crédito y SLA.
2. Comercio electrónico con adquirente real, reserva de inventario, flete y devoluciones.
3. CRM automatizado con consentimiento, seguimiento y atribución de campaña.
4. Compra/consignación/venta de usados con expediente legal y margen conciliado.
5. Reportería por empresa/sucursal: utilidad por OT, productividad, rotación, compras, caja y estados ERP.

### Prioridad 3: facilidad de uso

1. Asistente de configuración inicial por empresa.
2. Búsqueda global por VIN, placa, cliente, SKU, OT, factura y pedido.
3. Centro de tareas y aprobaciones por rol.
4. Ayuda contextual y tutorial guiado medible en cada módulo.
5. Importadores Excel con vista previa, errores por fila y reversión controlada.

## Definición de terminado

Un módulo no se declara terminado sólo porque abre una pantalla. Debe tener persistencia autoritativa, aislamiento por empresa, permisos de servidor, auditoría, idempotencia, documentos/notificaciones aplicables, estados vacíos/error/carga, pruebas API y UI servida, conciliación ERP y manual operativo.
