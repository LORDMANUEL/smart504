# SmartDiag504: auditoría de brechas y roadmap

**Fecha de corte:** 2026-08-14  
**Entorno comprobado:** demo de pruebas en `taller.nexusmedi.org`, Coolify  
**Objetivo:** determinar qué existe, qué es parcial y qué falta para convertir SmartDiag504 en un software integral, reutilizable y operable por varias empresas.

## 1. Dictamen ejecutivo

SmartDiag504 ya es una **demo operativa amplia y persistente**, no una colección de páginas en blanco. Cuenta con web pública, portal cliente, citas, Kanban, OT, fotografías, mano de obra, cotizaciones/PDF, mostrador, caja, pedidos, bodega, calidad, CRM, campañas, documentos configurables, heatmap e IA local.

Todavía **no es un ERP de taller listo para producción ni un SaaS multiempresa**. El bloqueo principal no es visual: el demo permite que PostgreSQL actúe como fuente de OT, caja, cotizaciones, ventas e inventario mientras la arquitectura declara ERPNext/Beveren como fuente autoritativa. Agregar más pantallas antes de cerrar esa convergencia aumenta la deuda y el riesgo de saldos distintos.

Las prioridades son:

1. ERPNext/Beveren como verdad única de OT, inventario y finanzas.
2. Aislamiento real por empresa y sucursal.
3. Identidad, actor, permisos y auditoría derivados del servidor.
4. Fiscalidad, documentos, impresoras y conciliación.
5. Evidencias privadas, notificaciones reales y recuperación operativa.
6. Después: RRHH, compras, importación, reportes, ecommerce, usados y Hub Social.

### Actualización de ejecución del 14 de agosto de 2026

Este documento comenzó como auditoría. Durante la misma jornada se ejecutó el primer bloque P0 y se comprobó en el VPS:

- ERPNext 16, HRMS, Beveren FSM y `smartdiag_workshop` están instalados en `erp.nexusmedi.org`.
- La API opera con `FRAPPE_REQUIRED=true` e `INVOICE_VERIFICATION_MODE=strict`; `/ready` confirma base, Valkey, Frappe, esquema, IA y seguridad.
- Existe una cola ERP idempotente y persistente. Las ocho OTs heredadas del demo quedaron conciliadas con ocho `Service Order` reales de Beveren (`8/8 SYNCED`). PostgreSQL conserva la proyección y la referencia ERP confirmada.
- Se agregó aislamiento por organización a los agregados operativos y claves compuestas por empresa. Las pruebas cubren dos empresas con el mismo VIN sin lectura ni modificación cruzada.
- El actor operativo, empresa y sucursal se derivan de la sesión. Los actores enviados por el navegador ya no gobiernan la auditoría protegida.
- El personal dispone de bloqueo por intentos, MFA TOTP, revocación de sesiones y bitácora. El token administrativo queda como recuperación, no como acceso cotidiano.
- Las fotografías diagnósticas se almacenan en volumen privado, requieren sesión para descargarse y se incrustan en el PDF diagnóstico.
- Citas y pedidos usan outbox multicanal. Sin SMTP o proveedor de WhatsApp/SMS/push quedan explícitamente `BLOCKED`, nunca falsamente `SENT`.
- El esquema vigente avanzó de `0015` a `0020`. Se probó desde una base limpia y desde una copia del esquema anterior.
- El respaldo ERP se restauró en una base aislada con 896 tablas y luego se eliminaron las bases temporales de prueba.
- La app servida se recorrió con navegador: 19 módulos operativos mostraron contenido, el Kanban cargó ocho OTs, el detalle abrió repuestos/historial/fotos/mano de obra, y la tienda filtró tres repuestos de Ford Escape por VIN.

Esto cierra la **primera parte** de P0; no convierte automáticamente en terminados fiscalidad, inventario ERP de todos los flujos, RRHH integral ni conectores externos.

## 2. Evidencia comprobada

### Runtime VPS

- Contenedores saludables: gateway, public-web, ops-web, platform-api, PostgreSQL, Valkey, ChromaDB, Ollama y AI Gateway.
- ERP saludable: frontend, backend, scheduler, colas, WebSocket, MariaDB y Redis, con ERPNext/HRMS/Beveren/SmartDiag instalados.
- Migración activa: `0020_notification_outbox (head)`.
- `/lading`, `/lading/repuestos`, `/lading/loginclie` y `/tallerv1/login`: HTTP 200.
- El readiness interno de API responde `ready` con Frappe estricto en `ok`; el gateway lo usa como healthcheck sin exponer una ruta administrativa pública.
- El Compose generado de Coolify conserva sus valores originales, pero el override versionado `infra/coolify/runtime-upgrade.override.yaml` activa Frappe estricto, evidencia privada y los dos workers sin alterar Traefik/Coolify.

