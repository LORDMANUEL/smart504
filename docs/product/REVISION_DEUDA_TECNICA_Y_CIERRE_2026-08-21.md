# Revisión de deuda técnica y cierre de módulos

**Corte:** 21 de agosto de 2026  
**Entorno validado:** VPS de pruebas SmartDiag504  
**Dictamen:** no existe evidencia válida para declarar todos los módulos terminados ni deuda técnica cero. El sistema es apto para demostración integral y piloto controlado; no está certificado para producción fiscal con datos reales.

## Evidencia repetida en este corte

- API: 106 pruebas recolectadas y suite completa aprobada en contenedor aislado del VPS.
- Web pública: 6 pruebas aprobadas y build Vite/TypeScript aprobado.
- Portal operativo: 19 pruebas aprobadas y build Vite/TypeScript aprobado.
- Repositorio: 746 archivos, 31 YAML, 35 JSON, 38 servicios y 108 variables de entorno validados.
- Runtime: base, Valkey, Garage/S3, Frappe, esquema, IA y seguridad reportan `ok`.
- Esquema activo: `0031_client_credit_amount`.
- Portable vigente: `smartdiag504-portable-20260821T163118Z.tar.zst`, 501174243 bytes, SHA-256 `d5c1cbf08ba9b287d7489772f7d3ee14da4bf3e7ae3a0ac56ea5456fdee13b50`.
- Debian vigente: `smartdiag504-platform_0.4.0_all.deb`, 34003140 bytes, SHA-256 `00edfb11c43d5b46a9cd5f2810e12e803a95e6b33d18efaea44442c1c210b514`.

## Defecto corregido durante la revisión

La configuración del portal cliente mezclaba una identidad cargada por una sesión SQLAlchemy asíncrona con la sesión síncrona del endpoint, produciendo error 500 al guardar. Además, la interfaz enviaba contraseña, MFA y monto de crédito, pero el servidor ignoraba esos valores.

Se corrigió así:

1. la mutación recarga el usuario dentro de la sesión transaccional correcta;
2. el cambio de contraseña se persiste y se prueba cerrando sesión y autenticando con la nueva clave;
3. la solicitud de crédito conserva el monto en `client_users.requested_credit_amount`;
4. se eliminó la falsa activación MFA mediante checkbox: el estado visible ahora refleja el servidor;
5. una prueba de regresión cubre guardado, monto y cambio real de contraseña.

## Estado real por bloque

| Bloque | Estado comprobado | No declarar terminado hasta |
|---|---|---|
| Landing, tienda y portal | Funcional para demo | pasarela real; comprobante PDF privado ya funciona; MFA cliente es opcional y aún no tiene enrolamiento TOTP |
| Citas, Kanban, técnico y OT | Funcional alto | check-in 360, cronómetro y QC obligatorio ya tienen gate servido; falta firma criptográfica/productiva y capacidad avanzada |
| Cotizaciones, caja y mostrador | Funcional alto | fiscalidad/CAI, hardware, banca y conciliación total con documentos ERP |
| Catálogo, bodega y compras | Funcional alto | Stock Ledger ERP único en todo flujo, lotes/series/conteos y datos reales |
| Importación | Funcional para piloto | aceptación contable, aduana/documentos reales y variaciones de costo |
| RRHH y nómina | Funcional para piloto | estructuras HRMS, pago/asientos, reglas laborales aprobadas y biometría opcional |
| CRM, publicidad y TV | Funcional para demo | automatización, atribución/ROI y proveedores reales |
| Hub Social | Parcial | canales aprobados, webhooks firmados, inbox y SLA reales |
| Contabilidad y reportes | Parcial sobre ERP | configuración y cierre firmado por contador, KPI conciliados y drill-down completo |
| Usados | Funcional básico | financiación, publicación externa, garantías y contabilización aceptada |
| Multiempresa, seguridad y documentos | Funcional alto | prueba de carga, pentest independiente, aceptación por rol y release limpio |

## Bloqueos externos que no se pueden simular

1. contador: empresa, cuentas, impuestos, CAI/rangos y papel preimpreso;
2. SMTP externo: transporte interno ya funciona; faltan PTR/HELO, TLS público, entrega/reputación y Dovecot sólo si habrá buzones;
3. impresoras, gaveta, lector, POS/datáfono y controladores físicos;
4. respaldo cifrado fuera de esta VPS y restauración periódica medida;
5. proveedores Meta/WhatsApp/pasarela si se habilitan;
6. pentest y aceptación formal de usuarios responsables.

## Regla de cierre

Un módulo sólo pasa a **terminado** cuando tiene persistencia autoritativa, permisos y tenant, auditoría, documentos/notificaciones aplicables, errores/reintentos, pruebas unitarias/integración/E2E servidas, conciliación ERP y manual de operación. Una tarjeta visible, HTTP 200 o contenedor saludable no satisface por sí solo ese criterio.
