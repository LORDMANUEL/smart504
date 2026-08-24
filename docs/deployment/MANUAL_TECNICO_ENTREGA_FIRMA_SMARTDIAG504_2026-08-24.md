# SmartDiag504 — Manual técnico de entrega, operación y firma

**Versión documental:** 1.0  
**Fecha de corte:** 2026-08-24  
**Repositorio:** `https://github.com/LORDMANUEL/smart504`  
**VPS entregado:** `169.58.217.146`  
**Orquestador:** Coolify sobre Docker  
**Dominio temporal:** `169.58.217.146.sslip.io`  
**Zona horaria de negocio:** `America/Tegucigalpa`

> Este manual documenta responsabilidades, integración, operación, diagnóstico y
> recuperación. No contiene contraseñas, tokens ni llaves privadas. Los secretos
> se entregan por un gestor de contraseñas y se rotan al cambiar de custodio.

## 1. Objeto de la entrega

SmartDiag504 reúne en una sola experiencia:

- landing, catálogo, tienda, citas y portal del cliente;
- operación de taller, técnicos, bahías, OT y evidencia fotográfica;
- cotizaciones, mostrador, caja, POS externo y documentos imprimibles;
- bodegas, reservas, picking, devoluciones y solicitudes de compra;
- compras, proveedores, importación y costo aterrizado;
- RRHH, asistencia, permisos, nómina y autoservicio del empleado;
- CRM, publicidad, calidad, flujos, reportes e IA local;
- ERPNext/Beveren como fuente autoritativa financiera y operativa;
- almacenamiento privado, antivirus, auditoría y copias locales verificadas.

La entrega es operativa por IP con TLS temporal. El correo transaccional definitivo
queda condicionado al dominio, PTR, MX, SPF, DKIM y DMARC.

## 2. Firmantes y responsabilidades

| Rol | Responsabilidad de aceptación |
|---|---|
| Propietario | Aprueba alcance, riesgo de respaldo local y usuarios autorizados. |
| Administrador técnico | Custodia Coolify, SSH, secretos, despliegues y restauración. |
| Contador | Configura papel preimpreso, correlativos, impuestos, cuentas y cierres. |
| Gerencia del taller | Valida flujos, permisos, tiempos, precios y responsables. |
| Encargado de caja | Calibra Epson L3250, prueba talonario y referencias POS. |
| Encargado de datos | Mantiene catálogo, VIN, repuestos, imágenes y calidad del maestro. |

## 3. Accesos de operación

| Superficie | URL temporal | Uso |
|---|---|---|
| Landing/tienda | `https://taller.169.58.217.146.sslip.io/lading` | Promoción, catálogo, venta y cita pública. |
| Portal cliente | `https://clientes.169.58.217.146.sslip.io/lading/cliente` | Vehículos, citas, alertas, aprobaciones y documentos. |
| Operaciones | `https://app.169.58.217.146.sslip.io/tallerv1/login` | Taller, ventas, caja, bodega y administración. |
| ERPNext | `https://erp.169.58.217.146.sslip.io` | Administración, ledger, inventario, compras y contabilidad. |
| Salud API | `https://api.169.58.217.146.sslip.io/ready` | Estado técnico agregado. |
| Coolify | `http://169.58.217.146:8000` | Contenedores, variables, logs y despliegues. |

Las credenciales de aceptación viven temporalmente en el VPS bajo
`/root/.config/smartdiag504/`, con permisos `0600`. No deben copiarse al repositorio
ni a este manual. El administrador crea usuarios personales, prueba sus roles y
elimina las credenciales compartidas.

## 4. Arquitectura entregada

```text
Navegador
   │ HTTPS
   ▼
Coolify / Traefik
   │
   ▼
HAProxy interno
   ├── public-web A/B ── landing, tienda y cliente
   ├── ops-web A/B ───── operación por rol
   ├── platform-api A/B ─ PostgreSQL / Valkey
   │                       │
   │                       ├── adaptador ERP ── ERPNext/Beveren ── MariaDB
   │                       ├── Garage S3 privado
   │                       ├── ClamAV
   │                       └── AI Gateway A/B ── Ollama + ChromaDB
   └── Frappe frontend ─── escritorio ERP en español
```

### 4.1 Regla de propiedad de datos

