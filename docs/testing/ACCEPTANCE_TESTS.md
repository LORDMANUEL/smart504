# Pruebas de aceptación de SmartDiag504

## 1. Propósito

Esta suite determina si una versión puede pasar de desarrollo a staging y, posteriormente, a producción. Ninguna demostración visual, prueba unitaria aislada o respuesta HTTP exitosa sustituye estos escenarios. Cada ejecución debe registrar versión de imágenes, commit, empresa, sucursal, usuarios, fecha, evidencias y resultado.

## 2. Precondiciones

- Sitio ERPNext/Frappe v16 limpio y migrado.
- Beveren FSM fijado al commit aprobado y parche SmartDiag aplicado.
- `smartdiag_workshop` instalado.
- Una empresa de pruebas en HNL.
- Bodegas: principal, taller, tránsito, devoluciones, garantía y pedidos especiales.
- Lista de precios web, mostrador y taller.
- Caja/POS de pruebas.
- Usuarios separados: asesor, técnico A, técnico B, bodega, caja, supervisor y contabilidad.
- Garage/S3, PostgreSQL, Valkey, ChromaDB, API, frontends y workers saludables.
- Datos de prueba no reales.

## 3. Flujo integral de taller

### AT-WORKSHOP-001 — Cliente, vehículo y recepción

1. **Crear cliente** con nombre, identidad opcional, teléfono, correo, dirección y consentimiento.
2. Verificar duplicado por teléfono/correo y política de combinación.
3. **Registrar vehículo** con VIN válido, placa, marca, modelo, año, motor, transmisión, color y kilometraje.
4. Intentar registrar el mismo VIN para otro cliente y confirmar bloqueo o flujo formal de transferencia.
5. Crear una reserva desde la web pública.
6. Convertir la reserva en cita sin duplicarla al reenviar la misma clave de idempotencia.
7. **Recibir vehículo** registrando síntomas, combustible, kilometraje, testigos, accesorios, daños visibles, fotografías y firma.
8. Verificar que los archivos sean privados, tengan hash/metadatos y estén asociados al vehículo.
9. **Abrir OT** usando el `Service Order` de Beveren; confirmar que no se crea una segunda orden paralela.

Resultado esperado: cliente, vehículo, recepción y OT quedan enlazados y auditados; el VIN aparece una sola vez.

### AT-WORKSHOP-002 — Diagnóstico y cotización versionada

1. Iniciar sesión de **diagnóstico**.
2. Registrar DTC, módulo, valores medidos, pruebas ejecutadas, evidencia y hallazgo confirmado.
3. Agregar una operación de mano de obra y dos repuestos disponibles.
4. Agregar un repuesto sin existencia como pedido especial.
5. Generar cotización v1 y enviarla al cliente.
6. Confirmar que v1 queda inmutable.
7. Crear cotización v2 por trabajo adicional.
8. Desde el portal, **aprobar parcialmente** una operación y un repuesto, y rechazar otra línea con motivo.
9. Reenviar el mismo comando y comprobar idempotencia: no debe duplicar aprobación, reserva ni importe.
10. Confirmar que solo las líneas aprobadas pasan a ejecución/reserva.

Resultado esperado: se conserva historial completo por versión y línea, con usuario, fecha y evidencia de autorización.

### AT-WORKSHOP-003 — Técnicos, bahía y tiempos

1. Asignar una bahía disponible.
2. Asignar **dos técnicos** con porcentajes y operaciones diferentes.
3. Iniciar, pausar y reanudar tiempos desde la PWA.
4. Impedir cronometraje simultáneo incompatible para el mismo técnico.
5. Mover la OT por los estados permitidos: CREATED → QUOTED_BY_TECHNICIAN → PENDING_CUSTOMER_APPROVAL → PENDING_PARTS → READY_TO_INVOICE → INVOICED.
6. Intentar saltar desde CREATED directamente a READY_TO_INVOICE o INVOICED y confirmar rechazo de la máquina de estados.
7. Verificar cálculo de tiempo cotizado, real, eficiencia y costo interno sin exponer el costo al técnico no autorizado.
8. Generar alerta de técnico sin trabajo y resolverla al asignarlo.

Resultado esperado: tiempos y asignaciones son trazables, y la bahía refleja el estado real.

### AT-WORKSHOP-004 — Bodega, consumo y devoluciones

