# Propiedad y ciclo de vida de los datos

## Principio

Cada concepto tiene un solo sistema autoritativo. Las otras capas guardan referencias, proyecciones regenerables o eventos; nunca un segundo ledger.

| Concepto | Sistema autoritativo | Copias permitidas | Escritura autorizada |
|---|---|---|---|
| Cliente y direcciones | ERPNext/Frappe | proyección portal/cache | Frappe y adaptador validado |
| Vehículo, VIN e historial técnico | `smartdiag_workshop` en MariaDB | índice de búsqueda/eventos | Frappe app |
| Recepción y evidencia técnica | `smartdiag_workshop` + Garage/S3 | miniaturas/cache | Frappe app/API firmada |
| OT, cita y ejecución | Beveren `Service Order`/Appointment | proyección PWA/eventos | Beveren + extensión SmartDiag |
| Cotización operativa | Beveren Service Quotation | PDF/eventos | Frappe app |
| Artículo y precio | ERPNext Item/Price List | caché de catálogo | ERPNext |
| Existencia y valoración | ERPNext Bin/Stock Ledger | disponibilidad web derivada | ERPNext documentos de stock |
| Compra/proveedor | ERPNext | reportes | ERPNext |
| Factura/nota | ERPNext | PDF/proyección portal | ERPNext |
| Pago/caja/banco | ERPNext | eventos de conciliación | ERPNext |
| Alertas e idempotencia | PostgreSQL plataforma | cache Valkey | servicios plataforma |
| Auditoría IA | PostgreSQL plataforma | retención/archivo | ai-gateway |
| Conocimiento/embeddings | ChromaDB | fuente original en S3/Docs | proceso de ingestión |
| Colas/caché/locks | Valkey | ninguna copia obligatoria | servicios autorizados |

## Regla de integración

```text
Frontend → platform-api/Frappe → documento autoritativo
                             ↘ outbox/evento → PostgreSQL/Valkey → consumidores
```

Ningún frontend se conecta a MariaDB, PostgreSQL, Valkey, ChromaDB o Garage con credenciales administrativas.

## Escrituras ERPNext

Toda escritura originada fuera de Frappe requiere:

1. identidad/rol;
2. validación Pydantic y de negocio;
3. clave de idempotencia;
4. `external_reference` única;
5. llamada al adaptador Frappe;
6. persistencia de resultado;
7. evento de salida;
8. conciliación posterior.

No se considera exitosa hasta recibir y registrar el identificador del documento ERPNext.

### Contrato aplicado a la OT

- Cada alta o modificación técnica genera un comando `UPSERT_SERVICE_ORDER` con clave idempotente.
- El payload incluye estado, diagnóstico, técnicos, bahía, repuestos, mano de obra y metadatos sanitizados de evidencias.
- Con `FRAPPE_REQUIRED=true`, la petición procesa su trabajo específico y sólo devuelve éxito cuando queda `SYNCED` con `erpnext_service_order_id`.
- Un fallo conserva la proyección y el trabajo `FAILED` para auditoría/reintento; nunca inventa una referencia ERP.
- `POST /api/v1/operations/work-orders/{id}/reconcile` lee por `sd_external_reference`, valida el estado Beveren y actualiza la proyección con eventos `ERP_RECONCILED` idempotentes.
- Los campos extendidos de Frappe usan exclusivamente el prefijo `sd_platform_*`.

## Outbox y eventos

Los cambios de negocio crean un registro `SmartDiag Event Outbox` en la misma transacción Frappe. Un publicador:

- construye `event_key` determinista;
- firma el payload;
- publica en API/stream;
- marca entrega/intentOS;
- reintenta con backoff;
- mueve a dead-letter al superar la política;
- nunca elimina la evidencia de fallo.

Los consumidores deben ser idempotentes por `event_key`.

## Archivos

- El objeto se almacena privado en Garage/S3.
- La base guarda bucket, key, hash, MIME, tamaño, propietario, contexto y estado antivirus.
- Las descargas usan autorización por objeto y URL corta/stream controlado.
- Borrar un documento de negocio no borra evidencia automáticamente; aplica retención/aprobación.
- Backups copian objetos con rclone y validan manifiesto.

## Retención inicial a validar legalmente

| Dato | Política técnica inicial |
|---|---|
| Auditoría financiera | según obligación fiscal/contable aprobada |
| Evidencia de OT | vida útil contractual + periodo de reclamación |
| Logs de seguridad | 12 meses, con minimización |
| Auditoría IA | 90–365 días según sensibilidad |
| Carrito/cache | TTL corto y regenerable |
| Backups | 14 diarios + política mensual externa |

Los plazos finales requieren revisión legal y fiscal hondureña.