| Dato | Fuente de verdad | Proyección permitida |
|---|---|---|
| Cliente, proveedor, artículo y precio | ERPNext | Búsqueda y UX en PostgreSQL. |
| Vehículo e historial técnico | SmartDiag Workshop/Frappe | Índice operativo. |
| OT | Beveren `Service Order` | Kanban y detalle en PostgreSQL. |
| Cotización | Beveren `Service Quotation` | Edición UX, HTML/PDF y estado. |
| Existencia y costo | ERPNext Stock Ledger | Disponibilidad derivada. |
| Factura, pago y nota de crédito | ERPNext | Portal, impresión y auditoría. |
| Sesión, CRM, campaña, flujo y auditoría | PostgreSQL | No requiere ledger ERP. |
| Evidencia y archivos | Garage/S3 privado | Metadatos y hash en base. |
| Embeddings | ChromaDB | Fuente original conservada. |

Nunca se corrige una diferencia creando otro documento. Se reintenta o reconcilia
la misma referencia idempotente.

## 5. Cómo se une SmartDiag504 con ERPNext

### 5.1 Camino de escritura

```text
Usuario → interfaz SmartDiag → API valida sesión/empresa/sucursal
        → crea comando con idempotency_key
        → adaptador Frappe crea o actualiza documento ERP
        → ERP devuelve identificador
        → PostgreSQL guarda referencia y estado SYNCED
        → evento auditable actualiza vistas y notificaciones
```

Estados de integración:

- `PENDING`: registrado y pendiente de ERP.
- `SYNCED`: ERP confirmó identificador autoritativo.
- `FAILED`: fallo conservado; puede reintentarse.
- `BLOCKED`: requiere corrección humana o configuración.

### 5.2 Contratos por operación

| Operación SmartDiag | Documento ERP | Resultado exigido |
|---|---|---|
| Crear/editar OT | `Service Order` | `erpnext_service_order_id`. |
| Cotizar servicio | `Service Quotation` | referencia ERP y versión. |
| Venta mostrador | `Sales Invoice` | factura sometida. |
| Cobro | `Payment Entry` | referencia y conciliación. |
| Devolución | nota de crédito/reembolso | documento enlazado a venta. |
| Entrega/traslado | `Stock Entry` | movimiento sometido. |
| Compra | `Purchase Order/Receipt/Invoice` | cadena documental enlazada. |
| Nómina aprobada | documentos HRMS/ERP | contabilización separada por rol. |

### 5.3 Idempotencia

`services/platform-api/app/services/erp_outbox.py` evita duplicar operaciones:

1. recibe organización, agregado, operación, clave y payload;
2. busca una clave existente dentro de la empresa;
3. devuelve el trabajo existente si ya fue creado;
4. crea un solo `ErpIntegrationJob` si no existe;
5. conserva intentos, error, referencia y próxima ejecución.

### 5.4 Reintento y reparación

Desde un rol administrador:

1. abrir **Administración → Integración ERP**;
2. filtrar `FAILED` o `BLOCKED`;
3. leer `last_error` y verificar configuración/dato de origen;
4. corregir el dato autoritativo, no la tabla de proyección;
5. pulsar reintentar sobre el mismo trabajo;
6. ejecutar procesamiento si la cola no lo toma automáticamente;
7. confirmar `SYNCED` y la referencia ERP;
8. abrir el documento en ERPNext y comprobar asiento/stock cuando aplique.

API administrativa relacionada:

- `GET /api/v1/operations/integrations/erp/jobs`
- `POST /api/v1/operations/integrations/erp/jobs/{id}/retry`
- `POST /api/v1/operations/integrations/erp/process`
- `POST /api/v1/operations/work-orders/{id}/reconcile`

No debe editarse directamente MariaDB o PostgreSQL para “forzar” una conciliación.

## 6. Relación entre vistas y ERP

| Vista | Acción del usuario | Escritura autoritativa |
|---|---|---|
| Técnico | Diagnóstico, tiempo, fotos, repuestos | Service Order + evidencia privada. |
| Kanban | Cambiar estado OT | transición validada de Service Order. |
| Cotizaciones | VIN, mano de obra, repuestos, aprobación | Service Quotation. |
| Mostrador | Buscar por VIN/SKU, vender | Sales Invoice + Payment Entry. |
| Caja | Abrir, cobrar, cerrar, arquear | pago/factura ERP y sesión auditada. |
| Bodega | Reservar, picking, entregar, devolver | Stock Entry/ledger ERP. |
| Compras | Solicitud, proveedor, orden, recepción | cadena de compras ERP. |
| RRHH | asistencia, permiso, nómina | HRMS/ERP según aprobación. |
| Portal cliente | cita, aprobación, historial | documento de taller enlazado. |
| Gerencia | KPI y reportes | lectura reconciliada ERP + eventos. |

