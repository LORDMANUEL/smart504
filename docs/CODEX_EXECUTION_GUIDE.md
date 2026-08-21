# Guía de ejecución para Codex — SmartDiag504

## 1. Misión

Convertir este skeleton en una plataforma productiva por incrementos verificables, preservando contabilidad, inventario y trazabilidad. Codex debe trabajar como ingeniero responsable de un sistema financiero-operativo, no como generador de pantallas aisladas.

## 2. Reglas inmutables

1. **ERPNext es la única fuente de verdad** para artículos, existencias, compras, POS, caja, facturas, pagos y contabilidad.
2. La OT central es Beveren **`Service Order`**. Es obligatorio **no crear una segunda OT** ni un ledger paralelo.
3. El dominio automotriz vive en `smartdiag_workshop` y enlaza documentos de terceros con campos `sd_` y referencias explícitas.
4. PostgreSQL de plataforma solo contiene eventos, alertas, idempotencia y auditoría IA.
5. Valkey contiene estado temporal, caché, locks, colas y streams; nunca es la única copia de un dato de negocio.
6. ChromaDB contiene embeddings/conocimiento; nunca clientes, facturas, pagos o inventario como verdad principal.
7. Garage/S3 almacena objetos privados; Frappe conserva referencias, permisos, hash y metadatos.
8. La IA es de lectura por defecto. Ningún LLM factura, cobra, mueve stock, cambia precio, autoriza descuento o libera un vehículo.
9. Todo adaptador externo debe ser sustituible y estar detrás de una interfaz.
10. No modificar el núcleo de ERPNext/Frappe. Usar hooks, extensiones, fixtures, overrides documentados o un **adaptador Frappe**.

## 3. Forma de trabajo

Aplicar **TDD** en cada comportamiento:

1. escribir prueba que falla por la razón correcta;
2. ejecutar y conservar evidencia del fallo;
3. implementar el mínimo;
4. ejecutar prueba específica y suite completa;
5. refactorizar con pruebas verdes;
6. actualizar documentación/contrato;
7. hacer commit pequeño y descriptivo.

No aceptar “debería funcionar”. Cada afirmación necesita comando y resultado fresco.

## 4. Gates

### Gate 0 — Base reproducible

- `bash scripts/verify.sh` en CI.
- `docker compose config` sin error.
- imágenes fijadas y escaneadas;
- restore drill básico;
- ningún secreto comprometido.

### Gate 1 — Certificación Beveren v16

- construir imagen Frappe;
- instalar sitio desde cero;
- comprobar dependencia ERPNext;
- probar selección de artículos y `process_item_selection`;
- cotización → Service Order → cita → ejecución → factura;
- impuestos, unidades, bodegas, seriales y cancelaciones;
- registrar cualquier parche adicional en `infra/frappe/patches/beveren` con prueba de regresión.

No avanzar al piloto hasta aprobar este Gate.

### Gate 2 — Núcleo automotriz real

- vehículo/VIN;
- recepción con evidencia;
- diagnóstico y hallazgos;
- cotización versionada y aprobación parcial;
- múltiples técnicos/tiempos;
- bahías;
- repuestos/retornos;
- QC/entrega;
- garantía/historial.

### Gate 3 — Integración ERPNext

Reemplazar repositorios demo por adaptadores reales. Cada escritura debe tener:

- usuario de integración con mínimo privilegio;
- clave idempotente;
- referencia externa única;
- validación de estado previo;
- respuesta persistida;
- conciliación y dead-letter para fallo no recuperable.

### Gate 4 — E-commerce y portal

- catálogo real;
- carrito server-side/firmado;
- reserva de inventario;
- pasarela y webhooks;
- impuestos/entrega;
- autenticación portal y autorización por objeto;
- privacidad/consentimiento.

### Gate 5 — Fiscalidad y producción

- localización Honduras aprobada por profesional competente;
- roles y segregación;
- carga, seguridad y observabilidad;
- backup/restauración medidos;
- suite completa de `docs/testing/ACCEPTANCE_TESTS.md`.

## 5. Orden de implementación recomendado

1. Certificar Beveren/Frappe en Docker.
2. Implementar `FrappeCatalogRepository` de solo lectura.
3. Implementar reserva/cita con idempotencia.
4. Implementar recepción y vínculo al `Service Order`.
5. Implementar diagnóstico/cotización/versiones.
6. Implementar técnicos, tiempos y bahías.
7. Implementar solicitud/entrega/devolución de repuestos usando Stock Entry/Delivery/consumo aprobado.
8. Implementar QC, factura, pago y entrega.
9. Implementar portal autenticado.
10. Implementar checkout/pasarela.
11. Activar IA/RAG y alertas con datos reales.
12. Ejecutar hardening, carga, restore y piloto.

## 6. Contratos a respetar

