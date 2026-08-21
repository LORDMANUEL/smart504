# AGENTS.md — Reglas de desarrollo SmartDiag504

## Arquitectura del sistema

Antes de modificar componentes, propiedad de datos o despliegue, consulte [ARCHITECTURE.md](./ARCHITECTURE.md). La auditoría priorizada y los criterios de salida están en [docs/product/AUDITORIA_BRECHAS_Y_ROADMAP_2026-08-14.md](./docs/product/AUDITORIA_BRECHAS_Y_ROADMAP_2026-08-14.md).

## Prioridades

1. No duplicar la fuente de verdad de ERPNext.
2. No crear otra OT paralela a Beveren `Service Order`.
3. Escribir prueba antes de cambiar comportamiento.
4. Mantener adaptadores externos detrás de interfaces.
5. Registrar eventos idempotentes y auditables.
6. Mantener IA en modo lectura salvo herramienta explícita, permiso y confirmación humana.

## Límites

- `frappe-apps/smartdiag_workshop`: dominio automotriz y extensiones Frappe.
- `services/platform-api`: BFF público; nunca contabilidad propia.
- `services/ai-gateway`: RAG y herramientas seguras.
- `services/alerts-worker`: evaluación de reglas; no altera documentos financieros.
- `apps/public-web`: cliente, tienda y reserva.
- `apps/ops-web`: operación del taller.
- `packages/smartdiag_domain`: reglas puras compartidas.

## Gates obligatorios

Por decisión del propietario, este equipo local se usa únicamente para conversación, edición y respaldo del código. Está prohibido crear máquinas virtuales o ejecutar aquí pruebas, migraciones, compilaciones o validaciones con Python. Todos los gates y ensayos funcionales se ejecutan en el VPS de pruebas de SmartDiag504, en contenedores aislados y sin afectar otros servicios de Coolify.

```bash
make test
make typecheck
make validate
```

No marcar una tarea como terminada si alguno falla en el VPS. Docker se valida adicionalmente con `docker compose config` en ese mismo entorno.

## Convenciones

- Python: tipado, Pydantic v2, `ruff` y pytest.
- TypeScript: `strict: true`, sin `any` implícito.
- Campos Frappe propios: prefijo `sd_` cuando extienden DocTypes de terceros.
- Eventos: mayúsculas con guion bajo, por ejemplo `WORK_ORDER_CREATED`.
- Secretos: solo variables de entorno o secretos del runtime.
- Fechas: ISO 8601 y UTC internamente; zona visible `America/Tegucigalpa`.
