# SmartDiag504 — rutas, mejoras y decisiones de la demo

## Objetivo

Esta fase presenta una demo integrada en `taller.nexusmedi.org` sin reutilizar
contenedores, redes privadas, bases de datos ni volúmenes de otros proyectos.
El sistema conserva una sola identidad visual, pero separa la superficie pública
de los flujos internos del taller.

## Rutas y responsabilidad

| Ruta | Aplicación | Propósito |
|---|---|---|
| `/lading` | `public-web` | Landing, servicios, reservas y catálogo público. Se conserva la grafía solicitada por compatibilidad. |
| `/lading/loginclie` | `public-web` | Acceso demostrativo del cliente. |
| `/lading/cliente` | `public-web` | Vehículos, repuestos compatibles, alertas, promociones, cotizaciones y facturas. |
| `/tallerv1/login` | `ops-web` | Acceso del personal técnico. |
| `/tallerv1/kanban` | `ops-web` | Time control y planeación del taller mediante OT. |
| `/tallerv1/caja` | `ops-web` | Verificación, cobro y facturación final. |
| `/tallerv1/bodega` | `ops-web` | Ticket de picking, ubicación y registro de entrega a la OT. |
| `/tallerv1/3gj` | `ops-web` | Vista de administración y directorio operativo. |
| `/tallerv1/publicida` | `ops-web` | Gestión de campañas y promociones. |
| `/tallerv1/publicida/tv` | `ops-web` | Pantalla completa para televisores. |

HAProxy enruta `/api` y `/media` a Platform API, `/tallerv1` a operaciones y el
resto a la web pública. Coolify sólo publica el gateway por el puerto interno
`8084`; no se abre ningún puerto del host.

## Datos demostrativos

- Vehículos: Ford Escape 2020, Ford F-150 2020 y Honda Civic 2008.
- Cinco operaciones de mano de obra con tiempo, costo interno y precio de venta.
- Nueve repuestos: tres por vehículo, con ubicación, inventario, costo interno y
  precio de venta.
- El endpoint público elimina el costo; el endpoint de bodega exige token de
  administración.
- El `seed.py` es idempotente: puede ejecutarse después de una migración sin crear
  duplicados por SKU, teléfono, VIN o número de OT.

## Decisiones técnicas

1. **Demo operativa primero, ERPNext después.** El Compose de demo deshabilita el
   requisito de Frappe en readiness para evitar publicar una integración que no
   se ha probado contra una instancia real. El Compose completo conserva Frappe.
2. **Una sola fuente para catálogo demo.** `app/demo_data.py` alimenta API y seed;
   las interfaces mantienen un espejo tipado para poder renderizar aun durante
   una demostración sin conectividad.
3. **Costos no públicos.** Costo de taller sólo aparece en importación/bodega; el
   portal del cliente expone precio de venta.
4. **Rutas compatibles con la solicitud.** Se conserva `/lading`, aun cuando la
   palabra habitual es `landing`, para que los enlaces entregados no cambien.
5. **Comentarios por intención, no por sintaxis.** Se documentan límites de
   seguridad, invariantes y decisiones. Comentar cada línea duplicaría el código,
   ocultaría errores y haría más difícil mantenerlo.
6. **Estado demo explícito.** Los botones actualizan estado de interfaz para una
   demo navegable. No se certifican pagos fiscales, inventario ni autenticación
   productiva hasta integrar ERPNext/identidad y validar las operaciones reales.

## Mapa de código

- `apps/public-web/src/components/CustomerExperience.tsx`: login y portal cliente.
- `apps/public-web/src/data/demo.ts`: vehículos y compatibilidades del navegador.
- `apps/ops-web/src/components/RoleViews.tsx`: caja, bodega, administración y TV.
- `services/platform-api/app/demo_data.py`: fuente controlada de datos demo.
- `services/platform-api/app/routes/demo.py`: contratos público e interno.
- `services/platform-api/scripts/seed.py`: persistencia idempotente de catálogo y OT.
- `infra/haproxy/haproxy.cfg`: propiedad de rutas en el dominio único.
- `compose.demo.yaml`: despliegue aislado y reducido para demostración.

## Validación obligatoria antes de declarar producción

1. Backup y restauración aislada del volumen PostgreSQL.
2. Autenticación real por roles; la credencial visible de cliente sólo es demo.
3. Registro persistente de picking, cobro, facturación y auditoría de actor.
4. Integración ERPNext/Frappe probada con una copia de staging.
5. TLS/rutas externas, consola, red, responsive y flujos de cada perfil.

