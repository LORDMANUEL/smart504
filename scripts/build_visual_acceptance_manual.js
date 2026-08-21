const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, Footer, Header,
  HeadingLevel, ImageRun, PageBreak, PageNumber, Packer, Paragraph, Table,
  TableCell, TableLayoutType, TableRow, TextRun, VerticalAlign, WidthType,
} = require('docx');

const repo = process.cwd();
const shots = path.join(repo, 'artifacts', 'manual-visual', 'screenshots');
const output = path.join(repo, 'artifacts', 'manual-visual', 'MANUAL_VISUAL_VALIDACION_SMARTDIAG504_2026-08-17.docx');
const RED = 'E3131B';
const DARK = '151922';
const BLUE = '1F4D78';
const MUTED = '667085';
const LIGHT = 'F4F6FA';
const LINE = 'D8DEE8';
const GREEN = '16784B';
const AMBER = 'A15C00';
const USABLE = 9360;

const border = { style: BorderStyle.SINGLE, size: 4, color: LINE };
const cellBorders = { top: border, bottom: border, left: border, right: border };

function run(text, options = {}) {
  return new TextRun({ text, font: 'Calibri', size: options.size || 22, color: options.color || DARK, bold: options.bold, italics: options.italics, break: options.break });
}

function p(text = '', options = {}) {
  return new Paragraph({
    children: Array.isArray(text) ? text : [run(text, options)],
    alignment: options.align || AlignmentType.LEFT,
    spacing: { before: options.before || 0, after: options.after === undefined ? 120 : options.after, line: options.line || 300 },
    keepNext: options.keepNext,
    pageBreakBefore: options.pageBreakBefore,
  });
}

function heading(text, level = 1) {
  return new Paragraph({
    text,
    heading: level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3,
    spacing: { before: level === 1 ? 360 : level === 2 ? 280 : 200, after: level === 1 ? 200 : level === 2 ? 140 : 100 },
    keepNext: true,
  });
}

function bullet(text) {
  return new Paragraph({ children: [run(text)], numbering: { reference: 'bullets', level: 0 }, spacing: { after: 80, line: 300 } });
}

function step(number, title, detail) {
  return new Paragraph({
    children: [run(`${title}. `, { bold: true }), run(detail)],
    numbering: { reference: 'steps', level: 0 },
    spacing: { after: 100, line: 300 },
    keepNext: false,
  });
}

function cell(content, width, options = {}) {
  const children = Array.isArray(content) ? content : [p(content, { after: 40 })];
  return new TableCell({
    children,
    width: { size: width, type: WidthType.DXA },
    borders: cellBorders,
    shading: options.fill ? { fill: options.fill, color: 'auto' } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 100, bottom: 100, left: 120, right: 120 },
  });
}

function table(headers, rows, widths) {
  return new Table({
    width: { size: USABLE, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell([p([run(h, { bold: true, color: 'FFFFFF', size: 20 })], { after: 0 })], widths[i], { fill: DARK })) }),
      ...rows.map((row) => new TableRow({ children: row.map((value, i) => cell(value, widths[i])) })),
    ],
  });
}

function callout(title, text, color = RED) {
  return new Paragraph({
    children: [run(title, { bold: true, color }), run(`\n${text}`)],
    shading: { fill: LIGHT },
    border: { left: { style: BorderStyle.SINGLE, size: 20, color } },
    indent: { left: 180, right: 120 },
    spacing: { before: 120, after: 180, line: 300 },
  });
}

function link(label, url) {
  return new Paragraph({ children: [new ExternalHyperlink({ children: [new TextRun({ text: label, style: 'Hyperlink', font: 'Calibri', size: 22 })], link: url })], spacing: { after: 100 } });
}

async function imageBlock(filename, caption, maxWidth = 640, maxHeight = 430) {
  const file = path.join(shots, filename);
  const metadata = await sharp(file).metadata();
  const scale = Math.min(maxWidth / metadata.width, maxHeight / metadata.height, 1);
  const width = Math.round(metadata.width * scale);
  const height = Math.round(metadata.height * scale);
  return [
    new Paragraph({
      children: [new ImageRun({ data: fs.readFileSync(file), type: 'png', transformation: { width, height }, altText: { title: caption, description: caption, name: filename } })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 70 },
      keepNext: true,
    }),
    p([run(`Figura. ${caption}`, { size: 18, color: MUTED, italics: true })], { align: AlignmentType.CENTER, after: 160 }),
  ];
}