## 7. Inventario de componentes construidos

### 7.1 Aplicaciones

| Ruta de código | Responsabilidad | Reparación inicial |
|---|---|---|
| `apps/public-web` | Landing, tienda, citas y cliente. | Revisar consola, API pública y configuración de rutas. |
| `apps/ops-web` | Operaciones y lanzador por rol. | Revisar sesión, permisos, API y estado vacío/error. |
| `services/platform-api` | Autenticación, BFF, proyecciones, documentos e integración. | Revisar `/ready`, logs y trabajos ERP. |
| `services/ai-gateway` | IA local, RAG y límites de cliente. | Revisar Ollama, Chroma y token interno. |
| `frappe-apps/smartdiag_workshop` | DocTypes, hooks, workspace y eventos ERP. | Ejecutar migración controlada y revisar scheduler. |
| `packages/smartdiag_domain` | Reglas puras compartidas. | Validar pruebas de dominio en CI/VPS. |

### 7.2 Rutas API documentadas

| Archivo | Dominio |
|---|---|
| `routes/public_catalog.py` | catálogo y compatibilidad pública. |
| `routes/store.py` | carrito, pedidos y gestión de venta web. |
| `routes/client_auth.py` | identidad y capacidades del cliente. |
| `routes/client_appointments.py` | citas autenticadas. |
| `routes/client_portal.py` | vehículos, historial, alertas y aprobaciones. |
| `routes/client_documents.py` | documentos del cliente. |
| `routes/work_orders.py` | OT, diagnóstico, fotos, tiempo y conciliación. |
| `routes/admin_catalog.py` | repuestos, mano de obra, vehículos e imágenes. |
| `routes/catalog_import.py` | Excel con vista previa y aplicación. |
| `routes/finance.py` | cotización, caja, mostrador, pago y devolución. |
| `routes/document_templates.py` | HTML/CSS, versiones, vista previa y publicación. |
| `routes/enterprise.py` | compras, importación, RRHH y módulos empresariales. |
| `routes/hr_self_service.py` | marcación, permisos y vouchers. |
| `routes/operations_control.py` | bodegas, calidad, CRM y flujos. |
| `routes/marketing.py` | campañas, medios, publicación y clics. |
| `routes/notifications.py` | outbox y entregas. |
| `routes/erp_integration.py` | observación, reintento y procesamiento ERP. |
| `routes/flow_events.py` | trazabilidad y mapa de calor. |
| `routes/staff.py` | usuarios, roles, MFA y auditoría. |
| `routes/settings.py` | marca y compuertas de producción. |

### 7.3 Evolución de datos

Las migraciones `0001` a `0033` son el historial ejecutable de la base. Cubren:

- núcleo, chat, pedidos y catálogo;
- eventos, caja, documentos y mostrador;
- RBAC, multiempresa e integración ERP;
- notificaciones, autoridad de inventario y empresa;
- compras, RRHH, nómina y autoservicio;
- solicitudes de artículos, mano de obra y registro de clientes;
- separación de funciones y crédito.

Regla: agregar una migración nueva; nunca editar una ya aplicada en producción.

### 7.4 Servicios Docker principales

| Servicio | Función | Persistencia |
|---|---|---|
| `haproxy` | balanceo A/B interno | configuración declarativa. |
| `public-web-a/b` | capa pública redundante | sin estado. |
| `ops-web-a/b` | capa operativa redundante | sin estado. |
| `platform-api-a/b` | API redundante | sin estado local. |
| `platform-migrate` | Alembic antes de API | PostgreSQL. |
| `platform-bootstrap` | sucursal, bodegas, formatos y marca | idempotente. |
| `postgres` | proyecciones, sesiones y auditoría | volumen PostgreSQL. |
| `mariadb` | datos ERPNext/Frappe | volumen MariaDB. |
| `frappe-*` | backend, frontend, colas, scheduler y socket | sitios/logs. |
| `redis-platform` | caché/locks de plataforma | AOF. |
| `redis-cache/queue` | caché y colas Frappe | volúmenes según servicio. |
| `garage` | objetos S3 privados | config, meta y data. |
| `clamav` | análisis de cargas | firmas antivirus. |
| `ollama` | modelo local | volumen del modelo. |
| `chromadb` | índice RAG | volumen Chroma. |
| `ai-gateway-a/b` | acceso controlado a IA | sin estado propio. |

