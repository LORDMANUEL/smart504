# SmartDiag504 Workshop OS

**Blueprint de producto, arquitectura y contratos — versión 0.1**  
**Fecha:** 11 de agosto de 2026  
**Estado:** propuesta de diseño para aprobación antes de programar el producto ejecutable.

## Decisión recomendada

Construir **SmartDiag504 Workshop OS** como producto propio para la operación automotriz, con:

- **FastAPI + PostgreSQL** para órdenes de trabajo, recepción, diagnóstico, tiempos, evidencias, aprobaciones, control de calidad e historial del vehículo.
- **React/TypeScript** para el portal administrativo y la PWA de técnicos.
- **ERPNext v16** como núcleo financiero y logístico: artículos, precios, bodegas, compras, existencias, POS, facturas, pagos, cuentas por cobrar/pagar, libro mayor, flujo de caja y pérdidas/ganancias.
- **Redis** para colas, caché, sesiones, rate limiting y eventos en tiempo real.
- **ChromaDB** para recuperación semántica de manuales, boletines, casos resueltos y políticas; nunca como fuente transaccional.
- **MinIO/S3** para fotografías, videos, escaneos, firmas, cotizaciones y documentos.
- El motor de alertas existente como base para reglas, eventos, notificaciones y observabilidad.

La arquitectura evita dos errores frecuentes: reinventar contabilidad/inventario desde cero y forzar toda la experiencia del taller dentro de un ERP genérico.

## Qué contiene este paquete

- Investigación comparativa de proyectos open source.
- Tres enfoques posibles y decisión recomendada.
- Arquitectura, límites de dominio y matriz de fuentes de verdad.
- Módulos funcionales y flujo completo de una OT.
- Modelo de datos y diagramas Mermaid.
- Mapa UX/UI por rol y canal.
- Diseño de IA, RAG, ChromaDB, Redis y alertas.
- Seguridad, auditoría, calidad, respaldos y operación.
- Estrategia de licencias y localización fiscal para Honduras.
- Roadmap por gates y criterios de aceptación.
- Árbol propuesto del monorepo.
- Contratos preliminares OpenAPI, eventos, permisos y máquina de estados.

## Principio rector

Cada dato tiene **una sola fuente de verdad**:

- SmartDiag504 controla la operación técnica del taller.
- ERPNext controla inventario valorizado, compras, facturación, caja y contabilidad.
- ChromaDB solo indexa conocimiento.
- Redis solo conserva estado temporal, colas y caché.
- El almacenamiento de objetos conserva evidencias y documentos.

## Uso esperado

Este paquete sirve para revisar y aprobar la arquitectura antes de generar el repositorio ejecutable. No contiene un ERP modificado ni una aplicación lista para producción; sí deja definidos los límites, contratos y criterios necesarios para programarla sin improvisar ni crear deuda técnica estructural.
