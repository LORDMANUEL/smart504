# SmartDiag504 - plan ejecutable de modulos, UX, datos y documentos

Fecha: 2026-08-13  
Estado: plan de implementacion; no certifica que las funciones descritas ya esten terminadas  
Documento relacionado: [PLAN_MAESTRO_SOFTWARE_INTEGRAL_TALLER_2026-08-13.md](./PLAN_MAESTRO_SOFTWARE_INTEGRAL_TALLER_2026-08-13.md)

## 1. Objetivo

Convertir SmartDiag504 en un producto configurable para distintos talleres, sin crear una copia diferente del codigo por empresa. Este plan baja el plan maestro a trabajo ejecutable y prioriza:

- landing page comercial, marca, botones y vistas operativas;
- fotografias y evidencia dentro de la OT;
- historial persistente por VIN, cliente, OT y documento;
- cotizaciones y facturas generadas desde HTML y convertibles a PDF;
- editor seguro de plantillas para adaptar documentos a cada empresa;
- impresion en carta, A4, termica de 80/58 mm, etiquetas y PDF;
- profundidad funcional de todos los modulos descritos en el plan maestro;
- pruebas de flujos completos y evidencia de lo validado.

## 2. Lectura de diseno aplicada

**Modo:** rediseño preservando rutas, contenido util y marca.  
**Producto:** taller automotriz orientado a confianza, rapidez operativa y conversion comercial.  
**Direccion visual:** rojo/negro SmartDiag504, fondos neutros, fotografia real del taller, repuestos y vehiculos, composicion asimetrica y jerarquia clara.  
**Diales:** densidad 6/10, movimiento 4/10, profundidad 5/10.

Reglas:

1. La landing comercial y las vistas internas no usan la misma densidad visual.
2. El logo se muestra en sus colores originales sobre una superficie con contraste; no se le aplica un filtro que borre su identidad.
3. El efecto de cristal esmerilado se limita a navegacion, overlays o controles flotantes. Siempre tiene respaldo opaco y contraste legible.
4. No se agregan animaciones por decoracion. Se permiten aparicion suave, zoom leve de imagen, transiciones de estado y desplazamiento respetando `prefers-reduced-motion`.
5. Toda accion tiene estados normal, hover, focus, disabled, loading, success y error.
6. Los iconos provienen del sistema ya usado en el proyecto; no se sustituyen por emoji.
7. Se preservan las rutas publicas y operativas. Un cambio de URL requiere redireccion y prueba.

## 3. Arquitectura funcional objetivo

```text
Landing / tienda / portal cliente / operacion interna
                         |
                 API de SmartDiag504
          _________|___________|___________
         |         |           |           |
   PostgreSQL   Objetos      Cola       Adaptadores
   proyeccion   fotos/PDF    trabajos   ERP/mensajes/POS
         |                                  |
         +------ eventos idempotentes -------+
                         |
               ERPNext/Frappe canonico
       OT, inventario, factura, pago y contabilidad
```

### Limite de verdad

- PostgreSQL de SmartDiag504 conserva experiencia digital, sesiones, configuracion, proyecciones, evidencias, actividad y analitica.
- ERPNext/Frappe debe ser la fuente canonica de OT, inventario valorizado, facturas, pagos y contabilidad.
- Mientras `FRAPPE_REQUIRED=false` y la verificacion de factura permanezca en modo desarrollo, las pantallas financieras se identifican como demo; no se declaran fiscales ni listas para produccion.
- Toda integracion usa `external_id`, idempotencia, reintentos, registro de error y conciliacion.

## 4. Fundacion de datos antes de ampliar pantallas

### 4.1 Tenencia y aislamiento

Para empresas independientes se recomienda un sitio Frappe aislado por organizacion. En PostgreSQL compartido, toda tabla empresarial nueva debe incluir:

- `tenant_id` obligatorio;
- `company_id` y `branch_id` cuando corresponda;
- claves foraneas e indices por alcance;
- Row Level Security habilitado y forzado;
- contexto de tenant establecido por transaccion;
- pruebas automatizadas que intenten leer y modificar datos de otro tenant.

No se debe confiar solo en filtros de la aplicacion.

### 4.2 Entidades transversales nuevas

