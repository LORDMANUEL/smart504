import { useMemo, useState } from 'react';
import { BookOpenCheck, Check, ChevronLeft, ChevronRight, ExternalLink, GraduationCap, ShieldCheck } from 'lucide-react';

type GuideStatus = 'LISTO' | 'PARCIAL' | 'EXTERNO';
type GuideStep = { title: string; detail: string; action: string; href: string };
type Guide = { id: string; title: string; audience: string; status: GuideStatus; description: string; steps: GuideStep[] };

const platforms = [
  { name: 'Landing del taller', description: 'Promociones, servicios y solicitud pública de cita.', href: '/lading' },
  { name: 'Tienda de repuestos', description: 'Catálogo, compatibilidad por VIN y pedido en línea.', href: '/lading/repuestos' },
  { name: 'Portal del cliente', description: 'Vehículos, citas, alertas, cotizaciones, facturas y perfil.', href: '/lading/loginclie' },
  { name: 'Operación SmartDiag504', description: 'Técnicos, recepción, caja, mostrador, bodega y gerencia.', href: '/tallerv1/login' },
  { name: 'ERPNext administrativo', description: 'Contabilidad, compras, RRHH y maestros autoritativos.', href: 'https://erp.nexusmedi.org/app' },
];

const guides: Guide[] = [
  { id: 'owner', title: 'Puesta en marcha de la empresa', audience: 'Dueño / administrador', status: 'PARCIAL', description: 'Configure empresa, sucursales, bodegas, documentos y accesos sin mezclar organizaciones.', steps: [
    { title: 'Revisar datos de empresa', detail: 'Confirme identidad legal, moneda, zona horaria, sucursales y reglas del taller.', action: 'Abrir configuración', href: '/tallerv1/configuracion' },
    { title: 'Crear personal SmartDiag', detail: 'Cree correo, nombre, código, puesto, rol y contraseña temporal. Empresa y sucursal se obtienen desde la sesión.', action: 'Crear usuarios', href: '/tallerv1/personal' },
    { title: 'Completar maestros ERP', detail: 'Revise Company, Branch, Warehouse y Accounts. Técnicos y cajeros usan SmartDiag salvo necesidad administrativa.', action: 'Abrir ERPNext', href: 'https://erp.nexusmedi.org/app' },
    { title: 'Personalizar documentos', detail: 'Edite versiones HTML/CSS de cotización, diagnóstico, factura, picking, garantía y pase de salida.', action: 'Abrir documentos', href: '/tallerv1/documentos' },
  ]},
  { id: 'reception', title: 'Cita, recepción y apertura de OT', audience: 'Recepción', status: 'LISTO', description: 'Lleve una solicitud pública o autenticada hasta una OT trazable por VIN.', steps: [
    { title: 'Revisar citas', detail: 'Valide cliente, vehículo, fecha, horario y motivo; confirme o reprograme.', action: 'Abrir citas', href: '/tallerv1/citas' },
    { title: 'Confirmar al cliente', detail: 'La confirmación crea el evento y encola la notificación; el canal externo debe estar configurado para entregarla.', action: 'Ver sistema', href: '/tallerv1/sistema' },
    { title: 'Crear o localizar la OT', detail: 'Busque por VIN, placa o cliente y conserve una sola historia del vehículo.', action: 'Abrir Kanban', href: '/tallerv1/login' },
    { title: 'Entregar a bahía', detail: 'Asigne el vehículo al flujo operativo y verifique el estado visible para el equipo.', action: 'Ver bahías', href: '/tallerv1/bahias' },
  ]},
  { id: 'technician', title: 'Diagnóstico técnico con evidencias', audience: 'Técnico', status: 'LISTO', description: 'Diagnóstico, fotos privadas, mano de obra, repuestos e historial de la OT.', steps: [
    { title: 'Abrir tarjeta de OT', detail: 'Confirme VIN, cliente, síntomas y trabajo asignado.', action: 'Abrir Kanban', href: '/tallerv1/login' },
    { title: 'Registrar diagnóstico', detail: 'Documente hallazgos, códigos y recomendaciones verificables.', action: 'Ir a las OTs', href: '/tallerv1/login' },
    { title: 'Tomar fotografías', detail: 'En Fotos suba evidencias de piezas, daños y controles. Son privadas y pueden incluirse en el diagnóstico impreso.', action: 'Abrir OTs', href: '/tallerv1/login' },
    { title: 'Agregar trabajo y piezas', detail: 'Añada mano de obra normal o especializada y solicite piezas compatibles.', action: 'Consultar catálogo', href: '/tallerv1/catalogo' },
    { title: 'Enviar a cotización o calidad', detail: 'Mueva la OT sólo cuando diagnóstico y evidencia estén completos.', action: 'Procesos y calidad', href: '/tallerv1/procesos' },
  ]},
  { id: 'warehouse', title: 'Bodega, picking y devoluciones', audience: 'Bodega', status: 'PARCIAL', description: 'Reserva, ubicación, entrega a OT, devolución, entrada y picking trazable.', steps: [
    { title: 'Revisar solicitudes por OT', detail: 'Priorice solicitudes y confirme bodega, ubicación y cantidad.', action: 'Abrir bodega', href: '/tallerv1/bodega' },
    { title: 'Preparar y entregar', detail: 'Registre quién entrega, quién recibe y la ubicación física.', action: 'Gestionar picking', href: '/tallerv1/bodega' },
    { title: 'Imprimir comprobante', detail: 'Genere el PDF de picking o entrega y adjúntelo al expediente.', action: 'Plantillas', href: '/tallerv1/documentos' },
    { title: 'Registrar devolución o entrada', detail: 'Nunca ajuste existencias sin motivo, referencia y actor autenticado.', action: 'Procesos', href: '/tallerv1/procesos' },
  ]},
  { id: 'cash', title: 'Cotización, aprobación y caja', audience: 'Asesor / cajera', status: 'PARCIAL', description: 'Cotización por VIN, aprobación por líneas, conversión a OT, cobro y cierre.', steps: [
    { title: 'Armar cotización', detail: 'Busque por VIN o dueño, agregue mano de obra y repuestos y revise margen.', action: 'Abrir cotizaciones', href: '/tallerv1/cotizaciones' },
    { title: 'Obtener aprobación', detail: 'El cliente aprueba o rechaza líneas; sólo lo aprobado pasa a OT y factura.', action: 'Ver portal cliente', href: '/lading/loginclie' },
    { title: 'Abrir turno de caja', detail: 'Use código privado, fondo inicial y terminal asignada.', action: 'Abrir caja', href: '/tallerv1/caja' },
    { title: 'Cobrar desde Kanban', detail: 'Seleccione OT aprobada, forma de pago, referencia y documento.', action: 'Cobrar', href: '/tallerv1/caja' },
    { title: 'Arqueo y cierre', detail: 'Cuente efectivo y cierre. Hardware y fiscalidad real requieren certificación externa.', action: 'Cerrar caja', href: '/tallerv1/caja' },
  ]},
  { id: 'counter', title: 'Venta de mostrador', audience: 'Vendedor / cajera', status: 'LISTO', description: 'VIN, búsqueda visual, cotización, venta y autorización de garantía o devolución.', steps: [
    { title: 'Identificar vehículo', detail: 'Ingrese VIN para filtrar compatibilidad o busque nombre, código u OEM.', action: 'Abrir mostrador', href: '/tallerv1/mostrador' },
    { title: 'Preparar carrito', detail: 'Confirme foto, existencia, precio, costo aterrizado y margen.', action: 'Ver productos', href: '/tallerv1/mostrador' },
    { title: 'Cotizar o vender', detail: 'Cotizar envía seguimiento al Kanban comercial; vender exige pago confirmado.', action: 'Continuar venta', href: '/tallerv1/mostrador' },
    { title: 'Devolución o garantía', detail: 'Registre motivo y piezas. El enlace al dueño depende del canal configurado.', action: 'Ver aprobaciones', href: '/tallerv1/mostrador' },
  ]},
  { id: 'ecommerce', title: 'Pedido web y logística', audience: 'Venta en línea / bodega', status: 'PARCIAL', description: 'Pedido, contacto, pago, reserva, tránsito, entrega, devolución o venta perdida.', steps: [
    { title: 'Validar pedido entrante', detail: 'Confirme identidad, teléfono, compatibilidad y existencia.', action: 'Abrir pedidos', href: '/tallerv1/pedidos' },
    { title: 'Contactar y cobrar', detail: 'Registre contacto y avance a pagado sólo con evidencia.', action: 'Kanban de pedidos', href: '/tallerv1/pedidos' },
    { title: 'Reservar y despachar', detail: 'Mueva existencia a tránsito, cargue guía o foto y asigne transportista.', action: 'Abrir bodega', href: '/tallerv1/bodega' },
    { title: 'Cerrar resultado', detail: 'Marque entregado, devuelto, ganado o perdido.', action: 'Ver flujo', href: '/tallerv1/flujos' },
  ]},
  { id: 'procurement', title: 'Compras e importaciones', audience: 'Compras / bodega / contador', status: 'LISTO', description: 'Proveedor, orden, recepción, importación y costo aterrizado con documentos autoritativos en ERPNext.', steps: [
    { title: 'Registrar proveedor', detail: 'Capture código, identidad fiscal, contacto, moneda y plazo. SmartDiag crea o actualiza el proveedor ERP.', action: 'Abrir compras', href: '/tallerv1/compras' },
    { title: 'Preparar orden', detail: 'Agregue SKU, cantidad, costo, moneda, tasa y fecha esperada; revise el total antes de enviar.', action: 'Nueva orden', href: '/tallerv1/compras' },
    { title: 'Aprobar y recibir', detail: 'El flujo DRAFT → SUBMITTED → APPROVED → RECEIVED crea Purchase Order y Purchase Receipt en ERP.', action: 'Kanban de compras', href: '/tallerv1/compras' },
    { title: 'Distribuir importación', detail: 'Registre flete, seguro, aduana e impuestos; al asignar, ERP crea Landed Cost Voucher.', action: 'Importaciones', href: '/tallerv1/importaciones' },
  ]},
  { id: 'human-resources', title: 'RRHH y nómina', audience: 'RRHH / gerencia / contador', status: 'PARCIAL', description: 'Contratos, asistencia, horas extra, permisos y borrador HRMS; deducciones y pago final requieren parametrización contable.', steps: [
    { title: 'Crear contrato', detail: 'Capture datos legales reales, fecha de nacimiento, cargo, inicio, salario y jornada.', action: 'Abrir RRHH', href: '/tallerv1/rrhh' },
    { title: 'Registrar jornada', detail: 'Asistencia y horas extra quedan asociadas al contrato y a la sesión que las registró.', action: 'Asistencia', href: '/tallerv1/rrhh' },
    { title: 'Resolver permisos', detail: 'Aprobar o rechazar vacaciones, incapacidad y permisos deja auditoría.', action: 'Permisos', href: '/tallerv1/rrhh' },
    { title: 'Calcular y revisar', detail: 'SmartDiag calcula salario y hora extra; al aprobar crea un borrador HRMS, nunca un asiento ficticio.', action: 'Nómina', href: '/tallerv1/rrhh' },
  ]},
  { id: 'used-vehicles', title: 'Compra y venta de usados', audience: 'Tasador / ventas / gerencia', status: 'PARCIAL', description: 'Tasación, adquisición, reacondicionamiento, publicación, reserva y venta por VIN.', steps: [
    { title: 'Crear tasación', detail: 'Capture VIN, kilometraje, modalidad, costo, precio objetivo, inspección y evidencias.', action: 'Abrir usados', href: '/tallerv1/usados' },
    { title: 'Aprobar adquisición', detail: 'Al adquirir se crea el maestro serializado en ERP; no se reconoce existencia sin documento de entrada.', action: 'Flujo de usados', href: '/tallerv1/usados' },
    { title: 'Reacondicionar y publicar', detail: 'Controle costos, calidad, fotografías y estado antes de ofrecer la unidad.', action: 'Inventario de usados', href: '/tallerv1/usados' },
  ]},
  { id: 'social', title: 'Hub Social', audience: 'Mercadeo / asesores', status: 'EXTERNO', description: 'Bandeja, consentimiento y respuesta humana; el envío depende del proveedor configurado.', steps: [
    { title: 'Registrar canal', detail: 'Guarde únicamente una referencia secret:// o vault://; nunca pegue credenciales en la pantalla.', action: 'Abrir Hub Social', href: '/tallerv1/social' },
    { title: 'Abrir conversación', detail: 'Capture contacto, consentimiento, asunto y responsable.', action: 'Conversaciones', href: '/tallerv1/social' },
    { title: 'Aprobar respuesta', detail: 'Una persona debe aprobar el mensaje. Sin consentimiento o con proveedor ausente queda bloqueado de forma visible.', action: 'Responder', href: '/tallerv1/social' },
  ]},
  { id: 'erp', title: 'ERP y contabilidad', audience: 'Administración / contador', status: 'PARCIAL', description: 'ERPNext es la fuente financiera y de inventario; SmartDiag es la capa simple del taller.', steps: [
    { title: 'Entrar al escritorio ERP', detail: 'Use una cuenta individual y cambie el idioma a Español en preferencias.', action: 'Abrir ERPNext', href: 'https://erp.nexusmedi.org/app' },
    { title: 'Crear empleado y usuario', detail: 'Cree Employee y vincule User sólo si necesita ERP. Técnicos se crean primero en SmartDiag.', action: 'Abrir empleados', href: 'https://erp.nexusmedi.org/app/employee' },
    { title: 'Compras e inventario', detail: 'Proveedores, órdenes, recepción y costo aterrizado se contabilizan en ERPNext.', action: 'Abrir compras', href: 'https://erp.nexusmedi.org/app/purchase-order' },
    { title: 'Contabilidad y reportes', detail: 'Diario, mayor, CxC, CxP y estados financieros pertenecen al ERP.', action: 'Abrir cuentas', href: 'https://erp.nexusmedi.org/app/account' },
    { title: 'Nómina y asistencia', detail: 'Costeo horario existe; contratos, turnos, vacaciones, deducciones y nómina siguen parciales.', action: 'Personal SmartDiag', href: '/tallerv1/personal' },
  ]},
];