### Calidad local

- API focalizada: 81 pruebas aprobadas en el entorno Python del servicio.
- Portal operativo: 16 pruebas aprobadas y build de producción aprobado.
- La app Frappe compila sin errores de sintaxis y el endpoint idempotente de OT se verificó contra el ERP servido.
- Validación de navegador servida: landing, tienda, login, 19 módulos, Kanban, detalle OT y portal cliente con contenido.
- El árbol Git contiene múltiples cambios sin consolidar; no es todavía un release reproducible.

## 3. Arquitectura actual frente a la objetivo

| Tema | Estado actual | Estado requerido |
|---|---|---|
| OT | Modelo y mutación local en PostgreSQL | `Service Order` Beveren autoritativa y proyección local conciliada |
| Cotización | Cotización local y PDF | `Service Quotation`/documento ERP con versión y aprobación enlazada |
| Inventario | Balances y movimientos locales en varios flujos | Stock Ledger ERPNext y documentos de stock idempotentes |
| Caja/contabilidad | Movimientos demo; mostrador tiene sync más avanzado | Factura, pago, devolución y asientos verificados en ERPNext |
| Clientes/vehículos | Datos locales y demo | Frappe autoritativo con autorización por objeto |
| Empresas/sucursales | Campos parciales y valores por defecto | Contexto tenant obligatorio en sesión, datos, índices y reportes |
| Evidencias | Volumen local servido por `/media` | Objeto privado, URL firmada, antivirus, retención y autorización |

## 4. Matriz de módulos

| Módulo | Estado | Ya existe | Falta para considerarlo completo |
|---|---|---|---|
| Taller y OT | Parcial alto | Kanban, seis estados, diagnóstico, fotos, repuestos, mano de obra e historial | Service Order ERP real, cronómetro/pausas, check-in 360, firma, DTC estructurado, trabajos externos y QC obligatorio |
| Citas y recepción | Parcial | Cita pública/cliente, horarios, agenda y estados | Capacidad por técnico/bahía/equipo, duración por servicio, feriados, espera, no-show, recordatorios y conversión formal a OT |
| Cotizaciones | Parcial alto | VIN/placa/cliente, líneas, aprobación, HTML/PDF y conversión | Documento ERP, versiones inmutables, vigencia, impuestos/listas reales, firma/IP y aprobación por margen/descuento |
| Caja OT/POS | Parcial alto | Apertura, código, Kanban, cobro, arqueo/cierre y documentos | Datáfono, impresora/gaveta, SAR/CAI/rangos, notas de crédito, conciliación bancaria y contabilidad ERP |
| Mostrador | Funcional alto | VIN/fitment, SKU/OEM, fotos, carrito, caja, factura, devolución/garantía y sync ERP | Clientes/listas/impuestos ERP completos, crédito, lector de código, hardware y fiscalidad certificada |
| Bodega | Parcial | Bodegas, balances, reservas, picking OT, transferencias, fletes, entrega/devolución y PDF | Stock Ledger único, lotes/series, escaneo, conteos, min/max, costos valorizados y aprobación de diferencias |
| Ecommerce | Parcial | Catálogo, compatibilidad, carrito, pedido y Kanban | Pago en línea, reserva fiable, logística/guía, notificaciones, Sales Order automático, identidad productiva, analítica y abandono |
| Catálogo | Parcial alto | CRUD, Excel, fitment, fotos, costo landed y ABC/XYZ | OEM/alternos/equivalencias, gobierno de datos, fotos exactas masivas, proveedores/listas y catálogo VIN productivo |
| RRHH y mano de obra | Parcial alto | Expediente, código automático, contrato, forma de pago, autoservicio de marcación/permisos/vouchers, horas extra, políticas versionadas, deducciones/aportes, prestaciones estimadas y borrador HRMS | Salary Structures y asignaciones HRMS, turnos complejos, habilidades, productividad, comisiones masivas, pago/asiento conciliado y certificación del contador |
| CRM/leads | Parcial | Captura manual/IA, Kanban, actividades y encuesta | Consentimiento, tareas/SLA, scoring, segmentación, atribución, automatización y mensajería integrada |
| Publicidad | Parcial | Campañas, imagen/video, publicación, slug y clics | TV dinámica, calendario, presupuesto, audiencia, aprobación, UTM, conversiones, ROI y programación |
| Hub Social | Ausente funcionalmente | Pantalla informativa | Inbox, cuentas, webhooks, asignación, plantillas, SLA, opt-in/out, auditoría y aprobación humana de IA |
| Procesos/calidad | Parcial | Recetas, casos, transiciones e historial VIN | BPM ejecutable, responsables, SLA, checklists, causa raíz y costo de no calidad |
| Reportería | Parcial bajo | Mostrador/margen, sync, cotizaciones, ABC/XYZ y heatmap | KPIs definidos, filtros/periodos/sucursal, P&G, caja, ventas de taller, gastos, nómina, drill-down y conciliación ERP |
| Contabilidad | Ausente en capa SmartDiag | Sync parcial de mostrador | Capa en español sobre diario, mayor, balance, P&G, CxC/CxP, impuestos, cierres y conciliaciones ERP |
| Compras/proveedores | Ausente | Costo de compra en producto | RFQ, comparativo, PO, recepción, factura proveedor, CxP, devolución, reorden y aprobaciones |
| Importación | Ausente | Factor landed simple y receta visual | Expediente, proforma, Incoterm, embarque, aduana, ETA, documentos, distribución de landed cost y variaciones |
| Compra/venta de usados | Ausente | Vehículos de clientes | Tasación, compra/consignación, inspección, reacondicionamiento, inventario por unidad, publicación y margen |
| Gerencia/configuración | Parcial bajo | Sucursales, CAI nominal, directorio y política de precios | Empresa/sucursal heredable, RTN/series reales, feature flags, metas, presupuestos y SoD |
| Portal cliente | Parcial | Vehículos, historial, citas, alertas, aprobaciones, documentos y perfil | Identidad real, MFA/recuperación, autorización por objeto, facturas sin fallback, pagos, crédito y lealtad |
| IA/RAG | Parcial | Ollama, Chroma, chat persistente, guardrails y captura de lead | Corpus autorizado/versionado, citas de fuente, herramientas reales, separación de permisos y evaluación continua |