| Entidad | Responsabilidad |
|---|---|
| `tenant` | organizacion cliente y aislamiento |
| `company` | empresa legal, datos fiscales y moneda |
| `branch` | sucursal operativa |
| `feature_flag` | modulos habilitados por tenant/sucursal |
| `setting_value` | configuracion versionada y heredable |
| `domain_event` | historial funcional append-only |
| `audit_event` | quien cambio que, cuando, origen y motivo |
| `evidence_asset` | metadatos seguros de foto/video/archivo |
| `document_template` | identidad de la plantilla por tipo |
| `document_template_version` | contenido versionado borrador/publicado |
| `document_render` | copia inmutable HTML/PDF de un documento emitido |
| `print_profile` | papel, margenes, impresora y copias |
| `print_job` | cola, intentos y resultado de impresion |
| `notification` | mensaje, destinatario, canal, estado y reintentos |
| `integration_outbox` | entrega confiable de eventos a ERP y terceros |

### 4.3 Historias que deben persistir

No se usara un solo campo JSON como sustituto de historial. Cada flujo conserva eventos estructurados:

- cliente: altas, cambios autorizados, consentimientos, contactos y solicitudes;
- vehiculo: propietarios, odometro, mantenimientos, diagnosticos, OT, reclamos y garantias;
- cita: origen, confirmacion, recordatorio, reprogramacion, cancelacion, no-show y conversion;
- OT: estado, responsable, tiempos, evidencia, diagnostico, aprobacion, repuestos, QC y entrega;
- cotizacion: versiones, lineas, precios, descuentos, envio y aprobacion/rechazo por linea;
- inventario: reserva, picking, entrega, consumo, devolucion y referencia al asiento ERP;
- caja: apertura, ingresos, retiros, pagos, anulaciones, cierre y aprobaciones;
- documento: plantilla/version usada, render, firma, envio, descarga e impresion;
- CRM: fuente, etapa, contacto, interes, proxima accion, perdida/venta y encuesta.

Los eventos funcionales no reemplazan el libro mayor ni el Stock Ledger de ERPNext.

## 5. Sistema visual y componentes reutilizables

### 5.1 Marca y recursos

1. Preparar variantes oficiales: horizontal, isotipo, fondo claro, fondo oscuro y favicon.
2. Recortar el espacio blanco excesivo del archivo actual sin deformar la marca.
3. Centralizar `Brand` para que landing y operacion no tengan implementaciones divergentes.
4. Definir tokens de color, tipografia, espaciado, radios, sombras, z-index y movimiento.
5. Registrar cada imagen con licencia/origen, texto alternativo, formatos y tamaños responsivos.

### 5.2 Botones

Variantes obligatorias:

| Variante | Uso |
|---|---|
| Primary | accion principal de la vista |
| Secondary | alternativa visible |
| Ghost | accion de baja prioridad |
| Danger | anulacion, devolucion o cierre sensible |
| Link | navegacion dentro de texto |
| Icon | accion compacta con `aria-label` y tooltip |

Reglas: altura tactil minima de 44 px, texto sin saltos involuntarios, foco visible, contraste AA, bloqueo contra doble envio y feedback inmediato. Acciones irreversibles requieren confirmacion y motivo.

### 5.3 Vistas internas

- Navegacion segun rol, empresa y sucursal.
- Una tarea principal por pantalla.
- Kanban para estado del trabajo; tabla para busqueda, auditoria y operaciones masivas.
- Cada tarjeta Kanban abre detalle real por ruta o panel lateral y permite ejecutar solo transiciones validas.
- Filtros persistentes por usuario, busqueda, paginacion, estados vacios, skeleton y error recuperable.
- Formularios por secciones; no mostrar todo el portal o la OT en una sola pagina larga.
- Escritorio, tableta y movil probados; bodega y tecnico priorizan uso tactil.

## 6. Landing page, tienda y portal cliente

### 6.1 Landing promocional

Estructura propuesta:

