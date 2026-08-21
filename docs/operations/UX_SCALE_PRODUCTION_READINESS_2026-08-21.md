# UX, accesibilidad y capacidad antes de producción

## Dictamen

La demo tiene una superficie funcional amplia, pero no está certificada para producción. Un HTTP 200 o un contenedor saludable no demuestra que cada rol complete su flujo. La salida exige sesiones reales por rol, conciliación ERP y evidencia de restauración.

## Hallazgos UX confirmados

1. **500 para técnico con sucursal asignada:** el overview intentaba duplicar `MAIN`. Corregido con lectura explícita por organización fuera del filtro de sucursal, sin permitir cruce de tenant.
2. **RR. HH. sin contrato devolvía 404:** ahora devuelve un estado vacío accionable; marcación y permisos quedan bloqueados hasta la vinculación.
3. **Recorrido interrumpe el primer trabajo:** debe recordarse por usuario y versión y poder reiniciarse desde Ayuda. La apertura automática por cada entrada a Mostrador debe eliminarse.
4. **Ruta de navegador permanece en `/login`:** después de autenticar debe navegar a la ruta del módulo permitido, para que historial, recarga y enlaces sean comprensibles.
5. **Navegación extensa:** agrupar Taller, Ventas, Inventario, Finanzas, Personas, Mercadeo y Sistema; permitir favoritos y recientes.
6. **Búsqueda global incompleta:** debe buscar realmente OT, VIN, placa, cliente, SKU, pedido y factura, con permisos aplicados en servidor.
7. **Objetivos táctiles y texto:** controles de 36–40 px y texto de 8–10 px deben subir a 44 px recomendados y texto operativo legible. No reducir información para que “quepa”.
8. **Estados inconsistentes:** unificar loading, vacío, error, reintento y permiso denegado; cada error debe indicar qué hacer.
9. **Credenciales demo prellenadas:** aceptable sólo en pruebas; el gate de producción debe impedir compilar/desplegar ese comportamiento.
10. **Carga inicial excesiva:** cargar únicamente el módulo activo, con cache y error boundary; evitar que un endpoint secundario bloquee toda la sesión.

## Gate WCAG 2.2 AA

Ejecutar `scripts/qa_authenticated_axe.mjs` en el VPS con credenciales de aceptación, en 360, 768, 1366 y 1920 px. El gate falla ante hallazgos `serious` o `critical`. Además se valida teclado, foco visible, Escape en diálogos, zoom 200%, reducción de movimiento, nombres accesibles, contraste 4.5:1 y mensajes con `role=status/alert`.

### Evidencia ejecutada el 21 de agosto de 2026

- Primera pasada: 68 vistas, 90 violaciones severas y 1,689 nodos de contraste repetidos.
- Segunda pasada: 68 vistas, 64 violaciones; quedaron únicamente contraste y se eliminaron nombres/roles/tamaños inválidos.
- Tercera pasada: 68 vistas, 9 violaciones de contraste concentradas en Bahías, Kanban y Mostrador.
- Pasada final servida: **68 vistas, 0 violaciones y 0 severas/críticas**.
- Roles autenticados incluidos: TECHNICIAN, CASHIER, ACCOUNTANT y MARKETING; público incluido en cuatro resoluciones.
- Evidencia durable: `artifacts/visual-qa/axe-authenticated-zero.json`.
- La sesión técnica servida mantuvo URL de módulo, cero errores de consola y endpoints overview/self-service en HTTP 200.

Este resultado no completa el E2E de OWNER, ADMIN, MANAGER, RECEPTION, WAREHOUSE, AUDITOR y cliente; esos flujos siguen siendo gate antes de producción.

## Un millón de transacciones no significa una sola carga

| Volumen | Promedio | Lectura técnica |
|---|---:|---|
| 1 millón/día | 11.6 transacciones/s | Posible con margen, cache y DB bien dimensionada |
| 1 millón/hora | 278/s | Requiere varias réplicas, pool y pruebas distribuidas |
| 1 millón/10 min | 1,667/s | Requiere arquitectura horizontal, colas y partición de cargas |
| 1 millón simultáneas | 1,000,000 concurrentes | No es objetivo realista para un VPS único |

## Arquitectura de absorción

1. Cloudflare: DDoS administrado, WAF, bot management/rate rules y cache; el origen acepta únicamente tráfico Cloudflare o túnel.
2. Gateway: límites por ruta/identidad, cola corta, `429/503` con `Retry-After`, tamaño máximo y timeouts.
3. API: réplicas stateless, sesiones/ratelimit en Valkey, circuit breakers y degradación de IA/publicidad antes que caja/OT.
4. Lecturas públicas: CDN para assets y catálogo versionado; nunca cachear saldo, pago, nómina ni datos privados.
5. Escrituras: idempotency key obligatoria, restricción única, lock por venta/stock, outbox y consumidores con reintento/DLQ.
6. PostgreSQL: PgBouncer en modo transaction, límites de pool, `statement_timeout`, índices medidos y réplica de lectura para reportes.
7. ERPNext: cola de sincronización, backpressure y conciliador; la API no confirma factura/stock definitivo hasta recibir estado autoritativo.
8. Observabilidad: SLO por flujo, p95/p99, saturación de pool/DB/Valkey, lag de cola, errores ERP, trazas y alertas.

La topología actual de pruebas —una API, un PostgreSQL, un Valkey y HAProxy `maxconn 1024`— no puede prometer un millón de solicitudes concurrentes.

### Capacidad actual verificada

La prueba previa de compradores sintéticos alcanzó 1,000 iteraciones con 100 usuarios virtuales y 2,000 solicitudes: 0 errores, 3,000/3,000 checks, p95 938.22 ms y p99 1.35 s. Es evidencia de una carga pequeña/controlada, no certificación de un millón.

## Prueba de capacidad segura

No disparar un millón de solicitudes desde ni contra el VPS compartido. Crear un entorno aislado equivalente y generadores distribuidos. Escalera: 100→1,000→10,000→100,000→1,000,000 transacciones totales; pruebas smoke, load, spike, soak y breakpoint. Criterios: cero corrupción/duplicados, cero sobreventa, p95 acordado, errores controlados, recuperación de cola y conciliación ERP exacta.

## Pendientes externos obligatorios

- CAI/fiscalidad y hardware certificados con contador/proveedor.
- SMTP definitivo con SPF, DKIM, DMARC y pruebas de entrega/rebote.
- Backup en otra infraestructura y restauración aislada documentada.
- Antivirus/CDR para PDFs y adjuntos.
- E2E autenticado completo por rol y axe sin severidad seria/crítica.
