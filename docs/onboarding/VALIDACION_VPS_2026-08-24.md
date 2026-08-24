# Validación del paquete en el VPS — 2026-08-24

Servidor de pruebas: `169.58.217.146`.

## Evidencia ejecutada

| Control | Resultado |
|---|---|
| Plantilla 01 generada por el importador oficial | 7,017 bytes; lectura `CatalogPreview(labor=[], parts=[], errors=[])` |
| Plantilla 02 | `OK`; 21 hojas y encabezados validados |
| API `/ready` | `database`, `valkey`, `object_storage`, `frappe`, `schema`, `ai_gateway` y `security`: `ok` |
| ERPNext `/api/method/ping` | `pong` |
| Repositorio del VPS | Código actualizado; sólo `.env.coolify` permanece local y no versionado |
| Coolify y servicios ajenos | No reiniciados ni modificados |

## Alcance pendiente de datos empresariales

La conectividad del ERP y las plantillas están verificadas. Aún no se puede certificar una migración empresarial porque la empresa no ha entregado catálogo definitivo, empleados, salarios, existencias, documentos fiscales ni aprobaciones. Cuando se reciban, deben ejecutarse la vista previa, conciliación, creación de usuarios y operación completa descritas en el manual.

SMTP continúa en pausa por la transferencia del dominio. La fiscalidad, los formatos preimpresos y el hardware requieren validación del contador y de la empresa.

## Nota de pruebas

La imagen productiva de `platform-api` no contiene `pytest`, lo cual es correcto para reducir superficie. Por eso la comprobación en este corte utilizó los validadores ejecutables de los propios libros, el parser oficial del catálogo y los endpoints reales de disponibilidad; la suite automatizada se ejecuta en la imagen de pruebas/CI, no dentro del contenedor productivo.
