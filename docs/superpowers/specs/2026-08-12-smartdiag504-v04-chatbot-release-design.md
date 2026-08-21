# SmartDiag504 v0.4 — Chatbot web y release autocontenida

## Objetivo

Entregar un ZIP listo para que Codex lo suba a una VPS y ejecute la instalación Docker de SmartDiag504. La versión v0.4 conserva la arquitectura ERPNext + Beveren FSM + `smartdiag_workshop`, agrega un chatbot público integrado en la landing y corrige dependencias faltantes del paquete v0.3.

## Decisiones

1. El chatbot público vive en `public-web`; nunca contiene secretos ni llama directamente al proveedor LLM.
2. `platform-api` crea sesiones anónimas con token opaco, persiste mensajes y aplica límites. Solo guarda el hash del token.
3. `platform-api` llama al `ai-gateway` por red interna con `AI_GATEWAY_INTERNAL_TOKEN`.
4. El chatbot funciona sin proveedor externo mediante respuestas deterministas de servicios, reservas, repuestos, seguimiento y seguridad. Un proveedor OpenAI-compatible u Ollama es opcional.
5. La IA pública no crea OT, cotizaciones, movimientos de inventario, facturas ni pagos. Para esas acciones deriva al formulario, portal o personal autorizado.
6. El historial enviado al LLM se limita a los últimos mensajes y no incluye secretos administrativos.
7. Dos réplicas de `ai-gateway` se balancean con HAProxy, igual que web y API.
8. El ZIP incluye el código fijado de Beveren FSM con su licencia y parches, evitando un directorio `vendor` vacío.
9. Las fotografías de la landing son archivos reales licenciados/atribuidos; ninguna fotografía automotriz se genera por IA.
10. Una VPS ofrece failover de contenedores, no alta disponibilidad física. El perfil de dos VPS continúa requiriendo almacenamiento/BD replicados y testigo.

## API del chatbot

- `POST /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions/{session_id}/messages`
- `GET /api/v1/chat/sessions/{session_id}/messages`

La creación devuelve `session_token` una sola vez. Las operaciones posteriores requieren `X-Chat-Session-Token`.

## Experiencia

- botón flotante visible en landing y tienda;
- bienvenida y acciones rápidas;
- conversación accesible en escritorio y móvil;
- estado escribiendo, error y reintento;
- enlaces a reservar, catálogo y WhatsApp;
- aviso de que no sustituye diagnóstico ni confirma compatibilidad sin VIN.

## Verificación

- pruebas de sesión, autorización, idempotencia y persistencia;
- pruebas de guardas y respuestas fallback del AI gateway;
- prueba de componente del widget;
- compilación TypeScript de ambas aplicaciones;
- validación de migraciones, Compose, scripts, manifiesto y ZIP;
- configuración Docker validada estáticamente; el runtime completo debe ejecutarse en una VPS con Docker.