## 8. Plantillas y documentos

Se entregan 33 plantillas: 11 documentos por tres perfiles.

Documentos: cotización, factura, diagnóstico, OT, garantía, pase de salida,
picking, entrega, devolución, entrada de bodega y voucher de pago.

Perfiles:

- `BRANDED`: logo y colores SmartDiag504;
- `PREPRINTED`: contenido variable sobre papel autorizado;
- `PDF`: archivo digital tamaño Carta.

Cada publicación conserva versión, HTML, CSS, perfil, variables, autor, fecha y
hash del render. Reemplazar significa crear y publicar una nueva versión; los
documentos históricos conservan la anterior.

El logo canónico se copia durante `platform-bootstrap` a medios privados y se
incrusta como `data:image/png;base64` para que el PDF no dependa de Internet.

### Epson L3250

1. Instalar controlador Epson en la computadora de caja.
2. Papel Carta, vertical, escala 100 %.
3. Desactivar “ajustar a página”.
4. Imprimir hoja de calibración.
5. Ajustar márgenes de la plantilla, no el histórico.
6. Para factura, seleccionar perfil preimpreso.

### POS bancario

El datáfono es externo. Caja selecciona Tarjeta/POS y exige la referencia bancaria.
SmartDiag504 no captura PAN, CVV, PIN ni datos de banda o chip.

## 9. Operación de Coolify

Aplicaciones:

- núcleo: Compose `compose.coolify.yaml`;
- auxiliares: Compose `compose.coolify-extras.yaml`.

Un despliegue correcto sigue:

1. obtener commit aprobado;
2. construir imágenes inmutables;
3. fijar digest en variables Coolify;
4. ejecutar migraciones;
5. ejecutar bootstrap idempotente;
6. migrar/inicializar Frappe;
7. esperar salud A/B;
8. conmutar tráfico;
9. comprobar rutas y flujos autenticados;
10. registrar UUID, commit y evidencia.

No reiniciar Coolify ni Traefik compartido para reparar SmartDiag504.

## 10. Diagnóstico y reparación

### 10.1 Pantalla en blanco

1. comprobar HTTP de la ruta;
2. abrir consola/red del navegador;
3. verificar que el bundle corresponde al commit;
4. comprobar API y CORS;
5. validar sesión y rol;
6. revisar estados `loading`, `empty`, `error` y permisos;
7. corregir y desplegar imagen nueva, nunca editar el contenedor.

### 10.2 API no saludable

1. abrir `/ready`;
2. identificar componente diferente de `ok`;
3. revisar logs de ambas réplicas;
4. comprobar PostgreSQL, Valkey, S3, Frappe, IA y esquema por separado;
5. si cambió una variable, redesplegar sólo la aplicación afectada;
6. no borrar volúmenes como intento de reparación.

### 10.3 ERP devuelve 403

1. identificar usuario de integración y DocType;
2. comprobar rol y permiso en Frappe;
3. validar empresa/sucursal del documento;
4. confirmar API key activa sin mostrarla;
5. repetir una lectura acotada;
6. reintentar el trabajo idempotente.

### 10.4 ERP devuelve 404

1. confirmar hostname del sitio Frappe;
2. usar `FRAPPE_BASE_URL` con el sitio correcto;
3. verificar instalación de `erpnext`, `beveren_fsm` y `smartdiag_workshop`;
4. comprobar que el DocType existe después de `bench migrate`;
5. no crear un DocType paralelo para ocultar el error.

### 10.5 Documento ERP no aparece en SmartDiag

1. buscar trabajo ERP por referencia externa;
2. distinguir `FAILED` de “no encontrado”;
3. ejecutar conciliación;
4. revisar eventos outbox/dead-letter;
5. confirmar aislamiento por empresa y sucursal;
6. registrar causa y corrección.

### 10.6 Inventario diferente

