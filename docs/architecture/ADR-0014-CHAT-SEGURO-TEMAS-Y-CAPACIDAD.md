# ADR-0014: chat contextual, temas temporales y protección de capacidad

- Estado: aceptada
- Fecha: 2026-08-24

## Contexto

El asistente público repetía preguntas aunque el cliente ya hubiera entregado nombre, teléfono o vehículo. La landing necesitaba campañas visuales mensuales administrables. Además, una promoción puede concentrar miles de compradores y requiere límites que protejan la venta sin convertir una sola IP en un vector de agotamiento.

## Decisión

1. El gateway de IA extrae únicamente hechos comerciales acotados del historial completo y los incorpora como `CUSTOMER_FACTS`. Nunca interpreta mensajes del cliente ni fragmentos RAG como instrucciones del sistema.
2. Los patrones de extracción limitan tamaño y formato. Se bloquean intentos de revelar instrucciones, cambiar rol o ejecutar órdenes incrustadas. Las consultas de negocio continúan parametrizadas mediante SQLAlchemy; no se concatena entrada del usuario en SQL.
3. La organización configura en Marca un tema mensual, título, mensaje y estado activo. La landing aplica animaciones CSS livianas, respeta `prefers-reduced-motion` y no modifica precios ni contenido transaccional.
4. Coolify/Traefik conserva la terminación TLS; HAProxy interno balancea dos réplicas y limita tasa/concurrencia por IP. Nginx dentro de cada frontend sirve archivos estáticos y añade CSP y cabeceras defensivas. No se instala otro Nginx en el host.
5. La prueba de 10 000 compradores es una prueba escalonada y autorizada. El script inicia con una carga pequeña y sólo alcanza 10 000 VU si el operador define explícitamente `MAX_VUS=10000`. No genera ventas ni altera inventario.

## Consecuencias

- El chat deja de pedir datos ya presentes sin guardar secretos ni aceptar órdenes desde RAG.
- Los temas se activan y retiran sin reconstruir la aplicación.
- Los límites por IP mitigan abuso básico, pero no sustituyen CDN/WAF ni dimensionamiento horizontal para tráfico sostenido.
- Una prueba de 10 000 VU requiere ventana aprobada, observabilidad y generadores distribuidos; no debe ejecutarse desde un único equipo ni contra datos reales.

## Verificación obligatoria

- Unitarias de conversación, prompt injection, tema y entrada SQL hostil.
- Validación de configuración HAProxy/Nginx dentro de las imágenes desplegadas.
- Smoke servido de landing, API, administración y chat.
- Ensayo de carga por peldaños: 100, 500, 1 000, 2 500, 5 000 y 10 000; detener ante error >1%, saturación sostenida o latencia p95 >1,2 s.