const menuCatalog = [
  ['kanban', 'Kanban', '/tallerv1/login', 'Abrir cada tarjeta, actualizar la OT y verificar su siguiente responsable.'],
  ['bays', 'Bahías', '/tallerv1/bahias', 'Asignar capacidad física y evitar que un vehículo quede sin ubicación.'],
  ['technician-menu', 'Mi trabajo técnico', '/tallerv1/tecnico', 'Atender OT, evidencias, marcación, permisos y vouchers desde la sesión propia.'],
  ['bookings-menu', 'Citas', '/tallerv1/citas', 'Confirmar, reprogramar y convertir la cita en recepción trazable.'],
  ['orders-menu', 'Pedidos web', '/tallerv1/pedidos', 'Validar contacto, pago, reserva, guía, entrega o venta perdida.'],
  ['catalog-menu', 'Catálogo', '/tallerv1/catalogo', 'Mantener piezas, fotos, compatibilidad, costos y precios sin duplicados.'],
  ['quotes-menu', 'Cotizaciones', '/tallerv1/cotizaciones', 'Buscar por VIN, construir líneas, imprimir y convertir lo aprobado en OT.'],
  ['counter-menu', 'Mostrador', '/tallerv1/mostrador', 'Filtrar por VIN o nombre, cotizar, vender y tramitar garantías con autorización.'],
  ['cash-menu', 'Caja', '/tallerv1/caja', 'Abrir turno, cobrar desde Kanban, imprimir, arquear y cerrar.'],
  ['warehouse-menu', 'Bodega', '/tallerv1/bodega', 'Reservar, ubicar, entregar, devolver y documentar cada movimiento.'],
  ['procurement-menu', 'Compras e importación', '/tallerv1/compras', 'Proveedor, orden, recepción y costo aterrizado conciliados con ERPNext.'],
  ['hr-menu', 'RR. HH. y nómina', '/tallerv1/rrhh', 'Usar los submódulos de expedientes, asistencia, permisos, nómina y prestaciones.'],
  ['used-menu', 'Vehículos usados', '/tallerv1/usados', 'Tasación, adquisición, reacondicionamiento, publicación y venta por VIN.'],
  ['process-menu', 'Procesos y calidad', '/tallerv1/procesos', 'Ejecutar controles, evidencias, responsables y cierres de calidad.'],
  ['flow-menu', 'Mapa de flujos', '/tallerv1/flujos', 'Leer eventos y detectar esperas o retrabajos dentro de Procesos y calidad.'],
  ['crm-menu', 'Leads CRM', '/tallerv1/leads', 'Capturar, asignar, dar seguimiento, encuestar y cerrar oportunidades.'],
  ['management-menu', 'Gerencia', '/tallerv1/gerencia', 'Revisar operación, margen, crecimiento y pendientes con trazabilidad.'],
  ['accounting-menu', 'Contador', '/tallerv1/contador', 'Configurar fiscalidad y conciliar documentos sin crear un libro paralelo.'],
  ['marketing-menu', 'Publicidad', '/tallerv1/publicida', 'Crear campañas, subir medios, publicar enlaces y medir clics.'],
  ['social-menu', 'Hub Social', '/tallerv1/social', 'Administrar canales, consentimiento, conversaciones y aprobación humana.'],
  ['admin-menu', 'Administración', '/tallerv1/3gj', 'Revisar configuración corporativa, seguridad y estado de módulos.'],
  ['staff-menu', 'Personal y accesos', '/tallerv1/personal', 'Crear accesos con código automático, rol, MFA y costos protegidos.'],
  ['documents-menu', 'Documentos', '/tallerv1/documentos', 'Elegir impresora, personalizar HTML/CSS, previsualizar, versionar y publicar.'],
  ['guides-menu', 'Guía interactiva', '/tallerv1/guias', 'Elegir un menú, completar pasos y conservar progreso en el navegador.'],
  ['settings-menu', 'Configuración', '/tallerv1/configuracion', 'Definir comportamiento del taller y valores heredables por empresa o sucursal.'],
  ['system-menu', 'Sistema', '/tallerv1/sistema', 'Verificar API, ERP, colas, IA, almacenamiento y servicios de soporte.'],
] as const;
const menuGuides: Guide[] = menuCatalog.map(([id, title, href, description]) => ({ id: `menu-${id}`, title: `Menú: ${title}`, audience: 'Usuario del módulo', status: 'LISTO', description, steps: [
  { title: 'Entender el objetivo', detail: description, action: `Abrir ${title}`, href },
  { title: 'Completar el dato obligatorio', detail: 'Use su sesión individual, confirme empresa y sucursal, y complete los campos requeridos antes de avanzar.', action: 'Practicar en el módulo', href },
  { title: 'Verificar el resultado', detail: 'Confirme estado, historial, responsable, documento o sincronización. Si aparece un error, no duplique la operación.', action: 'Revisar resultado', href },
] }));
const allGuides = [...guides, ...menuGuides];

