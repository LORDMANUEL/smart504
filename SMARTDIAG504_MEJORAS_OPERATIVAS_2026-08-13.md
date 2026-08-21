# SmartDiag504 - mejoras operativas 2026-08-13

Este corte convierte pantallas demostrativas en flujos persistentes para OT, diagnostico fotografico, cotizaciones por VIN, caja, bodega, calidad, notificaciones y CRM.

La especificacion funcional, estados, rutas, limites de hardware y decisiones de seguridad esta en [docs/operations/OT_COTIZACION_CAJA_BODEGA_CRM_2026-08-13.md](docs/operations/OT_COTIZACION_CAJA_BODEGA_CRM_2026-08-13.md).

## Criterio de terminado

Una tarjeta visual no se considera un modulo terminado. Cada flujo debe tener persistencia, validacion de servidor, trazabilidad, documento cuando aplica y una prueba sobre el runtime servido.

## Limites declarados

- La notificacion interna del portal es funcional; email, SMS o WhatsApp requieren proveedor y credenciales.
- Los PDF y HTML de caja son imprimibles; impresora termica, gaveta y POS fisicos requieren el equipo para certificar controlador, corte, ancho y apertura.
- Las imagenes genericas completan la demo, pero una venta real debe usar la fotografia exacta del repuesto.

