# Paquete de incorporación de empresa — SmartDiag504

## Qué debe entregar la empresa

| Prioridad | Información | Formato | Aprueba |
|---|---|---|---|
| Obligatoria | Datos legales, RTN, sucursales y bodegas | `02_paquete_datos_empresa.xlsx` | Gerencia |
| Obligatoria | Repuestos, costos, precios, existencias y compatibilidad | Ambas plantillas | Bodega/gerencia |
| Obligatoria | Servicios, tiempos, costo y venta | Plantilla 01 | Jefe de taller |
| Obligatoria | Empleados, salarios, seguro, contratos y asistencia | Plantilla 02 | RRHH/gerencia |
| Obligatoria | Usuarios, roles y sucursales permitidas | Plantilla 02 | Dueño |
| Obligatoria | Clientes, vehículos y VIN | Plantilla 02 | Servicio al cliente |
| Obligatoria | Cotizaciones, facturas, recibos, OT y garantías actuales | PDF/HTML/imagen | Gerencia/contador |
| Obligatoria | CAI, rangos y modalidad preimpresa/autoimpresor | Plantilla 02 + respaldo | Contador |
| Recomendada | Proveedores, compras e importaciones abiertas | Plantilla 02 | Compras/contador |
| Recomendada | Cotizaciones, pedidos, fletes y empresas de envío | Plantilla 02 | Ventas/logística |
| Recomendada | Saldos contables de apertura | Plantilla 02 | Contador |
| Opcional | Logos SVG/PNG, colores, textos y firmas | ZIP organizado | Gerencia |
| Opcional | Fotos exactas nombradas por SKU | JPG/PNG/WebP | Bodega |

## Reglas

1. No incluir contraseñas, tokens ni claves bancarias.
2. Fechas `AAAA-MM-DD`, horas `HH:MM`, importes numéricos sin símbolos.
3. VIN, identidad, correo, SKU y proveedor deben ser únicos.
4. Salarios sólo son visibles para RRHH, gerencia y administradores autorizados.
5. Precio de venta no puede quedar debajo del costo total aprobado.
6. Fiscalidad, inventario, nómina y saldos requieren aprobación antes de aplicar.
7. Las credenciales se entregan por canal separado y exigen cambio inicial.

## Orden de carga

1. Empresa, fiscalidad, sucursales y bodegas.
2. Empleados/contratos; después usuarios y roles.
3. Proveedores, catálogo y mano de obra.
4. Existencias conciliadas con contador.
5. Clientes y vehículos por VIN.
6. Compras, cotizaciones, pedidos e importaciones abiertas.
7. Logos y plantillas de impresión.
8. Prueba por rol y acta de aceptación.

Los contenedores saludables no prueban el proceso empresarial: cada flujo debe terminar con evidencia en ERPNext y SmartDiag504.