## 5. Mano de obra y RRHH: estado exacto

El bloque implementado calcula:

```text
asignación fija por hora = salario fijo mensual / horas productivas mensuales
costo normal = (asignación fija + pago normal por hora) × (1 + cargas patronales)
costo especializado = (asignación fija + pago especializado por hora) × (1 + cargas patronales)
importe OT = horas registradas × tarifa de venta aplicable
```

La OT conserva snapshots históricos de horas, costo y tarifa; un cambio salarial posterior no altera cotizaciones pasadas. La API impide vender la hora por debajo del costo real y no expone salario/costo al técnico o cajero.

Para completar RRHH hacen falta Employee/HRMS, contratos, turnos, asistencia, ausencias, competencias, horas extra, productividad, comisiones, nómina, deducciones, provisiones y asientos. La fuente de nómina debe ser HRMS/ERPNext; PostgreSQL sólo debe proyectar indicadores autorizados.

## 6. Brechas transversales de UX

1. Agrupar la navegación plana en Inicio, Taller, Ventas, Inventario, Finanzas, Personas, Mercadeo, Reportes y Configuración.
2. Reemplazar actores `asesor-demo`, `tecnico-demo`, `bodega-demo`, `cajero-demo` y `calidad-demo` por la identidad de sesión.
3. Sustituir `window.prompt` por diálogos accesibles con validación y confirmación.
4. Convertir el buscador superior en búsqueda global de OT, VIN, placa, cliente, SKU, pedido y factura.
5. Unificar estados de carga, vacío, error, reintento, permiso y modo degradado.
6. Eliminar fixtures y fallbacks demo del portal cliente cuando se activen datos reales.
7. Conectar la pantalla TV a campañas publicadas y programadas.
8. Agregar gates automáticos de accesibilidad, contraste, Lighthouse y regresión visual.

## 7. Seguridad y datos

### P0

- Aislamiento por organización y sucursal en todas las tablas, consultas, índices y eventos.
- Actor, sucursal y empresa derivados de la sesión, nunca del payload del navegador.
- MFA para propietario/administrador, recuperación por correo, revocación y protección contra fuerza bruta.
- Retirar el token administrativo universal del flujo normal y de `sessionStorage`.
- Secretos independientes y de longitud suficiente.
- Evidencias de OT privadas con control por cliente, OT y rol.
- Consecutivos de OT transaccionales; no usar `count + 1`.

### P1

- Cola/outbox ERP común con idempotencia, reintentos, dead-letter, compensación y conciliación.
- Consentimiento y retención para clientes, leads, chat, imágenes y comunicaciones.
- Webhooks firmados y auditoría para proveedores externos.
- Pruebas de autorización por objeto y aislamiento multiempresa.

## 8. Roadmap ejecutable

### P0 — Integridad y base productiva, 1–2 sprints