1. Barra superior limpia: logo, servicios, repuestos, por que elegirnos, ubicacion y boton `Ingresar`.
2. Hero dividido: promesa concreta y CTA `Agendar cita`; fotografia real de diagnostico/taller; CTA secundario `Comprar repuestos`.
3. Prueba de confianza: garantias, tecnicos, herramientas, reseñas verificables y marcas atendidas.
4. Servicios principales con duracion orientativa y accion de cita.
5. Promociones activas desde el modulo de publicidad.
6. Catalogo destacado con compatibilidad de vehiculo y existencia verificable.
7. Proceso de atencion en cuatro pasos.
8. Ubicacion, horario, contacto y pie legal.

Pruebas: CTA hasta confirmacion, atribucion de campaña, imagen responsiva, navegacion con teclado, contraste, LCP/CLS, movil y rutas antiguas.

### 6.2 Tienda

- Busqueda por placa/VIN o marca-modelo-año-motor.
- Fotografias exactas por SKU; placeholder claramente identificado si falta imagen.
- Compatibilidad explicada como confirmada, probable o pendiente de validacion.
- Precio, existencia, sucursal, retiro/envio y tiempo estimado.
- Pedido Kanban: entrado, contactado, confirmado, pagado, reservado, preparando, enviado, entregado, no responde, perdido y devuelto.
- Confirmacion y cambios de estado generan notificacion y quedan en historial.

### 6.3 Portal cliente

Separar por rutas/pestañas cargadas de forma independiente:

- `Mi vehiculo`: imagen sin fondo, VIN, kilometraje, estado de mantenimiento, siguiente servicio, historial corto y consejos rotativos;
- `Citas`: calendario autenticado, disponibilidad real, confirmacion, reprogramacion y historial;
- `Repuestos`: compatibilidad y pedidos;
- `Alertas y aprobaciones`: trabajos adicionales, estados, recordatorios y acciones;
- `Cotizaciones`: lista por fecha/vehiculo/estado, detalle, aprobacion por linea, imprimir/descargar;
- `Facturas`: lista, detalle, PDF y estado de pago;
- `Configuracion`: nombre, correo, telefono, usuario, contraseña, MFA, preferencias, credito y lealtad si estan habilitados.

## 7. Fotografias y evidencia de la OT

### 7.1 Modelo

`evidence_asset` debe guardar, como minimo:

- tenant, empresa, sucursal, OT y vehiculo;
- categoria: recepcion, daño, diagnostico, pieza, antes, despues, QC, entrega o garantia;
- archivo original privado, miniatura, MIME, dimensiones, peso y checksum;
- titulo, descripcion, marcador/anotacion y orden de impresion;
- autor, rol, fecha de captura y fecha de carga;
- retencion, estado de moderacion, sustitucion y eliminacion logica.

Se elimina EXIF sensible, se valida contenido/tamaño, se genera miniatura y se usan URLs firmadas. No se sirven carpetas de subida como archivos publicos.

### 7.2 Experiencia del tecnico

1. Abrir OT desde Kanban.
2. Elegir etapa/categoria antes de capturar.
3. Tomar varias fotos, marcar zona y agregar voz/texto.
4. Ver progreso de carga y reintentar sin duplicar.
5. Relacionar evidencia con diagnostico, linea de cotizacion, repuesto o control de calidad.
6. Seleccionar las fotos visibles para cliente e impresion.

### 7.3 Diagnostico impreso

El documento incluye resumen, sintomas, pruebas, valores, hallazgos, severidad, recomendacion y mosaico de evidencias con pie de foto. La plantilla controla tamaño y cantidad; el PDF usa las miniaturas optimizadas y conserva enlace/QR al expediente autorizado.

## 8. Centro de documentos editable

### 8.1 Alcance

Tipos iniciales:

- cotizacion;
- diagnostico;
- orden de trabajo;
- factura y recibo;
- nota de credito/devolucion;
- garantia;
- picking y entrega de bodega;
- devolucion a bodega;
- control de calidad y pase de salida;
- cierre/arreglo de caja;
- pedido y guia de envio;
- contratos y cartas gerenciales.

### 8.2 Editor por empresa

El administrador puede:

1. duplicar una plantilla base;
2. editar encabezado, bloques, tablas, columnas, textos, imagenes, firmas y pie;
3. insertar variables desde un catalogo permitido;
4. configurar visibilidad condicional mediante reglas declarativas;
5. elegir carta, A4, 80 mm, 58 mm o etiqueta;
6. previsualizar con datos ficticios y con un documento autorizado;
7. guardar borrador, solicitar aprobacion, publicar y volver a una version anterior;
8. exportar/importar un paquete de plantilla validado para reemplazarla facilmente.

No se permite JavaScript arbitrario ni HTML/CSS sin sanitizar. El editor usa bloques seguros y una lista de propiedades CSS admitidas.

### 8.3 Variables iniciales

```text
company.*       branch.*        fiscal.*       branding.*
customer.*      vehicle.*       appointment.*  work_order.*
diagnostic.*    evidence.*      quote.*        quote.lines[]
invoice.*       invoice.lines[] payment.*      warehouse.*
shipment.*      signatures.*    qr.*           document.*
```

Cada variable tiene nombre amigable, tipo, ejemplo, permisos y comportamiento si falta el dato.

### 8.4 Versiones y validez historica

- Una plantilla publicada es inmutable.
- Reemplazar una plantilla crea una version nueva y solo afecta documentos futuros.
- Al emitir un documento se guarda `template_version_id`, HTML final, PDF, hash, actor y fecha.
- Reimprimir un documento historico usa su render original, no la plantilla actual.
- Una correccion comercial genera una nueva version; una correccion fiscal sigue el flujo legal de anulacion/nota, nunca reescribe silenciosamente el original.

### 8.5 Pipeline de impresion

```text
datos validados -> plantilla publicada -> HTML canonico
        -> PDF/termico -> vista previa -> cola de impresion
        -> impresora -> resultado/reintento -> auditoria
```

Perfiles:

- carta y A4 para PDF/impresora normal;
- 80/58 mm para ticket;
- etiqueta para SKU/ubicacion/QR;
- copias y bandeja por terminal;
- margenes, escala, corte y apertura de gaveta como capacidad del adaptador local.

La prueba de PDF no valida una impresora fisica. Cada modelo/controlador requiere matriz y evidencia de impresion real.

## 9. Plan por modulo

La columna `Base` indica el punto de partida auditado, no un porcentaje de terminacion.