ERPNext es autoritativo. Comparar Item, Warehouse, Bin, Stock Ledger y movimiento
de origen. Corregir/reconciliar el documento ERP; no ajustar el balance local.

### 10.7 Impresión desalineada

Verificar tamaño Carta, escala, controlador y orientación. Crear una nueva versión
de plantilla con margen corregido, previsualizar, imprimir prueba y publicar.

### 10.8 Carga rechazada

Verificar tamaño, MIME, extensión, hash y resultado ClamAV. No desactivar el
antivirus; corregir el archivo o actualizar firmas.

### 10.9 IA lenta o sin respuesta

Comprobar `ai-gateway`, Ollama, modelo, memoria y Chroma. Mantener fallback estático
para consultas frecuentes. La IA no debe ejecutar escrituras financieras.

## 11. Logs y trazabilidad

| Evidencia | Ubicación lógica | Uso |
|---|---|---|
| despliegue | Coolify | commit, salida y estado. |
| contenedor | logs Docker/Coolify | diagnóstico por servicio. |
| acceso personal | `StaffAccessEvent` | inicio, fallo, bloqueo y MFA. |
| flujo | `FlowEvent` | acción, módulo, actor, resultado. |
| integración | `ErpIntegrationJob` | intento, error y referencia ERP. |
| documento | versión/render | HTML, CSS, hash y autor. |
| Frappe outbox | SmartDiag Event Outbox | evento ERP idempotente. |
| seguridad | Fail2ban/host | intentos y bloqueos SSH. |

Los actores deben provenir de la sesión. No usar `cajero-demo`, `tecnico-demo` o
identidades enviadas por el navegador como autoridad.

## 12. Respaldo y restauración

Temporizador: `smartdiag504-local-snapshot.timer`.  
Ruta: `/var/backups/smartdiag504-local`.  
Retención: 14 días.

Incluye PostgreSQL, MariaDB, sitios Frappe, Garage config/meta/data y manifiesto.
Cada ejecución restaura PostgreSQL en una base temporal, cuenta tablas y elimina
la restauración.

Comprobación:

```bash
systemctl status smartdiag504-local-snapshot.timer
systemctl show smartdiag504-local-snapshot.service -p Result -p ExecMainStatus
readlink -f /var/backups/smartdiag504-local/latest
cd /var/backups/smartdiag504-local/<snapshot>
sha256sum -c manifest.sha256
cat VERIFIED
```

Riesgo aceptado: al estar en el mismo VPS, no protege contra pérdida total del
servidor, cuenta o proveedor.

## 13. Seguridad operativa

- secretos sólo en Coolify o archivos root `0600`;
- TLS mediante Traefik/Coolify;
- contenedores con capacidades reducidas y `no-new-privileges`;
- MFA configurable y sesiones revocables;
- aislamiento por organización y sucursal;
- S3 privado con autorización por objeto;
- ClamAV obligatorio para cargas;
- rate limiting, bloqueo de intentos y Fail2ban;
- no exponer bases, Valkey, Ollama, Chroma o Garage a Internet;
- no registrar tokens, cookies, contraseñas o datos bancarios en logs.

## 14. Mantenimiento y cambios

1. crear rama `codex/<cambio>`;
2. escribir/actualizar prueba;
3. editar código localmente sin ejecutarlo;
4. ejecutar gates en VPS/CI;
5. revisar migraciones y compatibilidad;
6. construir imagen con digest;
7. tomar snapshot;
8. desplegar por Coolify;
9. validar por rol y conciliar ERP;
10. documentar evidencia y actualizar este manual si cambia arquitectura.

No se documenta cada línea obvia con comentarios que repitan el código. Cada
unidad construida sí debe tener contrato, razón, propietario, errores, pruebas y
referencia de archivo. Los comentarios en código explican decisiones no evidentes.

## 15. Matriz de aceptación de entrega