function testBlock(id, title, role, stepsText, expected) {
  return [
    heading(`${id} — ${title}`, 2),
    table(['Campo', 'Detalle'], [
      ['Responsable', role],
      ['Acción', stepsText],
      ['Resultado esperado', expected],
      ['Resultado del evaluador', '[ ] Aprobado   [ ] Parcial   [ ] Falló   [ ] No probado'],
      ['Observación', '________________________________________________________________________________\n________________________________________________________________________________'],
      ['Evidencia', 'Captura o video: __________________________________________   Hora: __________'],
    ], [1900, 7460]),
    p('', { after: 80 }),
  ];
}

function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }

async function build() {
  const children = [];

  children.push(
    p('SMARTDIAG504', { align: AlignmentType.CENTER, size: 24, bold: true, color: RED, after: 420 }),
    p('Manual visual de validación', { align: AlignmentType.CENTER, size: 56, bold: true, color: DARK, after: 100 }),
    p('Guía paso a paso para probar, documentar hallazgos y decidir si el sistema procede', { align: AlignmentType.CENTER, size: 28, color: MUTED, after: 420, line: 320 }),
    ...(await imageBlock('manual-02-centro-smartdiag.png', 'Centro administrativo SmartDiag504 publicado en el VPS de pruebas.', 600, 330)),
    table(['Control', 'Información'], [
      ['Entorno', 'VPS de pruebas — taller.nexusmedi.org / erp.nexusmedi.org'],
      ['Versión evaluada', 'SmartDiag504 Platform 0.4.0 — ERP image 31'],
      ['Fecha del manual', '17 de agosto de 2026'],
      ['Evaluador', 'Nombre: __________________________________________'],
      ['Empresa / cargo', '_________________________________________________'],
    ], [2200, 7160]),
    pageBreak(),
  );

  children.push(
    heading('1. Objetivo y reglas de la evaluación', 1),
    p('Este manual permite que una persona ajena al desarrollo recorra SmartDiag504, anote problemas y emita una decisión verificable. Debe probar el comportamiento real y no aprobar una pantalla únicamente porque abre.'),
    callout('Entorno de prueba', 'Use solamente los datos demo. No ingrese clientes, documentos fiscales, contraseñas personales ni información real. Las credenciales de este manual deben rotarse antes de producción.', AMBER),
    heading('Cómo calificar cada prueba', 2),
    table(['Resultado', 'Cuándo usarlo'], [
      ['Aprobado', 'La tarea se completa, guarda datos y muestra el resultado esperado sin errores.'],
      ['Parcial', 'La tarea funciona, pero existe una limitación visual, de datos o de facilidad de uso.'],
      ['Falló', 'No permite completar la tarea, pierde información, genera error o muestra datos incorrectos.'],
      ['No probado', 'No se pudo ejecutar por falta de datos, equipo, permiso o proveedor externo.'],
    ], [1800, 7560]),
    heading('Severidad de problemas', 2),
    bullet('Crítico: pérdida de datos, acceso no autorizado, contabilidad desbalanceada o cobro/inventario incorrecto.'),
    bullet('Alto: bloquea una operación principal como cita, OT, bodega, factura, pago o nómina.'),
    bullet('Medio: existe alternativa manual, pero causa demora, confusión o riesgo operativo.'),
    bullet('Bajo: detalle visual, redacción o comodidad sin bloquear el trabajo.'),
  );

  children.push(
    heading('2. Accesos y credenciales verificadas', 1),
    callout('Seguridad', 'Estas cuentas son compartidas sólo para la demostración. Cada empleado debe tener una cuenta individual, sucursal y rol antes de usar datos reales.'),
    heading('ERP y centro administrativo', 2),
    link('Abrir ERP SmartDiag504', 'https://erp.nexusmedi.org/app/smartdiag-workshop'),
    table(['Usuario', 'Contraseña temporal', 'Uso'], [
      ['admin@smartdiag504.com', 'SmartDiag504-Demo!2026', 'Centro SmartDiag504, ERP, logs, flujos y contabilidad'],
    ], [3000, 3000, 3360]),
    heading('Operación del taller', 2),
    link('Abrir ingreso del taller', 'https://taller.nexusmedi.org/tallerv1/login'),
    table(['Rol', 'Usuario', 'Contraseña'], [
      ['Propietario', 'demo.admin@smartdiag504.com', 'SmartDiag504-Demo!2026'],
      ['Recepción', 'recepcion.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Técnico', 'tecnico.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Caja', 'caja.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Bodega', 'bodega.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Gerencia', 'gerencia.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Marketing', 'mercadeo.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Auditoría', 'auditor.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
      ['Contador', 'contador.demo@taller.nexusmedi.org', 'SmartDiag504-Demo!2026'],
    ], [1700, 4300, 3360]),
    p([run('Código demo de caja: ', { bold: true }), run('5040')]),
    heading('Portal del cliente', 2),
    link('Abrir portal del cliente', 'https://taller.nexusmedi.org/lading/loginclie'),
    table(['Usuario', 'Contraseña'], [['cliente.demo@smartdiag504.com', 'Cliente504-Prueba-2026!']], [4800, 4560]),
    p('Verificación del 17/08/2026: las nueve cuentas internas devolvieron acceso correcto y el cliente demo inició sesión correctamente.'),
  );

  children.push(
    heading('3. Preparación de la prueba', 1),
    step(1, 'Use una ventana privada', 'Evita que sesiones antiguas mezclen permisos entre roles.'),
    step(2, 'Prepare evidencia', 'Active captura de pantalla. Registre fecha, hora, usuario y URL donde ocurrió cada problema.'),
    step(3, 'Pruebe un rol por vez', 'Cierre sesión antes de cambiar de propietario, técnico, caja, bodega o cliente.'),
    step(4, 'Use identificadores de prueba', 'En textos libres escriba “VALIDACIÓN” y sus iniciales para reconocer los datos creados.'),
    step(5, 'No repita operaciones financieras', 'Si una factura, devolución o pago queda procesado, no presione nuevamente. Registre el resultado.'),
    heading('Datos demo recomendados', 2),
    table(['Dato', 'Valor'], [
      ['Vehículo', 'Ford Escape 2020'],
      ['VIN', '1FMCU0G6XLUA12545'],
      ['OT', 'OT-2026-000008 o una OT identificada como demo'],
      ['Cotización ERP', 'SQ-2026-00001'],
      ['Bahía', 'BAHIA-01'],
      ['Moneda', 'HNL / lempiras'],
    ], [2400, 6960]),
    ...(await imageBlock('manual-01-login.png', 'Pantalla de ingreso al ERP. Escriba el correo administrativo y la contraseña temporal.')),
  );

  children.push(pageBreak(), heading('4. Centro administrativo ERP SmartDiag504', 1));
  children.push(...testBlock('ERP-01', 'Ingreso y lanzador', 'Administrador / contador', 'Entrar al enlace ERP. Confirmar logo, idioma español, cuatro accesos externos, métricas, salud operativa y actividad reciente.', 'Abre SmartDiag504 sin Permission Error, Not found ni módulos técnicos innecesarios.'));
  children.push(...(await imageBlock('manual-02-centro-smartdiag.png', 'Lanzador con métricas, salud de flujos y documentos reales.')));
  children.push(...testBlock('ERP-02', 'Volver a SmartDiag504', 'Administrador / contador', 'Abrir Órdenes de trabajo, una factura y un reporte. Pulsar el botón flotante “Volver a SmartDiag504”.', 'Regresa al centro sin cerrar sesión y sin usar el botón Atrás.'));
  children.push(...(await imageBlock('manual-03-ordenes-servicio.png', 'Lista de órdenes de servicio; el botón de retorno aparece en la esquina inferior.')));
  children.push(...testBlock('ERP-03', 'Conexiones sociales y correo', 'Administrador', 'Abrir “Acceso con redes sociales”, revisar proveedores disponibles y volver a SmartDiag504.', 'La configuración abre sin error. No debe mostrarse Meta/WhatsApp como conectado si no hay credenciales reales.'));
  children.push(...(await imageBlock('manual-04-conexion-social.png', 'Configuración ERP para proveedores de acceso social.')));
  children.push(...testBlock('ERP-04', 'Logs y flujos', 'Auditor / administrador', 'Abrir Flujos SmartDiag, revisar estado, intentos, fecha y último error. Abrir Error Log e Integration Request.', 'Los registros cargan; los fallidos muestran causa. No existen overlays de permiso.'));
  children.push(...(await imageBlock('manual-05-flujos-smartdiag.png', 'Cola de eventos SmartDiag con estado e historial de publicación.')));
  children.push(...testBlock('ERP-05', 'Asientos contables', 'Contador', 'Abrir Asientos contables. Filtrar una factura ACC-SINV. Comparar débitos y créditos por comprobante.', 'Cada factura enviada tiene líneas y débitos = créditos.'));
  children.push(...(await imageBlock('manual-06-asientos-contables.png', 'Asientos contables del ERP con botón de regreso.')));

  children.push(pageBreak(), heading('5. Flujo completo del taller', 1));
  children.push(...testBlock('TAL-01', 'Cita pública y recepción', 'Recepción', 'Desde /lading solicitar una cita. Luego entrar como Recepción, localizarla, confirmar horario y convertirla en recepción/OT.', 'La cita pública queda separada de la cita autenticada; aparece en agenda y conserva cliente, vehículo y motivo.'));
  children.push(...testBlock('TAL-02', 'Crear y trabajar una OT', 'Recepción + técnico', 'Localizar cliente por VIN. Crear/abrir OT. Asignar técnico y bahía. El técnico abre Mi trabajo, registra diagnóstico, tiempo, mano de obra, fotos y solicita repuesto.', 'La OT conserva VIN, estados, responsable, evidencia, tiempos, repuestos e historial.'));
  children.push(...(await imageBlock('tecnico.png', 'Portal técnico servido: trabajo asignado y acciones de la OT.')));
  children.push(...testBlock('TAL-03', 'Cotización y aprobación', 'Recepción / caja / cliente', 'Crear cotización por VIN con mano de obra y repuestos. Generar HTML/PDF. Entrar como cliente y aprobar/rechazar líneas.', 'La cotización queda ordenada por fecha; sólo líneas aprobadas pasan a OT y cobro.'));
  children.push(...testBlock('TAL-04', 'Bodega y entrega', 'Técnico + bodega', 'Solicitar pieza desde OT. Entrar como Bodega, reservar, preparar, entregar y generar picking. Probar devolución de sobrante.', 'La pieza cambia de estado, queda vinculada a OT y genera documentos PDF sin duplicar stock.'));
  children.push(...testBlock('TAL-05', 'Calidad y salida', 'Calidad / recepción', 'Completar control de calidad, evidencia y prueba de ruta cuando aplique. Generar pase de salida.', 'No debe facturarse como terminado si el control obligatorio está pendiente.'));
  children.push(...testBlock('TAL-06', 'Caja y conciliación', 'Caja', 'Abrir caja con código 5040, seleccionar OT aprobada, cobrar, imprimir factura y pase. Ejecutar arqueo y cierre.', 'Pago, factura y cierre quedan registrados. El ERP recibe documento y asiento balanceado.'));

  children.push(pageBreak(), heading('6. Ventas, cliente y ecommerce', 1));
  children.push(...testBlock('VEN-01', 'Mostrador por VIN', 'Caja / vendedor', 'Abrir Mostrador. Buscar VIN 1FMCU0G6XLUA12545. Confirmar piezas compatibles con foto, existencia y precio. Crear cotización directa.', 'La búsqueda filtra compatibilidad y la cotización entra al seguimiento de pedidos.'));
  children.push(...testBlock('VEN-02', 'Devolución o garantía', 'Caja + dueño', 'Solicitar devolución/garantía sobre una venta. Confirmar que requiere autorización y registra motivo/evidencia.', 'No se procesa sin autorización válida; el enlace vence y sólo se usa una vez.'));
  children.push(...testBlock('VEN-03', 'Portal cliente', 'Cliente', 'Entrar con cliente demo. Revisar vehículos, historial, alertas, citas, repuestos, cotizaciones y facturas.', 'Cada sección aparece separada; sólo muestra información del cliente autenticado.'));
  children.push(...testBlock('VEN-04', 'Tienda y pedido web', 'Cliente / caja', 'Buscar pieza por nombre o vehículo, agregar al carrito y enviar pedido. Entrar como Caja y ubicarlo en Kanban.', 'Pedido conserva contacto, compatibilidad y estados: entrado, contactado, pagado, enviado, devuelto, ganado o perdido.'));

  children.push(pageBreak(), heading('7. Compras, RRHH y módulos empresariales', 1));
  children.push(...testBlock('EMP-01', 'Proveedor, compra e importación', 'Compras / bodega / contador', 'Crear proveedor demo, orden de compra, recepción parcial/final e importación con flete/aduana. Revisar costo distribuido.', 'Los estados avanzan sin duplicar recepción y los documentos ERP quedan enlazados.'));
  children.push(...(await imageBlock('compras.png', 'Compras e importaciones con proveedores, recepción y costos.')));
  children.push(...testBlock('EMP-02', 'RRHH y nómina', 'RRHH / contador', 'Crear/revisar empleado, contrato, horario, marcación, permiso, horas extra y nómina. Abrir comprobante del empleado.', 'Código automático, deducciones, prestaciones, seguro y pago quedan separados por submódulo.'));
  children.push(...(await imageBlock('rrhh.png', 'RRHH operacional y nómina organizados por submódulos.')));
  children.push(...testBlock('EMP-03', 'Compra y venta de usados', 'Gerencia / ventas', 'Abrir Usados, revisar tasación, adquisición/consignación, reacondicionamiento, publicación y precio objetivo.', 'La unidad conserva VIN, costos, estado y margen esperado.'));
  children.push(...(await imageBlock('usados.png', 'Inventario y flujo de vehículos usados.')));
  children.push(...testBlock('EMP-04', 'Publicidad y TV', 'Marketing', 'Crear campaña con imagen/video, publicar, abrir enlace TV y revisar clics.', 'La TV muestra sólo campaña publicada y los enlaces registran atribución.'));
  children.push(...(await imageBlock('publicidad-tv.png', 'Vista de publicidad publicada para televisión.')));
  children.push(...testBlock('EMP-05', 'Hub Social', 'Marketing / atención', 'Abrir Hub Social. Revisar canales y conversaciones. No ingresar claves personales durante esta evaluación.', 'Distingue canales configurados y pendientes; no simula mensajes externos.'));
  children.push(...(await imageBlock('social.png', 'Hub Social y estado de configuración de canales.')));
  children.push(...testBlock('EMP-06', 'Guías interactivas', 'Todos los roles', 'Abrir Guía interactiva y seleccionar el rol. Recorrer pasos de cada menú utilizado.', 'La guía explica qué hacer, qué resultado esperar y cómo regresar.'));
  children.push(...(await imageBlock('guias.png', 'Centro de guías para capacitación por rol.')));

  children.push(pageBreak(), heading('8. Personalización de documentos', 1));
  children.push(...testBlock('DOC-01', 'Plantillas HTML y PDF', 'Administrador', 'Abrir Documentos. Exportar una plantilla, editar una copia y cargarla como nueva versión de prueba. Generar vista previa.', 'Factura, cotización, diagnóstico, OT, garantía, pase y documentos de bodega respetan la versión publicada.'));
  children.push(...testBlock('DOC-02', 'Marca por empresa', 'Administrador', 'Cambiar en ambiente demo logo/colores sólo si está autorizado. Revisar vista previa y revertir.', 'La personalización pertenece a la empresa y no modifica otras empresas.'));
  children.push(callout('No aprobar fiscalidad por apariencia', 'El contador debe definir CAI/rangos, impuestos, series, preimpreso o factura electrónica. Una vista PDF correcta no equivale a certificación fiscal.', AMBER));

  children.push(pageBreak(), heading('9. Registro consolidado de problemas', 1));
  children.push(p('Registre una fila por problema. Si es posible, adjunte captura y escriba pasos exactos para repetirlo.'));
  children.push(table(['ID', 'Módulo / URL', 'Descripción y pasos', 'Severidad', 'Estado'], Array.from({ length: 10 }, (_, i) => [
    `H-${String(i + 1).padStart(2, '0')}`,
    '________________',
    '________________________________________________\n________________________________________________',
    '[ ] C [ ] A [ ] M [ ] B',
    '[ ] Abierto [ ] Corregido',
  ]), [700, 1700, 3800, 1500, 1660]));
  children.push(heading('Preguntas de experiencia', 2));
  const questions = [
    '¿Qué tarea fue más difícil de encontrar?',
    '¿Qué pantalla mostró demasiada información?',
    '¿Qué dato faltó para tomar una decisión?',
    '¿Qué paso obligó a volver atrás o repetir trabajo?',
    '¿Qué reporte necesita el dueño diariamente?',
    '¿Qué capacitación requiere cada rol antes de usarlo?',
  ];
  questions.forEach((q, i) => children.push(p([run(`${i + 1}. ${q}`, { bold: true }), run('\n________________________________________________________________________________\n________________________________________________________________________________')], { after: 160 })));

  children.push(pageBreak(), heading('10. Decisión final: procede o no procede', 1));
  children.push(callout('Criterio mínimo para proceder', 'Deben aprobar cita→OT→diagnóstico/fotos→cotización/aprobación→bodega→calidad→factura/pago, sin defectos críticos o altos abiertos. Contabilidad debe balancear y cada rol debe ver sólo lo autorizado.', GREEN));
  children.push(table(['Decisión', 'Marque una opción'], [
    ['PROCEDE', '[ ] Puede continuar a la siguiente fase con los límites anotados.'],
    ['PROCEDE CON CONDICIONES', '[ ] Requiere corregir los hallazgos enumerados antes de nueva validación.'],
    ['NO PROCEDE', '[ ] Existe al menos un bloqueo crítico/alto o el flujo principal no termina.'],
  ], [3100, 6260]));
  children.push(
    heading('Resumen obligatorio del evaluador', 2),
    p('Pruebas aprobadas: ______ / ______     Parciales: ______     Fallidas: ______     No probadas: ______'),
    p('Defectos críticos: ______     Altos: ______     Medios: ______     Bajos: ______'),
    p('Condiciones o correcciones requeridas:\n________________________________________________________________________________\n________________________________________________________________________________\n________________________________________________________________________________'),
    p('Comentario final:\n________________________________________________________________________________\n________________________________________________________________________________\n________________________________________________________________________________'),
    p('Nombre y firma: ____________________________________   Fecha: __________________'),
    p('Aprobación del propietario: __________________________   Fecha: __________________'),
    heading('Cómo devolver el resultado', 2),
    bullet('Guarde este archivo con el nombre: VALIDACION_SMARTDIAG504_[NOMBRE]_[FECHA].docx.'),
    bullet('Adjunte capturas o videos usando el ID del hallazgo: H-01, H-02, etc.'),
    bullet('Envíe el manual completo, aunque existan pruebas no ejecutadas.'),
    bullet('No borre fallos después de corregirlos: márquelos Corregido y repita la prueba.'),
  );

  const doc = new Document({
    creator: 'SmartDiag504',
    title: 'Manual visual de validación SmartDiag504',
    description: 'Guía UAT con credenciales demo, capturas, casos y decisión procede/no procede.',
    numbering: {
      config: [
        { reference: 'bullets', levels: [{ level: 0, format: 'bullet', text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 }, spacing: { after: 80, line: 300 } } } }] },
        { reference: 'steps', levels: [{ level: 0, format: 'decimal', text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 }, spacing: { after: 100, line: 300 } } } }] },
      ],
    },
    styles: {
      default: { document: { run: { font: 'Calibri', size: 22, color: DARK }, paragraph: { spacing: { after: 120, line: 300 } } } },
      paragraphStyles: [
        { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal', run: { font: 'Calibri', size: 56, bold: true, color: DARK }, paragraph: { spacing: { after: 100 } } },
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Calibri', size: 32, bold: true, color: RED }, paragraph: { spacing: { before: 360, after: 200 }, keepNext: true } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Calibri', size: 26, bold: true, color: BLUE }, paragraph: { spacing: { before: 280, after: 140 }, keepNext: true } },
        { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { font: 'Calibri', size: 24, bold: true, color: DARK }, paragraph: { spacing: { before: 200, after: 100 }, keepNext: true } },
      ],
    },
    sections: [{
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 1080, bottom: 1080, left: 1080, header: 708, footer: 708 } },
      },
      headers: { default: new Header({ children: [p([run('SMARTDIAG504  |  Manual visual de validación', { size: 18, color: MUTED, bold: true })], { after: 0 })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [run('VPS de pruebas  •  Página ', { size: 18, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], font: 'Calibri', size: 18, color: MUTED })] })] }) },
      children,
    }],
  });

  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, await Packer.toBuffer(doc));
  console.log(output);
}

build().catch((error) => { console.error(error); process.exit(1); });
