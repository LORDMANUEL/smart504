# 09 — Licencias y localización fiscal de Honduras

## 1. Licencias open source

### ERPNext — GPLv3

Puede usarse, modificarse y ofrecerse como servicio. La distribución de una versión modificada exige respetar las obligaciones de GPL. Las personalizaciones, módulos y forma de distribución deben revisarse antes de vender un producto cerrado.

### Odoo Community — LGPLv3

La edición Community usa LGPLv3. La edición Enterprise usa una licencia propia que requiere suscripción válida. No se debe asumir que una función documentada o mostrada comercialmente está disponible en Community sin verificar el módulo concreto.

### Beveren FSM y Frappe Assistant Core — AGPLv3

AGPL extiende obligaciones de disponibilidad de código al uso a través de red. Si SmartDiag504 desea mantener módulos propietarios, no debe copiar o incorporar código AGPL sin aceptar esas obligaciones o negociar otra licencia.

### RepairOS y GarageBuddy — MIT

La licencia es permisiva, pero la licencia no resuelve el riesgo de madurez, mantenimiento o calidad. RepairOS está archivado y GarageBuddy reconoce funciones centrales aún en progreso.

### Dolibarr — GPLv3+

Es viable como ERP abierto, pero su stack y dominio no coinciden con la arquitectura seleccionada.

## 2. Estrategia recomendada de propiedad intelectual

- Código propio de SmartDiag504 en repositorio separado.
- Integración con ERPNext por API, campos personalizados y una app claramente delimitada.
- Registro de dependencias, licencia, versión y avisos.
- No copiar pantallas, textos, marcas ni código de proyectos de referencia.
- Revisión legal antes de distribuir imágenes que contengan ERP modificado.
- Política de contribuciones y cesión/licencia del código creado por terceros.
- Decidir explícitamente si el producto será propietario, open core o AGPL comercial con servicios.

## 3. Facturación en Honduras

El SAR establece que quienes transfieren bienes o prestan servicios deben emitir comprobante fiscal. Reconoce, entre otros, factura, ticket, notas de crédito y notas de débito. La Oficina Virtual permite solicitar inscripción al Régimen de Facturación y el SAR mantiene procedimientos específicos actualizados.

Por ello el producto requiere un **módulo de localización fiscal hondureña** validado por un contador y especialista del SAR antes de producción.

Capacidades mínimas a validar:

- RTN y datos legales del emisor/cliente;
- establecimiento y punto de emisión;
- tipo de documento fiscal;
- CAI, rango autorizado, correlativo y fecha límite;
- impuestos, exoneraciones y descuentos;
- factura, ticket, nota de crédito/débito y anulaciones;
- impresión y representación digital;
- cierre de caja y conservación cronológica;
- auditoría de documentos emitidos, anulados y no utilizados;
- exportes necesarios para declaraciones y revisión contable.

## 4. Regla de implementación

No se programará una “factura bonita” como sustituto de un comprobante válido. La factura se generará en ERPNext mediante una localización o integración fiscal que haya pasado:

1. revisión funcional del contador;
2. prueba con escenarios reales;
3. validación de numeración/rangos/vencimiento;
4. prueba de notas de crédito, anulaciones y devoluciones;
5. respaldo, auditoría y cierre.

Este documento es una guía técnica y no sustituye asesoría legal o tributaria.
