# Backlog por épicas — SmartDiag504

## Convención

- **P0:** bloquea piloto o integridad.
- **P1:** necesario para operación completa.
- **P2:** optimización/diferenciación.
- Cada épica termina en un Gate verificable, no en “pantallas terminadas”.

## E00 — Certificación de plataforma base (P0)

**Objetivo:** demostrar instalación limpia y reproducible.

- Construir imagen Frappe v16.
- Aplicar parche Beveren fijado.
- Crear sitio, instalar apps y migrar.
- Probar `process_item_selection`, impuestos, UOM, seriales y bodegas.
- Escanear imágenes y generar SBOM.
- Ejecutar backup/restore en staging.

**Aceptación:** Gate 0 y Gate 1 de `CODEX_EXECUTION_GUIDE.md` aprobados.

## E01 — Identidad, clientes y vehículos (P0)

- Adaptador Customer/Contact/Address.
- VIN único, placa, propietario e historial.
- Transferencia de propietario auditada.
- Consentimientos y deduplicación.
- Búsqueda por VIN, placa, teléfono y nombre.

**Aceptación:** AT-WORKSHOP-001.

## E02 — Agenda y recepción digital (P0)

- Capacidad por sucursal/bahía/técnico.
- Reserva web idempotente.
- Check-in, fotos, daños, combustible y firma.
- Almacenamiento S3 privado y antivirus.
- Promesa de entrega y notificaciones.

**Aceptación:** reserva no duplica cita y recepción completa abre `Service Order`.

## E03 — Diagnóstico y cotización (P0)

- DTC, pruebas, valores, hallazgos y evidencia.
- Catálogo de mano de obra.
- Cotización versionada.
- Aprobación/rechazo por línea.
- Trabajos adicionales.
- Margen visible solo por rol.

**Aceptación:** AT-WORKSHOP-002.

## E04 — Planificación, técnicos y bahías (P0)

- Operaciones y varios técnicos.
- Cronómetro, pausas y conflictos.
- Tablero de bahías y promesa de entrega.
- Productividad, eficiencia y costo interno.
- Offline controlado en PWA.

**Aceptación:** AT-WORKSHOP-003.

## E05 — Repuestos, bodega y compras (P0)

- Solicitud, reserva, picking, entrega, confirmación.
- Consumo y devolución.
- Core/pieza usada.
- Pedido especial, compra y recepción.
- Códigos QR/barra.
- Conciliación ERPNext.

**Aceptación:** AT-WORKSHOP-004 sin diferencias.

## E06 — Calidad, factura, caja y entrega (P0)

- Checklists por servicio.
- QC fallido/corrección/reprueba.
- Factura desde líneas autorizadas.
- Anticipo, pagos, POS y cierre de caja.
- Firma de entrega y mantenimiento futuro.

**Aceptación:** AT-WORKSHOP-005 y fiscalidad aprobada.

## E07 — Garantía y retrabajo (P1)

- Cobertura por operación/repuesto.
- OT enlazada.
- Reincidencia vs falla nueva.
- Costo y causa raíz.
- KPI de comeback/retrabajo.

**Aceptación:** AT-WORKSHOP-006.

## E08 — Tienda de repuestos (P0 comercial)

- Catálogo ERPNext real.
- Compatibilidad y pedido especial.
- Carrito persistente seguro.
- Reserva de stock.
- Checkout, entrega y pasarela.
- Webhooks/reembolsos/idempotencia.
- SEO, analítica y legal.

**Aceptación:** AT-STORE-001/002.

## E09 — Portal del cliente (P1)

- Autenticación y autorización por objeto.
- Vehículos, historial y estado de OT.
- Aprobación digital.
- Evidencias, facturas y pagos.
- Citas y garantías.

**Aceptación:** pruebas BOLA/IDOR y flujo de aprobación completo.

## E10 — Alertas y comunicación (P1)

- Outbox transaccional.
- Streams/grupos/reintentos/dead-letter.
- Reglas operativas.
- Email/WhatsApp/push con plantillas y consentimiento.
- Escalamiento y SLA.

**Aceptación:** evento duplicado produce un solo efecto y queda conciliado.

## E11 — IA/RAG segura (P2 diferenciador)

- Ingestión con permisos/versiones.
- Búsqueda técnica con citas.
- Resumen de recepción/diagnóstico.
- Casos similares.
- Herramientas read-only.
- Evaluaciones y defensa prompt injection.

**Aceptación:** suite de seguridad IA y auditoría completa.

## E12 — Reportería y rentabilidad (P1)

- Margen por OT/servicio/repuesto.
- Productividad por técnico.
- Conversión de cotización.
- Tiempo por estado/bahía.
- Retrabajos/garantías.
- Inventario lento/faltantes.
- Flujo de caja/P&L desde ERPNext.

**Aceptación:** totales concilian con documentos y ledger ERPNext.

## E13 — Seguridad, SRE y continuidad (P0)

- MFA, roles y segregación.
- Rate limit/WAF y hardening.
- Observabilidad y alertas.
- Backups cifrados externos.
- Restore drills y runbooks.
- Escaneo/SBOM/firmas.
- Carga, capacidad y DR.

**Aceptación:** AT-RECOVERY y aprobación de amenaza/riesgos.

## E14 — Producto multiempresa (P2)

- Instalador por cliente/sitio.
- Branding/configuración sin fork por cliente.
- Planes, límites y metering.
- Actualizaciones por canales.
- Soporte, telemetría consentida y SLA.

**Aceptación:** dos sitios aislados, upgrade/rollback y cero cruce de datos.