| ID | Modulo | Base | Incremento funcional prioritario | Datos/Integracion | Salida verificable |
|---|---|---|---|---|---|
| M01 | Identidad y seguridad | parcial/demo | usuarios individuales, MFA, recuperacion, roles y sesiones | tenant, usuario, rol, alcance, auditoria | matriz de permisos y pruebas de aislamiento |
| M02 | Multiempresa/configuracion | minima | empresa, sucursal, marca, fiscal, features y herencia | configuracion versionada; sitio Frappe por tenant | alta de una segunda empresa sin fork |
| M03 | RRHH | ausente | expediente, turnos, asistencia, habilidades, vacaciones y comisiones | Employee/HR de ERPNext y proyecciones | ciclo de empleado con permisos |
| M04 | Citas/recepcion | parcial | capacidad, recordatorios, reprogramacion, check-in y fotos 360 | cita, recurso, disponibilidad, notificacion | cita publica y autenticada llegan al tablero |
| M05 | Vehiculos/historial | parcial | VIN unico, propietarios, odometro, mantenimiento, alertas y reclamos | historial append-only y enlaces OT | linea de tiempo completa por VIN |
| M06 | Taller/OT | parcial avanzado | diagnostico estructurado, tiempos, evidencias, adicionales, QC y entrega | OT canonica ERP + proyeccion | flujo recepcion-entrega sin atajos |
| M07 | Cotizaciones | parcial | buscar VIN, versionar, margen, aprobar por linea y convertir a OT | Quote/Quotation ERP, renders | cotizacion HTML/PDF y conversion idempotente |
| M08 | Mano de obra | parcial | catalogo por vehiculo/motor, costo, precio, tiempo y vigencia | importacion Excel con preview | filtrar servicios compatibles en OT |
| M09 | Repuestos/catalogo | parcial | SKU/OEM, alternos, compatibilidad, fotos, costos y precios | Item ERP, activos y Excel | tres vehiculos demo y catalogo fotografiado |
| M10 | Compras/proveedores | ausente | solicitud, comparativo, orden, recepcion, factura y devolucion | compras ERPNext | compra completa conciliada |
| M11 | Bodega | parcial | multi-bodega, picking OT, reserva, entrega, retorno, conteo y escaneo | Stock Ledger ERP + proyeccion | picking PDF y trazabilidad por pieza |
| M12 | Importacion | ausente | proforma, embarque, documentos, landed cost y recepcion parcial | compras/stock/contabilidad ERP | costo importado conciliado |
| M13 | Tienda/pedidos | parcial | carrito, reserva, pago, envio, devolucion y Kanban | pedido, stock y transportista | pedido completo con notificaciones |
| M14 | Caja/POS | parcial/demo | Kanban cobrable, apertura, pagos mixtos, arqueo, cierre y devolucion | Payment/Sales Invoice ERP, adaptador POS | caja conciliada e impresion probada |
| M15 | Documentos/impresion | HTML/PDF fijo | editor de bloques, versiones, perfiles y cola | templates, renders, print jobs | empresa cambia formato sin cambiar codigo |
| M16 | Calidad/garantias | parcial | checklist, prueba ruta, comeback, garantia y causa raiz | QC, evidencia, OT y costos | caso de garantia trazable |
| M17 | CRM/leads | parcial | captura, prospeccion, tareas, encuestas, campañas y atribucion | lead, actividad, consentimiento | lead hasta venta/perdida con historial |
| M18 | Publicidad/social | parcial | gestor de imagen/video, programacion, links UTM y clicks | campaign, asset, publication, event | campaña publicada y medible |
| M19 | Reporteria/gerencia | parcial | KPIs definidos, margen, capacidad, calidad, caja y crecimiento | proyecciones + ERP verificado | tablero con fuente y fecha de corte |
| M20 | Contabilidad | objetivo no desplegado | libro, CxC/CxP, bancos, impuestos, cierres y conciliacion | ERPNext/Frappe obligatorio | pruebas y aceptacion contable local |
| M21 | Vehiculos usados | ausente | compra, tasacion, consignacion, reacondicionamiento y venta | activo/unidad, OT y contabilidad | rentabilidad completa por VIN |
| M22 | IA/RAG | demo/parcial | asistente cliente, tecnico, fuentes, leads, limites y evaluacion | documentos autorizados y tool gateway | respuestas citadas y sin fuga de tenant |
| M23 | Notificaciones | parcial | bandeja, email/SMS/WhatsApp, preferencias y reintentos | outbox, provider status | cita/pedido/OT notifican y auditan |
| M24 | Operacion/HA | parcial | health, backups, restauracion, observabilidad y failover probado | Coolify, Docker, DB y objetos | runbook y simulacro recuperable |

## 10. Flujos de referencia que deben quedar automatizados

### F01 - cita a entrega

```text
solicitud -> disponibilidad -> confirmacion/notificacion -> recepcion
-> inspeccion/fotos -> OT -> diagnostico -> cotizacion/aprobacion
-> reserva/picking/entrega -> reparacion -> QC -> cobro -> pase de salida
-> factura/notificacion -> historial VIN -> encuesta
```

### F02 - cotizacion rapida por VIN

```text
buscar VIN -> validar propietario/vehiculo -> elegir mano de obra compatible
-> agregar repuestos compatibles -> calcular impuestos/precio/margen autorizado
-> guardar version -> previsualizar HTML/PDF -> enviar/aprobar
-> convertir una sola vez a OT
```

### F03 - pedido online

```text
carrito -> contacto -> validacion compatibilidad -> reserva condicionada
-> confirmacion -> pago -> bodega de proceso -> picking -> transito
-> guia/foto -> entrega -> factura -> garantia/devolucion
```

### F04 - devolucion

```text
solicitud -> validar documento/plazo/estado -> inspeccion -> aprobar/rechazar
-> retorno a cuarentena -> nota/reembolso -> disposicion de inventario
-> cierre con evidencia e historial
```

### F05 - caja

```text
identificar cajero -> abrir/fondo -> Kanban de documentos cobrables
-> abrir detalle -> validar aprobados -> cobro simple/mixto -> factura/recibo
-> imprimir/enviar -> movimientos -> arqueo ciego -> cierre/conciliacion
```

## 11. API y servicios a construir

