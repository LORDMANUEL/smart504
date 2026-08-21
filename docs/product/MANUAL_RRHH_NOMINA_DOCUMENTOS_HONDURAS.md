# Manual operativo: RR. HH., nómina, documentos e impresión

Fecha de corte: 17 de agosto de 2026  
Entorno: demo de pruebas `taller.nexusmedi.org`

## 1. Alcance y regla de autoridad

SmartDiag504 es la capa sencilla de operación. Conserva expedientes, marcaciones, solicitudes, cálculos explicables y comprobantes como proyección operacional. ERPNext/HRMS debe conservar el empleado, la entrada de nómina y los documentos contables autoritativos. No se crea un libro contable paralelo.

Una nómina no debe aprobarse si falta la política vigente del contador, la conciliación con HRMS, la validación de empleados o el soporte del pago. El sistema no incluye tasas ocultas: cada deducción y aporte guarda código, tipo, porcentaje o monto, techo, vigencia, fuente y aprobador.

## 2. Accesos

- Administración de RR. HH.: `https://taller.nexusmedi.org/tallerv1/rrhh`
- Portal del técnico y autoservicio: `https://taller.nexusmedi.org/tallerv1/tecnico`
- Personal, roles, MFA y accesos: `https://taller.nexusmedi.org/tallerv1/personal`
- Plantillas y perfiles de impresión: `https://taller.nexusmedi.org/tallerv1/documentos`
- Guía interactiva de cada menú: `https://taller.nexusmedi.org/tallerv1/guias`
- ERPNext/HRMS: `https://erp.nexusmedi.org/app`

Cada persona utiliza una cuenta individual. El código `EMP-000001` se genera automáticamente en el servidor. Si el acceso ya existe, el contrato reutiliza exactamente ese código; no se permite que acceso, asistencia y nómina identifiquen a la misma persona con códigos diferentes. El correo del expediente permite vincular el contrato con el acceso ya creado.

## 3. Submódulos de RR. HH.

### 3.1 Expedientes y contratos

Registra nombre completo, identidad, fecha de nacimiento, dirección, teléfono, correo, cargo, tipo de contrato, inicio, jornada, número IHSS, seguro/póliza, forma de pago, tarifa por periodo y equivalente mensual.

Formas de pago admitidas:

- Mensual: tarifa × días del periodo / 30.
- Quincenal: tarifa × días del periodo / 15.
- Semanal: tarifa × días del periodo / 7.
- Diario: tarifa × días con asistencia.
- Por hora: tarifa × horas regulares registradas.

El equivalente mensual se conserva separado porque interviene en costos, promedios y prestaciones. Terminar el contrato no borra el historial; cambia su estado y encola la actualización en HRMS.

### 3.2 Marcaciones y horas

El empleado entra a **Mi trabajo técnico → Marcar entrada/salida**. La entrada queda sellada con la sesión y hora del servidor. La salida calcula horas regulares y deja el exceso en estado pendiente. RR. HH. aprueba o rechaza las horas extra con nota de auditoría.

El formulario administrativo de jornada se usa únicamente para correcciones justificadas. No debe sustituir la marcación diaria del empleado.

### 3.3 Permisos y vacaciones

El empleado solicita vacaciones, incapacidad, permiso personal, maternidad, paternidad o permiso sin goce desde su portal. RR. HH. decide desde su submódulo. Solicitud, actor y decisión permanecen en historial.

La referencia oficial de SETRASS establece como mínimo 10 días tras el primer año, 12 tras el segundo, 15 tras el tercero y 20 desde el cuarto; el salario de vacaciones utiliza el promedio ordinario de los últimos seis meses o la fracción disponible. La acumulación y excepciones deben ser revisadas por RR. HH. y el contador.

### 3.4 Nómina y vouchers

1. El contador crea reglas vigentes para IHSS, RAP, seguro, préstamos u otras deducciones.
2. Se registra por cada regla si corresponde al empleado o al patrono, si es porcentaje o monto fijo, el techo aplicable, fecha y fuente.
3. RR. HH. selecciona el periodo y calcula el borrador.
4. El cálculo usa la forma de pago de cada contrato, asistencia, horas extra aprobadas, ajustes y política vigente.
5. Se crea un voucher individual con bruto, deducciones, aportes patronales, neto y desglose.
6. Revisar cambia el estado; aprobar emite los vouchers y encola la entrada de nómina de HRMS con los empleados sincronizados.
7. El asiento y el pago sólo se consideran realizados cuando ERPNext/HRMS confirma.

Si una empresa paga frecuencias diferentes, se recomienda ejecutar periodos separados por frecuencia para que el `Payroll Entry` de HRMS conserve una frecuencia coherente.

### 3.5 Seguro y prestaciones

El estimador usa fecha de ingreso, terminación y promedio ordinario mensual. Presenta preaviso, cesantía, vacaciones proporcionales, décimo tercero y décimo cuarto proporcionales. Aplica las tablas de la guía SETRASS: preaviso según antigüedad, cesantía proporcional con máximo de 15 meses y divisores de vacaciones 36/30/24/18.

El resultado es una estimación de apoyo, no una liquidación automática. Antes de pagar deben validarse causa de terminación, promedio real de seis meses, horas extra habituales, salario en especie, embarazo u otras protecciones, contrato colectivo, pagos previos y reformas vigentes.