const progressKey = (id: string) => `smartdiag-guide-progress:${id}`;
function readProgress(id: string) { try { return JSON.parse(localStorage.getItem(progressKey(id)) || '[]') as number[]; } catch { return []; } }

export function GuidedTutorials() {
  const [selectedId, setSelectedId] = useState(allGuides[0].id);
  const [stepIndex, setStepIndex] = useState(0);
  const [completed, setCompleted] = useState<number[]>(() => readProgress(guides[0].id));
  const guide = useMemo(() => allGuides.find((item) => item.id === selectedId) ?? allGuides[0], [selectedId]);
  const current = guide.steps[stepIndex];
  const percent = Math.round((completed.length / guide.steps.length) * 100);
  function selectGuide(id: string) { setSelectedId(id); setStepIndex(0); setCompleted(readProgress(id)); }
  function toggleStep(index: number) { const next = completed.includes(index) ? completed.filter((item) => item !== index) : [...completed, index]; setCompleted(next); localStorage.setItem(progressKey(guide.id), JSON.stringify(next)); }

  return <section className="guided-hub role-view">
    <header className="content-header guided-header"><div><span>Centro de aprendizaje</span><h1>Guía interactiva SmartDiag504</h1><p>Aprenda cada flujo en orden, marque el avance y abra la pantalla donde se realiza.</p></div><div className="guided-security"><ShieldCheck /><span><b>Regla operativa</b><small>ERPNext es la fuente financiera; SmartDiag es la capa de trabajo.</small></span></div></header>
    <section className="platform-launcher" aria-label="Accesos a plataformas">{platforms.map((item) => <a key={item.name} href={item.href} target={item.href.startsWith('http') ? '_blank' : undefined} rel="noreferrer"><ExternalLink /><span><b>{item.name}</b><small>{item.description}</small></span></a>)}</section>
    <div className="guided-layout">
      <aside className="guide-list" aria-label="Tutoriales disponibles"><h2><GraduationCap /> Rutas y cada menú</h2>{allGuides.map((item) => <button key={item.id} className={item.id === guide.id ? 'active' : ''} onClick={() => selectGuide(item.id)}><span><b>{item.title}</b><small>{item.audience}</small></span><em className={`guide-status guide-status--${item.status.toLowerCase()}`}>{item.status}</em></button>)}</aside>
      <article className="guide-player"><header><div><span>{guide.audience}</span><h2>{guide.title}</h2><p>{guide.description}</p></div><b>{percent}%</b></header><div className="guide-progress" role="progressbar" aria-label="Progreso del recorrido" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}><span style={{ width: `${percent}%` }} /></div>
        <ol className="guide-stepper">{guide.steps.map((step, index) => <li key={step.title} className={`${index === stepIndex ? 'active' : ''} ${completed.includes(index) ? 'done' : ''}`}><button className="guide-step-select" onClick={() => setStepIndex(index)} aria-label={`Paso ${index + 1}: ${step.title}`}><span>{completed.includes(index) ? <Check /> : index + 1}</span><b>{step.title}</b></button></li>)}</ol>
        <section className="guide-current-step"><span>Paso {stepIndex + 1} de {guide.steps.length}</span><h3>{current.title}</h3><p>{current.detail}</p><div><button className={completed.includes(stepIndex) ? 'guide-complete done' : 'guide-complete'} onClick={() => toggleStep(stepIndex)}><BookOpenCheck /> {completed.includes(stepIndex) ? 'Paso completado' : 'Marcar completado'}</button><a href={current.href} target={current.href.startsWith('http') ? '_blank' : undefined} rel="noreferrer">{current.action} <ExternalLink /></a></div></section>
        <footer><button onClick={() => setStepIndex((value) => Math.max(0, value - 1))} disabled={stepIndex === 0}><ChevronLeft /> Anterior</button><button onClick={() => setStepIndex((value) => Math.min(guide.steps.length - 1, value + 1))} disabled={stepIndex === guide.steps.length - 1}>Siguiente <ChevronRight /></button></footer>
      </article>
    </div>
  </section>;
}
