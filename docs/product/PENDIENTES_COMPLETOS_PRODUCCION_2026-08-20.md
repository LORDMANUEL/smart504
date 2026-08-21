# SmartDiag504 — lista completa de pendientes

**Corte actualizado:** 21 de agosto de 2026. **Entorno:** VPS de pruebas.  
Esta lista separa código existente de dependencias que requieren contador, proveedores o hardware.

## Cerrado técnicamente en el VPS

- ERPNext/Beveren obligatorio y OT autoritativa con reconciliación servida.
- Aislamiento por organización y sucursal para transacciones operativas y actores obtenidos de sesión.
- MFA, bloqueo, recuperación, revocación, RBAC y evidencia de OT privada.
- Compras/importación, RRHH/nómina, documentos configurables, mostrador, caja, taller, publicidad/TV y portal técnico ejecutados de forma servida.
- Migración desde vacío, suite API, contratos, 26 menús SmartDiag y 39 enlaces ERP aprobados.
- Importación remota de imágenes protegida contra SSRF/DNS rebinding.
- Paquete Debian y copia portable reproducible disponibles.

## P0 — dependencias reales antes de producción

1. **Fiscalidad Honduras:** el contador debe configurar y firmar empresa, RTN, CAI/rangos, impuestos, cuentas, cierres y decidir papel preimpreso versus impresión completa.
2. **Conciliación de aceptación:** contador y responsables deben firmar el recorrido real con productos, clientes, impuestos y bancos de la empresa; las pruebas actuales usan datos controlados.
3. **SMTP:** entregar servidor, puerto, usuario, secreto y dominio con SPF/DKIM/DMARC; después repetir citas, pedidos, aprobaciones y recuperación.
4. **Evidencia privada:** Garage/S3 privado ya funciona en el VPS; faltan antivirus, política aprobada de retención/eliminación y réplica cifrada fuera de este servidor.
5. **Hardware:** validar físicamente datáfono/POS, gaveta, lectores e impresoras térmica y normal con sus controladores.
6. **Backups externos:** destino cifrado fuera de esta VPS, rotación, alertas y restauración aislada periódica medida.
7. **Operación segura:** eliminar cuentas E2E/demo, rotar secretos, exigir MFA a privilegios, configurar firewall, escanear imágenes y realizar pentest independiente.
8. **Aceptación por rol y carga:** usuarios reales deben aprobar sus recorridos; ejecutar volumen/carga según número esperado de sucursales y terminales.
9. **Release:** consolidar el árbol de trabajo en commits firmados/etiqueta, generar SBOM y registrar digests/rollback del release aprobado.

## Taller, recepción y técnicos

- capacidad de citas por técnico, bahía, equipo, duración y feriados;
- lista de espera, no-show, recordatorios y reprogramación;
- check-in 360°, firma del cliente, kilometraje/combustible/accesorios;
- cronómetro real, pausas, trabajos externos, DTC estructurados y checklists configurables;
- control de calidad obligatorio, retrabajo, garantía, pase de salida y firma;
- catálogo de mano de obra persistente por empresa y filtrable por vehículo ya implementado; falta gobierno de versiones y sincronización bidireccional certificada con el maestro ERP;
- manuales técnicos autorizados con versión, página y permisos, no búsquedas abiertas como fuente final;
- aplicación móvil/PWA del técnico probada con cámara y conectividad inestable.

## Ventas, cotizaciones, caja y mostrador

- versiones inmutables de cotización, vigencia, firma/IP y aprobación por margen/descuento;
- listas de precios, impuestos, crédito, límites y cuentas ERP reales;
- cotización técnica y mostrador conciliados como documentos ERP, no sólo proyecciones;
- datáfono/adquirente real, gaveta, lector, impresora térmica y normal certificados;
- cierre, arqueo, diferencias, depósito y conciliación bancaria por caja/sucursal;
- devolución, garantía y nota de crédito completas para OT, ecommerce y mostrador;
- consecutivos fiscales y reimpresión/anulación con permisos y auditoría.

## Inventario, compras e importación

El flujo técnico proveedor → orden → recepción → costo de importación ya fue repetido de forma servida y quedó sincronizado con ERPNext. Todavía falta la aceptación contable formal y la prueba con datos, impuestos, proveedores y documentos reales de la empresa.

- Stock Ledger ERP único para todas las bodegas y flujos;
- lotes, series, escaneo, conteos, ajustes, mínimos/máximos y aprobación de diferencias;
- reservas con vencimiento/liberación y bodegas tránsito/importación/proceso;
- proveedores, RFQ, comparativo, orden de compra, recepción, factura, CxP y devolución;
- reorden ABC/XYZ con demanda real y aprobación;
- expediente de importación, Incoterm, embarque, aduana, ETA, documentos y landed cost distribuido;
- conciliación de variaciones de costo y trazabilidad hasta la pieza vendida.

## Ecommerce, clientes y logística

- identidad productiva, verificación de correo, recuperación, MFA opcional y autorización por objeto;
- pago online, antifraude, reserva de inventario y conciliación;
- transportistas, tarifa, guía/foto, tracking, prueba de entrega, devolución y reclamo;
- notificaciones reales de pedido/cita/aprobación/entrega;
- SEO, analítica, consentimiento, carrito abandonado y atribución;
- crédito, lealtad, garantías y facturas reales sin fixtures/fallbacks demo.

