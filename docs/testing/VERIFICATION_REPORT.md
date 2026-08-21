# Informe de verificación — SmartDiag504 Platform v0.4.0

**Fecha:** 12 de agosto de 2026  
**Rama verificada:** `feature/v0.4-complete`

## Resultado ejecutado en este entorno

| Control | Resultado |
|---|---|
| Validación estructural del repositorio | Aprobada: **366 archivos**, 18 YAML, 27 JSON, 38 servicios Compose y 95 claves de entorno inspeccionadas |
| TypeScript/TSX sin dependencias | Aprobado: 29 archivos fuente analizados |
| Dominio de órdenes de trabajo | **14 pruebas aprobadas** |
| API de plataforma | **29 pruebas aprobadas** |
| Gateway de IA y chatbot | **13 pruebas aprobadas** |
| Motor de alertas | **5 pruebas aprobadas** |
| Contratos de arquitectura/despliegue | **46 pruebas aprobadas** |
| Pruebas de navegador | **3 pruebas aprobadas** sobre los contratos de interacción deterministas de landing/tienda y PWA; las superficies React completas se construyen con dependencias en CI/Docker |
| Total de pruebas ejecutadas | **110 aprobadas** |
| Compilación Python | Aprobada con `compileall` |
| Sintaxis Bash | Aprobada con `bash -n` para todos los scripts |
| Fotografías públicas | Contrato, URLs y atribuciones validados; descarga local pendiente cuando exista acceso de red |
| Secretos | `.env` real excluido del paquete; scripts generan valores aleatorios y el navegador no recibe claves del LLM |
| `docker compose config` | **No ejecutado aquí:** Docker no está instalado en este entorno |
| Construcción/arranque real de contenedores | **No ejecutado aquí:** requiere Docker, DNS y una VPS de staging |

Comando principal:

```bash
bash scripts/verify.sh
```

Salida resumida:

```text
Repository validation passed: 366 files, 18 YAML, 27 JSON,
38 services, 95 environment keys.
14 + 29 + 13 + 5 + 46 + 3 tests passed.
Static verification passed.
Docker Compose runtime validation skipped: docker is not installed.
```

## Alcance validado

- Los seis estados oficiales de la OT y sus transiciones permitidas.
- Catálogo público, alta administrativa de productos y fotografías con texto alternativo persistente.
- Solicitud web de pedidos con idempotencia.
- Sesión segura de chatbot, mensajes, límites, fallback sin proveedor externo y guardrails.
- Vista Kanban predeterminada y activación opcional de bahías.
- Réplicas A/B para web, PWA, API, IA, heartbeat y alertas en la misma VPS.
- Configuración, scripts y contratos para ERPNext, Beveren FSM y `smartdiag_workshop`.
- Backups con manifiesto y flujo de restauración controlada.

## Gates obligatorios en la VPS

Este informe no es una certificación de producción. Codex debe ejecutar y conservar evidencia de:

1. `docker compose config --quiet` con el `.env` real;
2. construcción de todas las imágenes, incluida Frappe/ERPNext/Beveren;
3. creación de un sitio ERPNext v16 desde cero;
4. creación de una OT con mano de obra y repuestos y selección correcta de artículos;
5. smoke tests de landing, tienda, chatbot, PWA, API y ERPNext;
6. prueba A/B deteniendo cada réplica de aplicación;
7. backup completo y restauración en staging vacío;
8. verificación de SMTP, Google CSE cuando se habilite, almacenamiento externo y proveedor LLM;
9. aprobación fiscal hondureña, pasarela de pago, análisis de vulnerabilidades, carga y pentest;
10. aceptación independiente de la topología física de dos VPS más testigo cuando se requiera tolerancia a pérdida del host.
