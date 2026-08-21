# Acta de aceptación funcional sin dependencia del dataset demo

**Fecha:** 21 de agosto de 2026  
**Entorno ejecutado:** VPS aislado de pruebas, `https://taller.nexusmedi.org`  
**Resultado:** candidato funcional aprobado; producción definitiva condicionada a infraestructura y certificaciones externas.

## Alcance

La aceptación creó datos nuevos mediante la API servida y sesiones reales del personal. No se consideraron suficientes los contenedores saludables ni las respuestas HTTP sin contenido. Se validaron persistencia, separación de funciones, permisos, navegador y confirmación de ERPNext.

El VPS continúa identificado como `staging`; no se cambió el dominio de pruebas a producción. El objetivo de esta ejecución fue demostrar que los módulos funcionan con registros nuevos y eliminar la dependencia automática del sembrado de demostración.

## Cambios aplicados

1. `SEED_DEMO_DATA` quedó desactivado por defecto.
2. El sembrador termina sin crear registros cuando `SEED_DEMO_DATA=false`.
3. El readiness productivo rechaza `SEED_DEMO_DATA=true`.
4. El override exclusivo del VPS demo conserva `SEED_DEMO_DATA=true` de forma explícita.
5. Las pruebas empresariales ahora usan sesiones distintas de propietario, revisor y contador; ya no aprueban nómina con el token de recuperación.
6. Se corrigió el contraste de empleados suspendidos sin ocultar su estado.
7. El validador visual dejó de usar evaluación bloqueada por CSP.
8. Se retiraron fixtures frontend sin uso y el texto visible fue cambiado de “demo” a “ejemplo” donde corresponde a una plantilla descargable.

## Evidencia funcional

- Proveedores: creado y `SYNCED` con ERPNext.
- Compras: orden recibida y `SYNCED`.
- Importación: estado `ALLOCATED` y costo distribuido.
- RR. HH.: contrato `SYNCED`, asistencia y horas extra aprobadas.
- Nómina: preparada, revisada y aprobada por tres actores distintos; `APPROVED:SYNCED`.
- Autos usados: unidad creada y adquirida.
- Documentos: plantilla HTML cargada, versionada y exportada.
- Autoservicio técnico: código automático, contrato enlazado, voucher HTML imprimible, marcación y permiso.
- Taller: check-in 360, cronómetro detenido y calidad aprobada.
- OT: `OT-2026-000033` confirmada como `SVC-ORD-2026-00033` en ERPNext, estado `SYNCED`.
- Permisos: aislamiento de sucursal y rechazos 403 correctos para técnico, caja, marketing y contador.
- Navegador: 47 rutas/subvistas con contenido, navegación correcta, logo administrado, cero overlays y cero errores de consola.
- Accesibilidad inicial: 262 combinaciones, cuatro hallazgos serios del mismo selector de empleado suspendido.
- Accesibilidad posterior: 64 páginas del propietario en móvil/escritorio, cero violaciones y cero hallazgos serios.
- Configuración no-demo: prueba roja contra la imagen anterior; posteriormente 3 pruebas aprobadas y salida `demo seed skipped`.

Evidencia durable en el VPS: `/opt/smartdiag504-demo/artifacts/production-acceptance/20260821-session-rbac/` y `/opt/smartdiag504-demo/artifacts/visual-qa/axe-authenticated.json`.

## Defectos detectados y corregidos

| Defecto | Causa | Corrección | Reprueba |
|---|---|---|---|
| 403 al revisar nómina | El validador intentaba preparar y revisar con `system-recovery` | Tres sesiones y actores separados | Nómina `APPROVED:SYNCED` |
| Playwright bloqueado por CSP | Esperas basadas en evaluación de código | Selectores y locators sin `unsafe-eval` | 47 vistas aprobadas |
| Contraste en usuarios suspendidos | Opacidad aplicada al artículo completo | Colores de estado accesibles sin opacidad | 64 páginas, cero violaciones |
| Producción sembraba datos demo | `platform-seed` siempre ejecutaba el dataset | Gate `SEED_DEMO_DATA=false` | 3 pruebas y omisión confirmada |

## Condiciones para la VPS productiva

- Usar `ENVIRONMENT=production` y `SEED_DEMO_DATA=false`.
- Crear secretos nuevos; no trasladar credenciales del VPS de pruebas.
- Crear el primer propietario mediante el instalador/bootstrap y luego crear los demás usuarios desde su sesión.
- Configurar empresa, sucursales, bodegas, listas, impuestos y cuentas ERP antes de operar.
- Ejecutar nuevamente el flujo integral y la conciliación sobre la VPS destino.
- No importar el dump demo en la base productiva.

## Pendientes que impiden una certificación productiva absoluta

1. CAI/fiscalidad aprobada por contador.
2. Impresora, gaveta, lector y datáfono físicos probados.
3. SMTP definitivo con SPF, DKIM, DMARC, entrega y rebote.
4. Respaldo fuera de este VPS y restauración demostrada en infraestructura separada.
5. Instalación limpia y aceptación final en la VPS de destino.

Estos puntos no deben presentarse como terminados. El software ya puede operar sin sembrado demo, pero la certificación productiva final se firma únicamente en la infraestructura destino y con los proveedores externos configurados.