Nombres finales pueden adaptarse a la convencion existente, pero deben conservar estos contratos:

### Evidencia

- `POST /work-orders/{id}/evidence/uploads` crea carga idempotente.
- `POST /work-orders/{id}/evidence` registra metadatos y relacion.
- `PATCH /evidence/{id}` cambia descripcion, categoria o visibilidad autorizada.
- `POST /evidence/{id}/annotations` agrega marcadores.
- `GET /work-orders/{id}/evidence` filtra por etapa/categoria.

### Historial

- `GET /vehicles/{id}/timeline` combina eventos autorizados por VIN.
- `GET /customers/{id}/timeline` muestra relacion comercial y vehiculos.
- `GET /work-orders/{id}/timeline` muestra eventos y responsables.
- `GET /documents/{id}/history` muestra versiones, envios e impresiones.

### Plantillas y documentos

- CRUD de plantillas y borradores por tipo/empresa/sucursal.
- `POST /document-templates/{id}/preview` renderiza datos de muestra.
- `POST /document-templates/{id}/publish` exige permiso/aprobacion.
- `POST /documents/{type}/{business_id}/render` crea snapshot inmutable.
- `GET /document-renders/{id}.html|.pdf` entrega la version emitida.
- `POST /print-jobs` encola; `GET /print-jobs/{id}` devuelve resultado.

### Notificaciones

- plantillas versionadas por evento/canal/idioma;
- outbox transaccional;
- preferencia y consentimiento del destinatario;
- webhook de entrega/fallo;
- reintento con limite y bandeja de errores.

## 12. Migraciones de base de datos

Orden recomendado, siempre con Alembic y despliegue expand/migrate/contract:

1. Introducir tenant/company y rellenar registros actuales con tenant demo.
2. Agregar alcances e indices sin activar restricciones destructivas.
3. Migrar lecturas/escrituras de aplicacion al contexto empresarial.
4. Activar `NOT NULL`, claves e invariantes despues de validar datos.
5. Habilitar y forzar RLS; ejecutar pruebas de cruce de tenant.
6. Crear evidencia y migrar referencias actuales sin perder archivos.
7. Crear eventos/auditoria e iniciar outbox.
8. Crear plantillas, versiones, renders y perfiles de impresion.
9. Importar plantillas actuales como version base `v1`.
10. Solo despues retirar campos/formatos obsoletos.

Cada migracion incluye respaldo, conteos antes/despues, rollback operativo o restauracion ensayada y prueba sobre copia de produccion anonimizada.

## 13. Orden de implementacion

### Ola 0 - seguridad y verdad (2-4 semanas)

- inventario final de rutas, tablas, flujos y dependencias;
- identidad individual, tenant/company/branch y permisos;
- activar ERP obligatorio en entorno de integracion;
- observabilidad, backups restaurables y datos demo separados;
- correccion del logo y tokens base.

**Gate:** no hay cruce entre empresas y ninguna pantalla demo se presenta como contabilidad real.

### Ola 1 - experiencia y documentos (3-5 semanas)

- landing, botones, navegacion y portal dividido;
- evidencia OT y almacenamiento seguro;
- historial VIN/OT/cliente;
- editor de plantillas v1;
- HTML/PDF canonico para cotizacion, diagnostico, OT y picking.

**Gate:** una empresa cambia logo, encabezado, columnas y pie; el documento historico no cambia.

### Ola 2 - taller completo (4-7 semanas)

- citas/recepcion, OT, catalogos de mano de obra y repuestos;
- aprobaciones por linea, piezas solicitadas/entregadas/consumidas;
- bodega Kanban, calidad, garantia y pase de salida;
- notificaciones de cita, aprobacion y estado.

**Gate:** F01 funciona de extremo a extremo con datos persistidos y permisos por rol.

### Ola 3 - venta y dinero (4-7 semanas)

- tienda/pedidos/devoluciones/envios;
- caja Kanban, POS mediante adaptador, pagos mixtos y cierre;
- factura/recibo/nota y perfiles de impresion;
- conciliacion con ERP y pruebas fisicas de impresoras seleccionadas.

**Gate:** pedido y OT se cobran una sola vez, concilian y generan documento verificable.