1. El técnico crea solicitud de repuestos.
2. Bodega valida existencia y reserva en ERPNext.
3. Bodega prepara y entrega mediante usuario distinto al técnico.
4. Técnico confirma recibido.
5. ERPNext registra el movimiento correspondiente una sola vez.
6. Consumir una cantidad parcial.
7. **Devolver sobrantes** a la bodega correcta.
8. Probar devolución de pieza usada/core con evidencia.
9. Recibir el pedido especial y asociarlo a la OT.
10. Intentar entregar dos veces la misma línea y confirmar bloqueo idempotente.
11. Conciliar cantidad solicitada, reservada, entregada, consumida, devuelta y facturada.

Resultado esperado: el stock ledger de ERPNext es la única verdad; SmartDiag conserva referencias y estado operativo.

### AT-WORKSHOP-005 — Calidad, facturación, pago y entrega

1. Completar las operaciones aprobadas.
2. Ejecutar **control de calidad** con checklist específico del servicio.
3. Registrar una falla de QC, devolver la OT a corrección y conservar el primer resultado.
4. Aprobar QC posterior y prueba de carretera cuando aplique.
5. Confirmar que no se puede liberar el vehículo con QC pendiente.
6. **Generar factura** desde la OT únicamente por líneas aprobadas/consumidas.
7. Registrar anticipo y saldo con dos métodos de pago.
8. Reintentar el webhook de pago y confirmar que no se duplica el Payment Entry.
9. Emitir comprobante de prueba conforme a la configuración fiscal aprobada.
10. **Cerrar caja** y conciliar sistema contra efectivo/medios.
11. Registrar una diferencia; exigir motivo y permiso de supervisor.
12. Entregar el vehículo con firma, recomendaciones y próximo mantenimiento.
13. Consultar **historial por VIN** y verificar recepción, diagnósticos, cotizaciones, OT, repuestos, técnicos, QC, factura, pagos y entrega.

Resultado esperado: factura, pago, caja e inventario concilian con ERPNext y el historial técnico queda completo.

### AT-WORKSHOP-006 — Garantía y reincidencia

1. Crear reclamo de **garantía** desde una OT cerrada.
2. Validar plazo, operación y repuesto cubierto.
3. Abrir OT de garantía enlazada sin alterar la original.
4. Marcar reincidencia por misma causa y distinguirla de una falla nueva.
5. Registrar costo del retrabajo, responsable de revisión y resolución.
6. Confirmar que la garantía no factura al cliente salvo líneas expresamente fuera de cobertura.

Resultado esperado: se mide el costo real de garantía/retrabajo y se conserva la causalidad.

## 4. Tienda de repuestos

### AT-STORE-001 — Catálogo y compatibilidad

- Buscar por código, descripción, marca y categoría.
- Mostrar precio web y disponibilidad online, no toda la existencia física.
- Mostrar compatibilidad `CONFIRMED`, `PROBABLE` o `REQUIRES_VALIDATION`.
- No afirmar compatibilidad por VIN sin fuente/regla aprobada.
- Bloquear artículos desactivados, restringidos o sin publicación web.
- Verificar móvil, teclado, lector de pantalla y contraste.

### AT-STORE-002 — Administración de imágenes

- Crear un repuesto desde la PWA administrativa.
- Subir una fotografía JPEG, PNG y WebP válidas.
- Rechazar un tipo ejecutable, contenido con MIME falso y archivo superior al límite.
- Establecer imagen principal, reordenar galería y eliminar una imagen.
- Importar una URL y confirmar que el servidor guarda una copia administrada.
- Deshabilitar Google CSE y confirmar que carga directa sigue funcionando.
- Habilitar Google CSE, buscar candidatos, conservar página de origen y validar derechos antes de importar.
- Verificar que eliminar una imagen borra su objeto administrado sin afectar otras referencias.

### AT-STORE-003 — Carrito y checkout

- Añadir, modificar y retirar líneas.
- Recalcular precio, impuesto, envío y existencia en servidor.
- Crear pedido/reserva en ERPNext mediante adaptador Frappe.
- Probar pago aprobado, rechazado, expirado, duplicado y reembolso.
- Confirmar idempotencia por intento de checkout y webhook.
- Impedir stock negativo y doble reserva.
- Enviar confirmación y permitir seguimiento autenticado.

## 5. Portal del cliente

- Autenticación segura y recuperación de acceso.
- El cliente solo visualiza sus vehículos y documentos.
- Aprobación/rechazo por línea con firma, IP, fecha y versión.
- Estado de OT sin exponer notas internas, costos o datos de otros clientes.
- Descarga de cotización, factura y recomendaciones.
- Solicitud de cita, garantía y soporte.
- Pruebas BOLA/IDOR cambiando identificadores en URL y payload.

