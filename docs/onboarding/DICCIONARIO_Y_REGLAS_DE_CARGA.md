# Diccionario y reglas de carga

## Plantilla 01 — catálogo directamente importable

Se carga en **Operaciones → Catálogo → Importar Excel**, siempre usando primero **Vista previa**.

- Mano de obra: `codigo`, `descripcion`, `marca_vehiculo`, `modelo_vehiculo`, `anio_desde`, `anio_hasta`, `motor`, `tiempo_horas`, `precio_costo_hnl`, `precio_venta_hnl`, `activo`.
- Repuestos: `codigo`, `descripcion`, `numero_oem`, `marca_repuesto`, `unidad`, `marca_vehiculo`, `modelo_vehiculo`, `anio_desde`, `anio_hasta`, `motor`, `precio_costo_hnl`, `precio_venta_hnl`, `activo`.

Código, descripción, marca y modelo son obligatorios; años entre 1900 y 2100; mano de obra mayor que cero; venta mayor o igual al costo. Para varias compatibilidades se repite el código conservando descripción y precios.

## Plantilla 02 — incorporación controlada

Este libro recopila empresa, sucursales, bodegas, empleados, asistencia, proveedores, inventario, clientes, VIN, cotizaciones, compras, importaciones, transportistas, usuarios, fiscalidad, documentos y saldos. No escribe por sí solo: cada área valida y luego un administrador aplica el flujo correspondiente.

El código del empleado se genera automáticamente como `EMP-######`; no debe inventarse. La hoja de usuarios nunca contiene contraseñas. Fiscalidad y saldos contables se bloquean hasta recibir aprobación escrita del contador.

## Corrección

Una fila rechazada no se corrige en la base. Se modifica el archivo fuente, se repite la vista previa y se conserva el informe. Duplicados, costos negativos, venta debajo del costo, referencias inexistentes o identidades/VIN repetidos bloquean la aplicación.