## RRHH y nómina

- estructuras/asignaciones HRMS autoritativas;
- turnos complejos, asistencia biométrica opcional, vacaciones, incapacidades y horas extra;
- competencias, productividad, comisiones y costo por OT;
- deducciones/aportes/seguro/prestaciones conforme política validada para Honduras;
- vouchers, pago, provisiones y asientos conciliados;
- aprobación del especialista laboral/contador y privacidad estricta del expediente.

## CRM, marketing, publicidad y Hub Social

- consentimiento, segmentación, scoring, tareas, SLA, campañas y atribución;
- recuperación y correo transaccional ya alimentan un outbox real; falta configurar y monitorear SMTP para que las entregas pasen de `BLOCKED` a `SENT`;
- TV dinámica enlazada a campañas, calendario, presupuesto, UTM, conversiones y ROI;
- Inbox social, Meta/WhatsApp aprobados, webhooks firmados, plantillas, opt-in/out y auditoría;
- supervisión humana de IA, límites, escalamiento y protección contra prompt injection.

## Contabilidad, gerencia y reportes

- vistas españolas completas sobre diario, mayor, balance, P&G, flujo, CxC/CxP e impuestos;
- presupuestos, metas, centros de costo, sucursales y comparativos;
- definición formal de cada KPI, filtros, exportación y drill-down al documento fuente;
- gastos, compras, nómina, taller, mostrador, ecommerce y usados en reportes conciliados;
- cierre periódico, bloqueo, reapertura controlada y auditoría.

## Vehículos usados

- tasación, compra/consignación, inspección, documentación y aprobación;
- reacondicionamiento mediante OT y costo acumulado;
- inventario por unidad/VIN, publicación, test drive, reserva, financiación y venta;
- margen, comisión, garantía y contabilización ERP.

## Plataforma y operación

- observabilidad con alertas, Sentry/APM, métricas de colas y conciliación ERP;
- rotación de secretos, firewall, hardening, escaneo de imágenes y pentest;
- HSTS/CSP y encabezados del gateway ya están activos; falta automatizar su regresión, escanear imágenes y completar pentest externo;
- política de actualización, migraciones reversibles y rollback por digest;
- HA física de dos VPS sólo si el RTO/RPO la exige; dos contenedores en una VPS no son HA física;
- instalador `.deb` validado en Debian limpio y procedimiento de actualización/desinstalación;
- manual visual y recorrido guiado existen; falta repetir la aceptación formal con cada usuario real y hardware real;
- accesibilidad WCAG, móvil/tablet, rendimiento y pruebas con datos de volumen real.

## Dependencias externas no resolubles sólo con código

- contador y asesor laboral de Honduras;
- CAI/rangos y decisión de papel preimpreso;
- SMTP y dominio con SPF/DKIM/DMARC;
- adquirente/pasarela, POS, impresoras, gaveta y lectores;
- Meta/WhatsApp Business y sus aprobaciones;
- almacenamiento privado y backup externo;
- segundo nodo físico si se aprueba HA;
- usuarios responsables para aceptación por rol.

Estas dependencias permanecen visibles y bloqueantes. No deben reemplazarse con estados ficticios: en el corte actual las diez entregas de notificación pendientes están `BLOCKED`, no `SENT`, porque SMTP y proveedores externos no han sido configurados.

## Criterio de salida

El sistema estará listo para producción cuando una restauración limpia pueda ejecutar, con usuarios reales y sin actores demo, la cadena cita → recepción → OT → diagnóstico/fotos → cotización/aprobación → reserva/entrega → trabajo/calidad → factura/pago → asiento/reporte, y cada documento coincida con ERPNext y pueda auditarse por empresa y sucursal.
# Cerrado el 2026-08-21

- Identidad persistente del cliente y vínculo con empresa/cliente.
- Sesiones de cliente en cookie segura y revocables; no hay token sensible en almacenamiento web.
- Aislamiento de portal, citas, vehículos, cotizaciones y documentos por `organization_id` y `customer_id`.
- Eliminación de la factura ficticia como fallback del portal.

# Pendientes internos priorizados

1. Implementar el enrolamiento MFA TOTP completo en la experiencia cliente. El 21 de agosto se eliminó la activación ficticia por checkbox; ahora la pantalla muestra el estado real y explica que hace falta enrolamiento confirmado.
2. Normalizar fitment OEM por motor/versión y gobernar equivalencias; el portal ya consume catálogo persistido por VIN y no importa fixtures de repuestos.
3. Completar E2E servido de todos los roles y aislamiento negativo entre dos organizaciones, incluyendo ERPNext.
4. Completar conciliación autoritativa ERP de OT, compras, bodega y nómina; PostgreSQL debe quedar sólo como proyección operacional.
5. Completar asistentes visuales específicos para los menús que aún usan guía genérica; hardware fiscal y SMTP requieren las dependencias externas. El almacenamiento privado de OT ya está activo en Garage/S3.
