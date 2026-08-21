# RR. HH. y costeo de mano de obra

## Decisión funcional

SmartDiag504 es la interfaz operativa. ERPNext/HRMS seguirá siendo la fuente laboral y contable final, pero el técnico nunca necesita abrir el escritorio del ERP. La ficha de costos es información protegida para propietario y administración; la OT sólo muestra técnico, servicio, tipo de hora, duración y precio de venta.

## Configuración por técnico

En `Personal y accesos` se configura:

- salario fijo mensual;
- horas productivas mensuales;
- pago variable por hora normal;
- pago variable por hora especializada;
- porcentaje de cargas patronales y costos indirectos;
- tarifa de venta normal y especializada;
- fecha desde la cual rige la política.

Los valores del demo son ilustrativos y deben reemplazarse por los autorizados por la empresa antes de operar en producción.

## Fórmulas

```text
asignación fija por hora = salario fijo mensual / horas productivas mensuales
costo normal por hora = (asignación fija + pago variable normal) × (1 + cargas / 100)
costo especializado por hora = (asignación fija + pago variable especializado) × (1 + cargas / 100)
costo de la labor = horas aplicadas × costo por hora vigente
venta de la labor = horas aplicadas × tarifa de venta vigente
margen bruto = venta de la labor - costo de la labor
```

El servidor rechaza una tarifa de venta inferior al costo real. Al registrar la labor se guarda una fotografía de costo y tarifa; los cambios salariales futuros no alteran las cotizaciones históricas.

## Flujo OT a cotización

1. El administrador configura la política del técnico.
2. En la OT, el técnico abre `Mano de obra`.
3. Selecciona servicio, hora normal o especializada y duración.
4. SmartDiag504 calcula usando la política vigente y registra un evento auditable.
5. `Armar desde OT` transforma cada registro en una línea de cotización.
6. El cliente ve descripción, horas, tarifa y total, pero nunca salario ni costo interno.
7. Gerencia puede estudiar costo, venta, margen y productividad; la contabilización final se sincroniza con ERPNext.

## Persistencia

- `staff_compensation_profiles`: un perfil protegido por técnico y empresa.
- `work_order_labor_entries`: horas y valores congelados por OT.
- `work_order_events`: historial operativo `LABOR_RECORDED`.
- `flow_events`: medición del paso dentro del mapa de procesos.

La migración es `0015_labor_costing`. Los datos tienen organización, claves foráneas, restricciones de horas positivas e índices por técnico, OT y fecha.