| Control | Evidencia de corte | Estado |
|---|---|---|
| Web pública | HTTP 200 | Aceptado |
| Portal cliente | HTTP 200 | Aceptado |
| Operaciones | HTTP 200 | Aceptado |
| ERPNext | ping HTTP 200 | Aceptado |
| API | DB, Valkey, S3, Frappe, esquema, IA y seguridad `ok` | Aceptado |
| ERP/Beveren | migración e inicialización código 0 | Aceptado técnico |
| Documentos | 33 plantillas, 11 publicadas | Aceptado |
| Logo | PNG embebido en vista previa | Aceptado |
| Sucursal/bodegas | MAIN + 4 bodegas | Aceptado |
| Impresión | perfil Epson L3250/preimpreso | Pendiente prueba física firmada |
| POS | referencia obligatoria; sin datos de tarjeta | Pendiente prueba con banco |
| Fiscal | modo preimpreso | Pendiente aprobación del contador |
| Respaldo | hashes correctos y 62 tablas restauradas | Aceptado con riesgo local |
| SMTP | dominio/DNS no disponibles | Pendiente externo |

## 16. Evidencia técnica de referencia

- Despliegue Coolify: `3xpax8lkbxxrdodaqamtv9un`, estado `finished`.
- Commit de aplicación validado: `f264649`.
- Commit documental de evidencia: `763da88`.
- CI y construcción de imágenes: `success`.
- Snapshot validado: `20260824T032425Z`.
- Tablas restauradas: `62`.
- Compuertas productivas: `9/10`; pendiente `SMTP`.

## 17. Acta de entrega y firma

### Declaración del proveedor técnico

Se entrega el código fuente, definición de contenedores, migraciones, manuales,
configuración temporal por IP y evidencia descrita. Los secretos no se incluyen
en el repositorio. Las reservas externas y físicas permanecen señaladas.

**Nombre:** __________________________________________  
**Cargo:** ___________________________________________  
**Identidad:** _______________________________________  
**Firma:** ___________________________________________  
**Fecha y hora:** ____________________________________

### Declaración del propietario/cliente

Declaro haber recibido el sistema y este manual. Comprendo que SMTP/dominio,
aprobación fiscal, calibración física de la Epson L3250 y prueba del POS requieren
participación de terceros; también acepto temporalmente que el respaldo está en
el mismo VPS.

**Nombre:** __________________________________________  
**Cargo:** ___________________________________________  
**Identidad:** _______________________________________  
**Firma:** ___________________________________________  
**Fecha y hora:** ____________________________________

### Validación del contador

**Modo:** ☐ preimpreso ☐ ERP/autoimpresión  
**Talonario/rango verificado:** ☐ sí ☐ no ☐ no aplica  
**Impuestos y cuentas revisados:** ☐ sí ☐ no  
**Observaciones:** ________________________________________________  
**Nombre y firma:** ______________________________________________  
**Fecha:** _______________________________________________________

### Validación de caja

**Epson L3250 calibrada:** ☐ sí ☐ no  
**Prueba en papel real:** ☐ aprobada ☐ rechazada  
**POS y referencia bancaria:** ☐ aprobados ☐ pendientes  
**Nombre y firma:** ______________________________________________  
**Fecha:** _______________________________________________________

## 18. Reservas abiertas al firmar

1. SMTP productivo depende del dominio, PTR y DNS de correo.
2. Fiscalidad final depende del contador y documentos autorizados.
3. Epson/POS requieren prueba física en la sucursal.
4. El respaldo local no cubre pérdida completa del VPS.
5. Toda nueva empresa requiere parametrización, usuarios y aislamiento validados.

Una reserva sólo se cierra con evidencia fechada y firma del responsable.

## 19. Documentos relacionados

- `ARCHITECTURE.md`
- `docs/architecture/DATA_OWNERSHIP.md`
- `docs/architecture/ADR-0012-ERP-FISCAL-Y-PROYECCIONES.md`
- `docs/deployment/NUEVO_VPS_169_58_217_146_ENTREGA_TECNICA.md`
- `docs/deployment/CONFIGURACION_TEMPORAL_IP_IMPRESION_Y_RESPALDOS.md`
- `docs/deployment/VPS_RUNBOOK.md`
- `docs/deployment/VERSIONADO_ACTUALIZACION_ROLLBACK.md`
- `docs/operations/MANUAL_ERPNEXT_SMARTDIAG504_ES.md`
- `docs/operations/MANUAL_COMPLETO_SMARTDIAG504_2026-08-17.md`
- `docs/security/THREAT_MODEL_SMARTDIAG504_2026-08-21.md`
- `docs/testing/ACTA_VALIDACION_FINAL_VPS_2026-08-21.md`

---

**Fin del documento controlado.** Toda modificación debe cambiar versión, fecha,
commit y evidencia de validación.
