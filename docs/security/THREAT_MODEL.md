# Modelo de amenazas de SmartDiag504

## Activos críticos

1. Identidad de clientes, teléfonos, correos, VIN, placas e historial mecánico.
2. Evidencia: fotos, videos, firmas, DTC y documentos.
3. Inventario valorizado, compras, ventas, caja, facturas y contabilidad.
4. Credenciales de ERPNext, correo, pasarela, Garage/S3 y proveedores LLM.
5. Código, imágenes Docker, backups y registros de auditoría.
6. Disponibilidad del taller: agenda, OT, bahías, técnicos y entrega.

## Límites de confianza

```text
Internet
  │ TLS/Caddy
  ├── Web pública / portal / PWA
  ├── API pública con rate limit e idempotencia
  │
Red app interna
  ├── FastAPI / Frappe / WebSocket
  │
Red data interna
  ├── MariaDB / PostgreSQL / Valkey / ChromaDB / Garage S3
  └── workers y scheduler
```

No existe acceso directo desde el navegador hacia bases, Valkey, ChromaDB o la administración de Garage.

## Amenazas y controles

| Amenaza | Riesgo | Control requerido |
|---|---|---|
| Robo de credenciales | Fraude y exposición | MFA para administradores, contraseñas únicas, rotación, mínimo privilegio y bloqueo por intentos |
| Inyección/abuso API | Escritura o fuga | Validación Pydantic/Frappe, consultas parametrizadas, allowlist, límite de tamaño y rate limiting |
| Doble cobro/orden | Pérdida financiera | Idempotency-Key, referencia externa única, webhook firmado y conciliación |
| Manipulación de inventario | Pérdida y fraude | ERPNext como único ledger, segregación bodega/caja, auditoría inmutable y conteos |
| Acceso horizontal | Ver OT de otro cliente | Autorización por objeto, tokens de portal de corta vida y pruebas BOLA |
| Archivo malicioso | Ejecución o malware | MIME real, allowlist, tamaño máximo, bucket privado, URL firmada y antivirus como Gate de producción |
| Ransomware | Paralización | Backup 3-2-1, copia fuera del host, cifrado, restore drill y credenciales separadas |
| Dependencia comprometida | Ejecución de código | Pines, SBOM, escaneo de imágenes, revisión de forks y CI firmado |
| Prompt injection/RAG | Exfiltración o acción indebida | IA de lectura, herramientas allowlist, separación de instrucciones/documentos y auditoría |
| SSRF por importación de imagen | Acceso a metadatos/red interna | Solo HTTP(S), resolución/control de destino, bloqueo de redes privadas, límite de redirecciones/tamaño y copia server-side |
| Secuestro de sesión de chat | Suplantación/privacidad | token opaco con hash, TTL, cierre/revocación, rate limit y no guardar secretos en navegador |
| Split-brain de workers | Doble alerta/acción | lease con expiración, fencing token, idempotencia y test de pérdida de conectividad |
| Datos sensibles en LLM externo | Privacidad | Redacción/minimización, consentimiento, proveedor aprobado y opción local |
| Abuso de administrador | Fraude interno | MFA, logs, doble aprobación, alertas de cambios y revisión periódica |
| Caída de VPS | Indisponibilidad | A/B de proceso, healthchecks, monitoreo, backup externo y topología física con quorum cuando se requiera |

## Reglas de IA

- ChromaDB solo almacena conocimiento y embeddings; nunca reemplaza la base transaccional.
- El LLM no factura, cobra, consume inventario, aplica descuentos ni libera vehículos.
- Toda herramienta declara rol permitido, modo lectura y parámetros validados.
- Las fuentes recuperadas se tratan como datos no confiables, no como instrucciones.
- No enviar secretos, contraseñas, tokens o documentos completos innecesarios al proveedor.
- Registrar pregunta, usuario, herramientas, fuentes, modelo y resultado sin duplicar datos sensibles.

## E-commerce y pagos

- El navegador recibe un identificador de producto, precio mostrado y disponibilidad informativa.
- El servidor vuelve a calcular precio, impuesto, entrega y existencia al confirmar.
- La pasarela aloja o tokeniza datos de tarjeta; SmartDiag504 no almacena PAN/CVV.
- Los webhooks se validan criptográficamente, se procesan una vez y se concilian.
- Una aprobación de pago no equivale a entrega: primero se registra el documento ERPNext correspondiente.

## Roles mínimos

| Rol | Puede | No puede |
|---|---|---|
| Técnico | Diagnóstico, tiempos, evidencia, solicitar repuestos | Precio, factura, pago, cierre de caja |
| Bodega | Preparar, entregar, recibir devolución | Autorizar descuentos o cobrar |
| Asesor | Cliente, recepción, cotización, aprobación | Ajustar ledger o cerrar caja |
| Caja | Cobro, recibo, apertura/cierre | Cambiar diagnóstico o consumo técnico |
| Supervisor | Asignar, aprobar excepciones, QC | Borrar auditoría |
| Contabilidad | Configuración fiscal y conciliación | Alterar evidencia técnica |
| Administrador técnico | Configuración e infraestructura | Operar caja ordinaria sin control compensatorio |

## Respuesta a incidentes

1. Contener: bloquear cuenta/token, aislar servicio y conservar evidencia.
2. Clasificar: confidencialidad, integridad, disponibilidad y alcance.
3. Erradicar: rotar secretos, corregir vulnerabilidad y reconstruir imágenes.
4. Recuperar: restaurar, migrar, verificar y monitorear.
5. Notificar conforme a contratos y obligaciones aplicables.
6. Registrar causa raíz, línea de tiempo, impacto y acciones preventivas.

## Riesgos residuales antes de producción

- El fork Beveren aún necesita prueba integrada real sobre ERPNext v16.
- El catálogo, chat, pedidos y proyección operacional ya persisten en PostgreSQL; la sincronización financiera/inventario completa con ERPNext sigue siendo un Gate.
- El portal autenticado y la pasarela de pago no están habilitados como transacciones productivas.
- La importación de imágenes necesita antivirus y prueba SSRF de staging antes de publicar.
- Las imágenes Docker deben construirse, escanearse y firmarse en CI con acceso de red.
- La redundancia A/B en una VPS no cubre pérdida física; la topología de dos VPS requiere testigo y aceptación formal.
- La localización fiscal hondureña requiere validación profesional independiente.