### Ola 4 - crecimiento empresarial (5-8 semanas)

- compras, proveedores, importacion y multi-bodega completa;
- RRHH, CRM, publicidad, encuestas y reporteria;
- vehiculos usados;
- IA/RAG con fuentes y controles.

**Gate:** KPIs tienen formula/fuente; los asientos e inventario provienen de ERP.

## 14. Pruebas obligatorias

| Capa | Pruebas |
|---|---|
| Unidad | reglas de estado, totales, permisos, variables y sanitizacion |
| API | contrato, idempotencia, concurrencia, paginacion y errores |
| Datos | FK, indices, RLS, migracion, auditoria y restauracion |
| Integracion | ERP, objetos, correo/WhatsApp, POS y cola |
| Navegador | landing, portal, Kanban, formulario, carga de foto y descarga |
| Documento | snapshot HTML, PDF visual, saltos, fuentes, QR y formatos |
| Fisica | impresora normal/termica, corte, gaveta y escaner seleccionado |
| Seguridad | aislamiento, RBAC, subida maliciosa, XSS de plantilla y secretos |
| Rendimiento | catalogo, timeline largo, tableros, fotos y render concurrente |
| Recuperacion | backup/restauracion y reintento sin duplicados |

Se deben capturar capturas, IDs creados, respuesta API y evidencia de impresion. Un HTTP 200 o contenedor sano no demuestra que el flujo funciona.

## 15. Definition of Done de cada historia

Una historia solo termina si:

1. tiene criterio de aceptacion y permisos definidos;
2. persiste en la fuente correcta y registra historial;
3. maneja vacio, carga, exito, error, reintento y concurrencia;
4. es usable con teclado y en el dispositivo objetivo;
5. tiene pruebas automatizadas proporcionales al riesgo;
6. tiene migracion y documentacion operativa si cambia datos;
7. fue probada en el runtime realmente servido;
8. no expone extensiones `.php`, `.css` u otras rutas internas como arquitectura del producto;
9. conserva compatibilidad o incluye migracion/redireccion;
10. actualiza la matriz funcional como `validado`, `parcial` o `pendiente` con evidencia.

## 16. Primer backlog listo para desarrollar

### EPIC UX-01 - identidad visual

- recortar y preparar variantes del logo;
- unificar componente de marca;
- tokens y botones accesibles;
- landing responsive;
- pruebas visuales y de rutas.

### EPIC OT-01 - evidencia fotografica

- migracion `evidence_asset`;
- almacenamiento privado y miniaturas;
- captura multiple categorizada;
- relacion con diagnostico/repuesto/QC;
- galeria OT y seleccion para cliente/PDF;
- pruebas de permisos, archivo invalido y reintento.

### EPIC DATA-01 - historial confiable

- `domain_event`, `audit_event` y outbox;
- timelines VIN, cliente y OT;
- backfill desde eventos existentes;
- indices y paginacion por cursor;
- prueba de inmutabilidad y tenant.

### EPIC DOC-01 - editor y render

- modelos de plantilla/version/render;
- editor de bloques y catalogo de variables;
- sanitizacion, preview, publish y rollback;
- importacion/exportacion de paquete;
- migrar cotizacion/diagnostico/OT/picking;
- golden tests HTML/PDF.

### EPIC PRINT-01 - impresion

- perfiles carta/A4/80/58;
- cola e historial;
- adaptador local opcional;
- reimpresion del snapshot original;
- matriz fisica por impresora.

## 17. Decisiones que requieren aprobacion antes de produccion

- proveedor y estrategia de identidad social/correo;
- ERPNext/Frappe definitivo y topologia por tenant;
- reglas fiscales hondureñas validadas por profesional competente;
- proveedores de WhatsApp/SMS/correo y consentimientos;
- POS/adquirente y modelos de impresora/terminal;
- retencion y consentimiento de fotografias del vehiculo;
- alcance legal de vehiculos usados, credito y lealtad;
- licencias de manuales y fuentes del RAG.

Este documento permite iniciar por UX, evidencia, historial y plantillas sin inventar integraciones externas. Los modulos financieros solo pasan a produccion cuando ERP, fiscalidad, dispositivos y restauracion hayan sido probados con evidencia.