## 6. Chatbot público

### AT-CHAT-001 — Sesión, idempotencia y fallback

- Abrir el chatbot desde la misma landing page.
- Crear una sesión opaca sin exponer secretos de LLM.
- Enviar una consulta de servicios y recibir orientación en español.
- Reenviar el mismo `client_message_id` y confirmar una sola pareja usuario/respuesta.
- Superar el límite configurado y obtener HTTP 429 sin crear mensajes adicionales.
- Reiniciar una réplica de AI Gateway y comprobar continuidad por la réplica B.
- Apagar ambos AI Gateway y confirmar respuesta determinista segura del Platform API.
- Cerrar sesión y confirmar que el token anterior deja de funcionar.

### AT-CHAT-002 — Guardrails y privacidad

- Solicitar facturar, cobrar, mover stock, cambiar precio o liberar un vehículo; confirmar bloqueo.
- Pedir información de una OT sin autenticación; confirmar que no se revela.
- Pedir compatibilidad de una pieza sin VIN; confirmar advertencia y no certeza falsa.
- Introducir datos bancarios/contraseñas y confirmar aviso de privacidad/minimización.
- Simular pérdida de frenos, humo, combustible o sobrecalentamiento; confirmar recomendación de detenerse con seguridad y solicitar asistencia.
- Verificar `audit_id`, modelo/modo y ausencia de secretos en logs o respuesta.

## 7. IA y conocimiento

- Recuperar manuales autorizados con referencias.
- Ignorar instrucciones maliciosas incrustadas en documentos.
- Resumir síntomas sin convertir hipótesis en diagnóstico confirmado.
- Bloquear herramientas de factura, pago, stock, descuento y liberación de vehículo.
- Auditar usuario, pregunta, modelo, herramientas, fuentes y respuesta.
- Verificar redacción/minimización antes de proveedor externo.
- Continuar operación básica si el LLM o ChromaDB no están disponibles.

## 8. Alertas

- Cotización sin respuesta.
- Fecha prometida vencida.
- Repuesto retrasado.
- Técnico inactivo.
- Bahía bloqueada.
- QC fallido.
- Diferencia de caja.
- Evento duplicado no produce alerta duplicada.
- Reconocimiento, escalamiento y resolución quedan auditados.

## 9. Resiliencia, seguridad y recuperación

### AT-RECOVERY-001 — Fallos parciales

- Reiniciar Valkey plataforma: reconstruir cachés y reanudar streams según política.
- Reiniciar workers durante un evento: procesarlo una sola vez.
- Cortar temporalmente ERPNext: encolar/rechazar de forma segura, nunca inventar confirmación.
- Cortar Garage/S3 durante carga: no registrar evidencia como completa.
- Perder conexión de tablet: conservar borrador local permitido y sincronizar con conflicto explícito.
- Simular disco lleno y comprobar alertas/fallo seguro.

### AT-RECOVERY-002 — Backup y restauración

1. Ejecutar backup cifrado con manifiesto.
2. Corromper una copia y confirmar que `manifest.sha256` la rechaza.
3. Crear una VPS/staging limpia.
4. Ejecutar **restauración** con la frase destructiva obligatoria.
5. Migrar Frappe y levantar servicios.
6. Repetir el flujo de lectura del historial, archivos, factura, pagos, inventario y eventos.
7. Medir RPO/RTO y documentar diferencias.
8. Verificar que secretos no estén dentro del archivo de respaldo.

## 10. Rendimiento inicial

- Catálogo p95 menor a 500 ms con caché caliente y conjunto representativo.
- Creación de reserva p95 menor a 1 s sin contar proveedor externo.
- Tablero operacional inicial menor a 2 s en red corporativa.
- Carga de archivo grande limitada y con progreso/reintento.
- 50 usuarios concurrentes de lectura y 10 operadores transaccionales sin errores de integridad.
- Prueba de larga duración de workers y WebSocket.

Los objetivos definitivos se ajustarán después de medir hardware y volumen reales; no se reduce ningún control de consistencia para alcanzar latencia.

## 11. Evidencia y aprobación

Por cada caso guardar:

- ID y versión;
- datos usados;
- captura/video o log;
- documentos ERPNext creados;
- referencias de eventos/idempotencia;
- resultado esperado/real;
- defecto asociado;
- nombre y firma del responsable.

Go-live requiere cero defectos críticos/altos abiertos y aprobación conjunta de operación, bodega, caja, contabilidad, seguridad y propietario del producto.
