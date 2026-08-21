# 00 — Investigación open source y selección tecnológica

## 1. Contexto real de SmartDiag504

La presencia pública encontrada presenta a SmartDiag504 como taller de San Pedro Sula especializado en diagnóstico, programación y reparación automotriz Ford. También comunica servicios de aire acondicionado y reparación de transmisiones Ford. Esto orienta el producto hacia trazabilidad técnica, evidencia del diagnóstico, programación electrónica, historial por VIN y una experiencia de atención especializada, no solo hacia una caja de repuestos.

## 2. Enfoques evaluados

### Enfoque A — Adoptar un sistema automotriz open source completo

**Ventaja:** parece reducir el trabajo inicial.  
**Riesgo:** los proyectos encontrados no cubren con suficiente profundidad contabilidad, compras, valorización de inventario, fiscalidad, conciliación de caja, seguridad y operación sostenida.

**Conclusión:** rechazado como núcleo de producción. Es útil únicamente para estudiar pantallas, flujos y modelos de datos.

### Enfoque B — Construir todo dentro de ERPNext

**Ventaja:** menor complejidad de sincronización; inventario, compras, ventas, POS y contabilidad ya viven en una sola plataforma.  
**Riesgo:** la experiencia de recepción, bahías, diagnóstico, técnicos, fotografías, aprobaciones y PWA queda muy ligada a Frappe y puede sentirse como un ERP adaptado en vez de un producto automotriz especializado.

**Conclusión:** opción válida para un despliegue interno económico, pero menos flexible como producto comercial diferenciado.

### Enfoque C — SmartDiag504 Workshop OS + ERPNext por adaptador

**Ventaja:** UX automotriz propia, motor de alertas reutilizable, API Python limpia y libertad para vender el producto; ERPNext conserva las áreas en las que un error es más costoso: inventario, compras, caja y contabilidad.  
**Riesgo:** exige integración idempotente, conciliación y límites estrictos para evitar doble fuente de verdad.

**Conclusión:** **recomendado**.

## 3. Proyectos evaluados

| Proyecto | Qué aporta | Limitación relevante | Uso recomendado |
|---|---|---|---|
| **ERPNext v16** | Contabilidad, ventas, compras, existencias, almacenes, POS, pagos, reportes, API y framework Python | No es un DMS/taller automotriz especializado; requiere app e integración propias | Núcleo ERP y fuente de verdad financiera/logística |
| **Odoo Community 19** | ERP amplio, reparación genérica, POS, e-commerce, inventario y reportes | La reparación estándar está orientada a productos devueltos; hay que revisar qué capacidades dependen de Enterprise | Alternativa estratégica a ERPNext, no primera elección |
| **Beveren FSM** | Flujo solicitud → cotización → orden → agenda → ejecución → factura; React/TypeScript sobre ERPNext | Proyecto joven, AGPL y orientado a servicio de campo, no a recepción vehicular | Referencia de arquitectura y experiencia técnica |
| **RepairOS** | Multiempresa, OT, inventario, roles, portal técnico y enfoque SaaS | El repositorio fue archivado el 8 de julio de 2026 y quedó en solo lectura | Referencia de dominio; no adoptar ni depender de él |
| **GarageBuddy** | Usuarios, vehículos e historial de servicio | El propio repositorio marca el seguimiento de servicios como trabajo en progreso | Referencia menor; no base productiva |
| **Dolibarr** | ERP/CRM maduro con cotizaciones, facturas, compras, stock, POS y contabilidad | Stack PHP y sin dominio automotriz profundo | Plan B ligero para empresas pequeñas |
| **Frappe Assistant Core** | MCP/LLM conectado a permisos de ERPNext y auditoría de llamadas | AGPL; incluye herramientas que deben restringirse en un sistema financiero | Referencia para la capa IA y permisos, no copiar sin decidir licencia |

## 4. Matriz de decisión técnica

Puntuación estimada de 1 a 5. Es una evaluación de adecuación a SmartDiag504, no una calificación absoluta de cada proyecto.

| Criterio | Peso | ERPNext | Odoo CE | Beveren FSM | RepairOS | GarageBuddy | Dolibarr |
|---|---:|---:|---:|---:|---:|---:|---:|
| Madurez operativa | 20% | 5 | 5 | 2 | 1 | 2 | 4 |
| Finanzas, compras e inventario | 20% | 5 | 5 | 4 | 2 | 1 | 4 |
| Ajuste al taller automotriz | 20% | 3 | 3 | 4 | 4 | 2 | 2 |
| Python/API/extensibilidad | 15% | 5 | 4 | 5 | 4 | 1 | 2 |
| TypeScript/UX propia | 10% | 3 | 3 | 5 | 2 | 1 | 1 |
| Riesgo de licencia/comercialización | 10% | 3 | 4 | 2 | 5 | 5 | 3 |
| Comunidad y continuidad | 5% | 5 | 5 | 2 | 1 | 2 | 4 |
| **Resultado ponderado** | **100%** | **4.30** | **4.20** | **3.55** | **2.70** | **1.80** | **3.00** |

## 5. Decisión final

1. **ERPNext v16** como back office de negocio y contabilidad.
2. **SmartDiag504 Workshop OS** como operación técnica, experiencia de usuario, portal, PWA, IA y alertas.
3. **Beveren FSM, Odoo Repairs, RepairOS y GarageBuddy** solo como referencias funcionales; no como dependencia central.
4. Integración por API y eventos, con adaptadores reemplazables para permitir Odoo u otro ERP en el futuro.
5. Revisión legal de GPL/AGPL/LGPL antes de incorporar código de terceros al producto comercial.