1. Inventariar cambios, limpiar artefactos y crear release reproducible.
2. Aprobar ADR de fuente de verdad y migración de modelos demo a proyecciones.
3. Hacer Beveren/ERP obligatorio para OT, cotización, inventario, factura y pago.
4. Generalizar cola ERP y conciliación; eliminar estados falsamente `DELIVERED` o `SYNCED`.
5. Implementar tenant/empresa/sucursal y actor server-side.
6. Cerrar MFA, recuperación, SoD y autorizaciones de descuentos/devoluciones.
7. Configurar fiscalidad, CAI/series y backup externo con restore probado.
8. Exponer readiness real y agregar observabilidad del flujo.

**Salida P0:** una OT completa demuestra igualdad entre aprobación, trabajo, stock, factura, pago, historial VIN y ERP; ninguna empresa puede leer otra; el restore aislado funciona.

### P1 — Operación completa del taller, 2–3 sprints

1. Capacidad real de citas y recepción/check-in con firma.
2. Cronómetro, pausas, productividad, DTC, checklists y fotografías privadas.
3. QC obligatorio, pase de salida, garantía y costo de retrabajo.
4. Bodega ERP con escaneo, lotes/series, conteos, reservas y devoluciones.
5. Notificaciones reales de cita, aprobación, pedido, entrega y garantía.
6. Plantillas y pruebas con impresora térmica/normal y datáfono.

**Salida P1:** recorridos E2E por rol ejecutan cita→OT→aprobación→bodega→calidad→caja→entrega sin edición directa de base ni actores demo.

### P2 — Gestión empresarial, 2–3 sprints

1. Compras, proveedores, reabastecimiento e importación/landed cost.
2. RRHH/HRMS y nómina completa enlazada al costeo de mano de obra.
3. Reportería gerencial/contable en español sobre ERPNext.
4. Ecommerce con pago, reserva, logística, abandono y conciliación.
5. CRM/marketing con consentimiento, atribución, campañas y TV dinámica.

**Salida P2:** P&G, balance, caja, margen por OT/repuesto/técnico/sucursal y nómina concilian con ERP y permiten drill-down al documento fuente.

### P3 — Expansión, después de estabilizar P0–P2

1. Compra, venta y consignación de vehículos usados.
2. Multiempresa SaaS, branding, paquetes y feature flags.
3. Hub Social real con Meta/WhatsApp y supervisión humana.
4. IA técnica con manuales aprobados, citas de fuente y evaluación continua.
5. HA física de dos nodos cuando el volumen y RTO/RPO lo justifiquen.

## 9. Dependencias externas que no se deben simular

- Cuenta, aprobación y credenciales de Meta/WhatsApp Business.
- SMTP o proveedor de correo transaccional.
- Pasarela/adquirente y hardware POS.
- Datos fiscales hondureños: RTN, CAI, rangos y política legal aprobada.
- Impresoras, gaveta y lectores físicos para pruebas reales.
- Proveedor de almacenamiento privado/backup externo.
- Política laboral y nómina validada por administración/contabilidad.

## 10. Definición de terminado por módulo

Un módulo sólo se marca terminado cuando cumple:

- estados y reglas de negocio válidos;
- persistencia en la fuente autoritativa;
- tenant, RBAC y autorización por objeto;
- actor server-side, auditoría e idempotencia;
- documentos y notificaciones aplicables;
- manejo de errores, reintentos y conciliación;
- pruebas unitarias, integración y E2E contra la app servida;
- métricas, alertas y trazabilidad;
- backup/restore cuando crea datos críticos;
- runbook, configuración y guía de capacitación.

## 11. No declarar terminado todavía

- Contabilidad, facturación fiscal o reportes financieros consolidados.
- Nómina pagada/contabilizada y cumplimiento laboral certificado; la capa operacional y el borrador HRMS ya existen.
- OT e inventario completamente autoritativos en ERPNext.
- Multiempresa segura.
- Pago en línea o datáfono real.
- Impresión fiscal/térmica certificada.
- Notificaciones de citas/pedidos por correo o WhatsApp.
- Meta/WhatsApp/Hub Social.
- RAG técnico con manuales certificados.
- HA física y recuperación ante pérdida total de VPS.

## 12. Próxima unidad de trabajo recomendada

El siguiente bloque debe ser **Convergencia ERP P0**, no otro módulo visual:

1. Crear OT/Service Order en ERPNext desde recepción.
2. Proyectarla en PostgreSQL con `external_reference` e idempotencia.
3. Convertir mano de obra y repuestos aprobados en documentos ERP.
4. Reservar/entregar/devolver stock mediante documentos ERP.
5. Facturar y pagar desde la misma cadena documental.
6. Conciliar y mostrar diferencias en una bandeja operativa.
7. Cubrir todo con E2E por asesor, técnico, bodega, caja y propietario.

Sólo después de demostrar esa cadena conviene ampliar RRHH o compras sobre una base financiera estable.
