# SmartDiag504 v0.4 — Chatbot público y entrega VPS

## Objetivo

Entregar el código fuente completo del skeleton SmartDiag504 con un chatbot incrustado en la landing, persistencia auditada de conversaciones, IA opcional local o externa, despliegue Docker de una VPS, réplicas de procesos web/API y documentación de alta disponibilidad física para dos VPS más testigo.

## Decisiones cerradas

1. La landing y la tienda usan un `ChatWidget` React accesible y adaptable a móvil.
2. El navegador nunca llama directamente al proveedor LLM. Toda conversación pasa por `platform-api`.
3. `platform-api` crea una sesión anónima, entrega un token opaco, persiste mensajes y llama al `ai-gateway` interno.
4. El chatbot funciona sin credenciales mediante un proveedor de respuestas operativas y preguntas frecuentes. Puede enriquecerse con Ollama o cualquier API compatible con OpenAI.
5. El asistente público responde sobre servicios, reservas, horarios configurados, proceso de taller, seguimiento y búsqueda de repuestos. No confirma diagnósticos, compatibilidad definitiva, precios no publicados ni ejecuta escrituras financieras.
6. Las conversaciones se almacenan en PostgreSQL con expiración, consentimiento y metadatos mínimos. El token de sesión se almacena únicamente como hash.
7. `ai-gateway` se ejecuta en dos réplicas detrás de HAProxy. ChromaDB y el proveedor LLM se consumen como dependencias internas.
8. El perfil local de IA con Ollama es opcional mediante `docker compose --profile local-ai`; la instalación estándar no descarga modelos grandes automáticamente.
9. El logo entregado por SmartDiag504 se incluye como activo de marca. Las fotografías de vehículos/taller siguen siendo fotografías existentes con atribución, no imágenes generadas.
10. La entrega contiene `AGENTS.md`, guía Codex, instalador VPS, verificación, smoke tests, respaldo/restauración, manifiesto, ZIP y checksum.

## Flujo del chatbot

1. El visitante abre el widget y acepta el aviso de privacidad.
2. `POST /api/v1/chat/sessions` devuelve `session_id` y `session_token`.
3. El visitante envía un mensaje a `POST /api/v1/chat/sessions/{session_id}/messages` con el token.
4. La API valida longitud, frecuencia, token y estado de la sesión.
5. La API guarda el mensaje, llama a `ai-gateway /v1/assist`, guarda la respuesta y devuelve texto, modo, fuentes y acciones sugeridas.
6. Las acciones sugeridas son enlaces seguros: reservar, buscar repuesto, WhatsApp o llamar. No son herramientas de escritura.
7. El cliente puede cerrar la sesión; el backend marca `closed_at`.

## Modelos de datos

- `chat_sessions`: id, token_hash, locale, consent, source, status, ip_hash, user_agent_hash, expires_at, closed_at y timestamps.
- `chat_messages`: id, session_id, role, content, mode, model, audit_id, sources, suggested_actions, created_at.

## Seguridad y privacidad

- Token aleatorio de 32 bytes; solo SHA-256 en base de datos.
- Límite por sesión y ventana temporal en PostgreSQL.
- No almacenar IP ni user-agent en claro; solo hash con secreto HMAC.
- CORS restringido, cuerpo limitado y timeout al proveedor.
- Mensajes del sistema impiden escrituras, diagnósticos definitivos y divulgación de información interna.
- El modo público no recibe datos de OT ni historial salvo que exista autenticación futura.
- El servicio sigue disponible en modo FAQ si el LLM o ChromaDB fallan.

## Despliegue

### Una VPS

- Caddy termina TLS.
- HAProxy distribuye landing, PWA, API y AI entre réplicas.
- ERPNext/Frappe, PostgreSQL, MariaDB, Valkey y ChromaDB quedan en redes internas.
- `restart: unless-stopped`, health checks, backups y smoke tests.

### Dos VPS más testigo

- La carpeta `infra/ha/two-node` conserva Patroni/etcd, Galera/garbd, Keepalived y reglas activo/pasivo para Frappe.
- Las evidencias y medios requieren S3 externo; `frappe-sites` requiere almacenamiento compartido validado.
- No se declara HA física hasta completar `HA_ACCEPTANCE.md`.

## Pruebas requeridas

- Sesión, token inválido, expiración, rate limit, persistencia y cierre.
- Proxy AI exitoso y fallback cuando el proveedor falla.
- Guardrails del asistente.
- Widget abre/cierra, crea sesión, envía y muestra respuesta.
- Compose contiene dos AI gateways, HAProxy y variables requeridas.
- Instalador y scripts pasan validación de sintaxis.
- Pruebas Python, TypeScript, compilación y validación estructural antes del ZIP.