Fuentes primarias:

- Código del Trabajo: <https://www.trabajo.gob.hn/wp-content/uploads/2016/07/DEPARTAMENTO_DE_INSPECTORIA._ART._614_CODIGO_DEL_TRABAJO.pdf>
- Guía oficial de cálculo: <https://www.trabajo.gob.hn/wp-content/uploads/2017/11/guiacalculo.pdf>
- Consulta SETRASS de prestaciones: <https://consulta.trabajo.gob.hn/decretos/scr/Prestaciones.htm>
- Tabla de salario mínimo 2026–2027: <https://www.trabajo.gob.hn/ppt_viewer/tabla-de-salario-minimo-y-bono-educativo-2026-2027/>

## 4. Portal del técnico

El enlace `/tallerv1/tecnico` queda dividido en:

- **Mis órdenes:** diagnóstico, fotografías, piezas, mano de obra y calidad.
- **Marcar entrada/salida:** jornada del día y horas resultantes.
- **Mis permisos:** formulario y estados de solicitudes propias.
- **Mis vouchers:** únicamente comprobantes aprobados o contabilizados del contrato asociado a la sesión. **Imprimir voucher** abre un HTML aislado en tamaño Carta con bruto, deducciones, aporte patronal y neto; desde el navegador puede imprimirse o guardarse como PDF sin imprimir el resto del portal.

Un técnico nunca puede consultar nóminas o vouchers de otra persona. Si aparece “usuario no vinculado”, el administrador debe crear el acceso y registrar el mismo correo en el expediente laboral.

## 5. Centro de documentos e impresión

Cada formato conserva HTML, CSS, variables, sucursal, historial de versiones y perfil de impresión. Reemplazar un archivo crea un borrador nuevo y nunca modifica documentos ya emitidos.

El asistente pregunta:

- salida PDF/navegador, impresora normal, térmica o papel preimpreso;
- tamaño Carta, A4, térmico 80 mm o 58 mm;
- orientación, márgenes y número de copias;
- si se muestra el logotipo;
- si la hoja ya contiene membrete o campos preimpresos.

Flujo seguro: crear o cargar HTML/CSS UTF-8 → elegir impresora → vista previa → prueba de impresión → guardar versión → revisión → publicar. Facturas, cotizaciones, diagnósticos, OT, garantías, pases, picking, entregas, devoluciones y entradas utilizan la versión publicada correspondiente a empresa/sucursal.

Los scripts, eventos HTML y recursos externos permanecen bloqueados. Los colores, logo y datos de empresa se insertan por variables aprobadas. La prueba final debe hacerse en el modelo real de impresora antes de producción.

## 6. Guía interactiva por menú

`/tallerv1/guias` incluye rutas completas por rol y un tutorial individual para cada menú visible: Kanban, bahías, técnico, citas, pedidos, catálogo, cotizaciones, mostrador, caja, bodega, compras, RR. HH., usados, procesos, mapa de flujos, CRM, gerencia, contador, publicidad, Hub Social, administración, personal, documentos, configuración y sistema.

Cada tutorial explica objetivo, dato obligatorio y verificación final. El progreso se conserva por tutorial en el navegador; no altera datos empresariales.

## 7. Datos y API

Migración: archivo `0025_honduras_payroll_self_service.py`, revisión `0025_hn_payroll`.

Tablas nuevas:

- `payroll_policies`: reglas versionadas aprobadas.
- `payroll_vouchers`: comprobante individual por empleado y corrida.

Campos ampliados de `employee_contracts`: identidad, dirección, contacto, seguridad social, seguro, frecuencia y tarifa base.

Rutas principales:

- `POST /api/v1/operations/enterprise/hr/contracts`
- `GET|POST /api/v1/operations/enterprise/hr/payroll-policies`
- `POST /api/v1/operations/enterprise/hr/payroll-runs`
- `GET /api/v1/operations/enterprise/hr/payroll-vouchers`
- `POST /api/v1/operations/enterprise/hr/prestations/preview`
- `GET /api/v1/staff/self-service/overview`
- `POST /api/v1/staff/self-service/punch`
- `POST /api/v1/staff/self-service/leave-requests`
- `GET /api/v1/staff/self-service/vouchers/{voucher_id}/html`

El tipo documental `PAYSLIP` también está disponible en el centro de formatos para que cada empresa publique su propio diseño de voucher. El endpoint de autoservicio valida organización, contrato, dueño y estado aprobado/contabilizado; devuelve `404` ante un comprobante ajeno y marca la respuesta como privada y no cacheable.

## 8. Criterios antes de producción

- El contador valida por escrito tasas, techos, salario mínimo, 13.º/14.º, deducciones y política efectiva.
- Se configura HRMS, cuentas por pagar de nómina, Salary Structures y asignaciones.
- Se prueba una nómina completa: marcación → permiso → horas extra → cálculo → voucher → aprobación → entrada HRMS → pago → asiento → conciliación.
- Se prueba cada formato en PDF, láser/tinta, térmica o papel preimpreso que realmente usará la empresa.
- Se valida aislamiento por empresa/sucursal, privacidad de vouchers y revocación de sesiones.
- Se configura respaldo externo y restauración periódica en infraestructura distinta al VPS de pruebas.

No declarar “cumplimiento legal certificado” ni “nómina pagada” solamente porque el cálculo o el contenedor responda correctamente.
