# Modelo de amenazas SmartDiag504

## Overview

SmartDiag504 expone una landing, ecommerce, portal de cliente, interfaz operativa por roles, API FastAPI, IA/RAG y una integración con ERPNext. Los activos críticos son identidades, VIN e historial del vehículo, fotografías/evidencias, inventario, precios y costos, nómina, documentos fiscales, pagos y asientos contables. La revisión cubre el repositorio y el despliegue de pruebas; no certifica hardware, proveedores externos ni fiscalidad.

## Threat Model, Trust Boundaries, and Assumptions

Límites de confianza: Internet→Cloudflare/origen; navegador→gateway/API; API→PostgreSQL/Valkey/S3; API→ERPNext; API→SMTP/pagos/logística; trabajador→módulos autorizados; organización/sucursal→otra organización/sucursal. Se asume TLS en el borde, secretos fuera de Git y ERPNext como fuente financiera autoritativa. No se asume que un cliente, archivo subido, encabezado proxy, webhook o salida de IA sea confiable.

Actores: cliente anónimo, cliente autenticado, empleado por rol, administrador, proveedor integrado y atacante externo/interno. Capacidades relevantes: automatización masiva, credenciales robadas, IDOR, carga maliciosa, reintentos duplicados, abuso de descuentos/devoluciones y saturación de recursos.

## Attack Surface, Mitigations, and Attacker Stories

| Superficie | Historia de atacante | Impacto | Mitigación requerida | Estado |
|---|---|---:|---|---|
| Login/recuperación | Fuerza bruta, fijación o robo de sesión | Alto | rate limit distribuido, cookies seguras, revocación, MFA configurable, bloqueo progresivo | Parcial |
| Multiempresa | Cambiar ID y leer/modificar otra empresa o sucursal | Crítico | identidad del servidor, filtros por organización/sucursal, pruebas negativas y RLS/defensa en profundidad | Parcial alto |
| Documentos/fotos | Subir PDF/imagen activa o consultar evidencia ajena | Alto | S3 privado, URLs firmadas cortas, MIME+magic bytes, antivirus/CDR, límites y autorización por objeto | Parcial |
| Pagos/devoluciones | Repetir cobro, vender sin stock o autorizar su propia devolución | Crítico | idempotencia, locks/constraints, maker-checker, conciliación ERP, webhook firmado | Parcial alto |
| Catálogo/mostrador | Vender bajo costo, sin precio o stock | Alto | reglas server-side, inventario ERP, reserva atómica, auditoría | Parcial alto |
| IA/RAG | Prompt injection, fuga de secretos o uso como proxy | Alto | herramientas allowlist, datos por tenant, filtro de salida, límites, corpus firmado/evaluado | Parcial |
| Integraciones | SSRF, webhook falsificado o credencial expuesta | Alto | allowlist, firma, rotación, egress control, timeout/circuit breaker | Parcial |
| Disponibilidad | Botnet o pico legítimo de gran volumen agota conexiones | Crítico | DDoS/WAF en borde, cache, admisión, réplicas, colas, PgBouncer, backpressure y pruebas distribuidas | Pendiente de infraestructura |
| Contabilidad/nómina | Usuario manipula asiento o aprueba su propia planilla | Crítico | ERP autoritativo, segregación de funciones, doble aprobación, ledger/auditoría inmutable | Parcial |
| Operación | Dependencia caída deja transacciones a medias | Alto | outbox, reintentos idempotentes, DLQ, conciliador, alertas y runbooks | Parcial |

## Severity Calibration

- Crítico: cruce de empresa, fraude financiero/fiscal, pérdida irreversible o indisponibilidad general.
- Alto: exposición de PII/evidencia, escalamiento de privilegio o corrupción operativa importante.
- Medio: abuso limitado, degradación parcial o información interna no sensible.
- Bajo: hardening y fuga de metadatos sin acceso material.

No se debe declarar producción mientras sigan pendientes: fiscalidad certificada, SMTP entregable, restauración externa demostrada, análisis malware/CDR, E2E autenticado completo y axe sin hallazgos serios/críticos.

<!-- codex-security-scan: target_id=smartdiag504-platform-v0.4.0 version=codex-security-snapshot/v1:sha256:769a20340082a133b8757923a8b223924a8a7b71617c19c915d72a12960d8506 -->