- API pública: `contracts/openapi-public.yaml`.
- Eventos: `contracts/events.yaml`.
- Máquina de estados: `packages/smartdiag_domain`.
- Propiedad de datos: `docs/architecture/DATA_OWNERSHIP.md`.
- Pantallas: `docs/ux/SCREEN_INVENTORY.md`.
- Criterios de aceptación: `docs/testing/ACCEPTANCE_TESTS.md`.

Cuando un contrato cambie, modificar primero prueba/contrato, versionar el cambio y mantener compatibilidad o migración explícita.

## 7. Prohibiciones

- SQL directo desde navegador o frontend.
- Escribir en tablas ERPNext desde FastAPI por conexión MariaDB.
- Duplicar Item, Bin, Sales Invoice, Payment Entry o Stock Ledger en PostgreSQL.
- Editar cotización enviada sin nueva versión.
- Marcar archivo cargado antes de confirmación S3.
- Confiar en precio/importe calculado por cliente.
- Utilizar rama `develop` de Beveren en producción.
- Añadir dependencias sin pin, licencia y revisión de seguridad.
- Ocultar fallos con mocks en pruebas de integración.

## 8. Comandos de control

```bash
bash scripts/verify.sh
bash scripts/capture-previews.sh
python scripts/validate_repository.py
docker compose --env-file .env -f compose.yaml config
docker compose --env-file .env -f compose.yaml up -d
bash scripts/verify.sh --runtime
```

## 9. Definition of Done

Una tarea está terminada solamente cuando:

- prueba roja/verde demostrada;
- suite completa verde;
- tipos/build verde;
- migración idempotente;
- permisos y auditoría revisados;
- UX de error/carga/vacío/responsive incluida;
- documentación y contrato actualizados;
- rollback conocido;
- commit limpio;
- Gate correspondiente sin deuda crítica nueva.

## 10. Despliegue v0.4.0 en VPS

El punto de entrada para una VPS nueva es:

```bash
sudo bash scripts/bootstrap-host.sh --open-firewall
cp .env.example .env
bash scripts/generate-secrets.sh .env
# El operador revisa .env sin exponer secretos.
sudo bash scripts/codex-vps-deploy.sh --env-file .env --observability
```

Para Ollama local, agregar `--local-ai`. Codex debe usar `docs/CODEX_VPS_DEPLOY_PROMPT.md` como procedimiento y registrar salida de `scripts/verify.sh`, construcción Docker, creación del sitio, smoke test, failover A/B y backup. No declarar HA física en una sola VPS.

## 11. Chatbot

El chatbot público se implementa en `ChatWidget → Platform API → AI Gateway`. Las claves permanecen en servidor. `LLM_PROVIDER=demo` mantiene orientación segura sin proveedor; Ollama y proveedores compatibles se habilitan por configuración. Cualquier intención de escribir factura, pago, inventario, precio, estado financiero o liberación debe bloquearse.

## 12. Contrato obligatorio de la OT

Codex debe conservar el flujo sin renombrar ni agregar estados paralelos:

```text
CREATED
→ QUOTED_BY_TECHNICIAN
→ PENDING_CUSTOMER_APPROVAL
→ PENDING_PARTS
→ READY_TO_INVOICE
→ INVOICED
```

Toda pantalla, API, evento y migración debe utilizar estos códigos. La vista de bahías es opcional y no modifica la máquina de estados; Kanban permanece disponible como fallback.

## 13. Repuestos, fotografías y pedidos web

- La carga de imagen por administrador debe funcionar sin Google.
- Google Programmable Search es solamente un descubridor de candidatos; la clave permanece en servidor.
- Toda imagen importada debe copiarse a almacenamiento administrado y conservar procedencia.
- El pedido web es una solicitud idempotente hasta que ERPNext confirme precio, existencia, impuestos y Sales Order.
- El checkout nunca debe confiar en importes enviados por navegador.

## 14. Chatbot público

Mantener la ruta `ChatWidget → platform-api → ai-gateway`. El frontend solo recibe un token opaco de sesión. Conservar:

- TTL y revocación;
- rate limit;
- `client_message_id` idempotente;
- auditoría y `audit_id`;
- fallback determinista cuando LLM/Chroma están caídos;
- bloqueo de escrituras financieras y de inventario;
- prohibición de exponer una OT sin autenticación.

## 15. Entrega de VPS

Codex debe ejecutar, guardar evidencia y no omitir:

```bash
bash scripts/verify.sh
docker compose --env-file .env -f compose.yaml config --quiet
sudo bash scripts/codex-vps-deploy.sh --env-file .env --observability --test-failover
bash scripts/backup-now.sh .env
```

Antes de declarar producción, restaurar el backup en otra instalación y completar `docs/testing/ACCEPTANCE_TESTS.md`. Una pareja A/B dentro de la misma VPS solo cubre proceso/contenedor; no debe presentarse como HA física.
