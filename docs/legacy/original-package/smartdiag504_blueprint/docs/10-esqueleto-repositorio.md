# 10 — Esqueleto propuesto del repositorio

```text
smartdiag504/
├── apps/
│   ├── api/                     # FastAPI: dominio del taller y API pública/interna
│   ├── web/                     # React/TypeScript: operación administrativa
│   ├── technician-pwa/          # React/TypeScript: técnicos y bahías
│   ├── storefront/              # Landing, portal y e-commerce
│   └── worker/                  # Outbox, integración, alertas y tareas programadas
├── packages/
│   ├── domain-contracts/        # Tipos, estados, eventos y validaciones compartidas
│   ├── api-client/              # Cliente TypeScript generado desde OpenAPI
│   ├── ui/                      # Design system y componentes accesibles
│   ├── auth/                    # OIDC, permisos y sesión
│   └── observability/           # Logs, métricas y trazas
├── services/
│   ├── ai-rag/                  # Ingesta, ChromaDB, retrieval y gateway LLM
│   ├── notifications/           # Email, WhatsApp/SMS/push por adaptadores
│   └── control-plane/           # Licencias/versiones; sin datos operativos del cliente
├── integrations/
│   ├── erpnext/                 # Adaptador, mapeos, webhooks y conciliación
│   ├── fiscal-hn/               # Localización validada para Honduras
│   ├── payments/                # Proveedor configurable
│   └── messaging/               # Proveedor configurable
├── db/
│   ├── migrations/              # Migraciones PostgreSQL
│   ├── seeds/                   # Datos demo reproducibles
│   └── policies/                # RLS/aislamiento cuando aplique
├── contracts/
│   ├── openapi-outline.yaml
│   ├── events.yaml
│   ├── permissions.yaml
│   └── work-order-state-machine.yaml
├── infra/
│   ├── compose/                 # Desarrollo y despliegue sencillo
│   ├── kubernetes/              # Solo cuando el volumen lo justifique
│   ├── terraform/               # Infraestructura reproducible
│   └── monitoring/              # Métricas, logs, trazas y alertas
├── tests/
│   ├── contract/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   └── performance/
├── docs/
│   ├── architecture/
│   ├── product/
│   ├── runbooks/
│   ├── decisions/
│   └── user-guides/
├── scripts/                     # Instalación, backup, restore, seed y diagnóstico
├── .github/workflows/           # CI, seguridad, build y releases
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
└── README.md
```

## Límites de módulos del backend

```text
app/
├── identity/
├── organizations/
├── customers/
├── vehicles/
├── appointments/
├── intake/
├── work_orders/
├── diagnostics/
├── estimates/
├── technicians/
├── parts/
├── quality/
├── delivery/
├── warranties/
├── alerts/
├── documents/
├── integrations/
├── assistant/
└── audit/
```

Cada módulo contiene:

- modelo de dominio;
- comandos y consultas;
- reglas/invariantes;
- repositorio o puerto;
- endpoints;
- eventos;
- pruebas.

## Contratos antes de código

1. Máquina de estados de OT.
2. Esquema de eventos versionados.
3. OpenAPI inicial.
4. Matriz de permisos.
5. Mapeo SmartDiag ↔ ERPNext.
6. Formato de idempotencia y correlación.
7. Política de errores y reintentos.

## Flujo de ramas y releases

- rama principal protegida;
- cambios por pull request;
- pruebas y escaneo obligatorios;
- migración junto al cambio de dominio;
- versionado semántico del producto y contratos;
- changelog generado por release;
- despliegue primero en staging con datos anonimizados/demo;
- rollback o forward-fix documentado.

## Configuración

- `.env.example` sin secretos.
- configuración validada al inicio.
- secretos por gestor del entorno.
- flags de función por cliente/plan.
- separación estricta de desarrollo, staging y producción.

## Orden recomendado de construcción

1. contratos y modelo de dominio;
2. identidad, organización y auditoría;
3. cliente/vehículo;
4. OT y estados;
5. recepción/diagnóstico/cotización;
6. técnicos/repuestos/QC;
7. adaptador ERP;
8. portal/tienda;
9. IA/alertas avanzadas;
10. comercialización y operación multi-cliente.
