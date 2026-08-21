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
