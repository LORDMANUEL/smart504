import { useEffect, useState, type CSSProperties } from 'react';
import { ArrowRight, BadgeDollarSign, BarChart3, Bot, Box, CalendarCheck, CheckCircle2, ClipboardList, Copy, FileDown, FileText, Image, Instagram, Link2, MapPin, Megaphone, MessageCircle, MousePointerClick, PackageCheck, Plus, RotateCcw, ShieldCheck, ShoppingCart, Tv, Upload, UserCog, Video, Warehouse, Wrench } from 'lucide-react';
import { createCampaign, getAdminDocument, getCampaigns, getPublicCampaigns, publishCampaign, uploadCampaignMedia } from '../lib/api';
import type { FlowHeatmapCell, ManagementSummary, MarketingCampaign, OperationsOverview, StaffUser, WorkOrderCard, WorkOrderPartRequest } from '../types';
import { useBranding } from '../lib/branding';

type RecordFlow = (module: string, action: string, itemReference: string, metadata?: Record<string, unknown>) => Promise<void>;

type WarehouseRequest = { workOrder: WorkOrderCard; part: WorkOrderPartRequest };

export function LegacyWarehouseView({ workOrders, onDeliver }: { workOrders: WorkOrderCard[]; onDeliver: (workOrder: WorkOrderCard, requestId: string, location: string) => Promise<void> }) {
  const requests: WarehouseRequest[] = workOrders.flatMap((workOrder) => (workOrder.parts_required ?? []).filter((part) => part.request_id).map((part) => ({ workOrder, part })));
  const delivered = requests.filter(({ part }) => part.status === 'DELIVERED').length;
  async function deliver({ workOrder, part }: WarehouseRequest) {
    if (!part.request_id || part.status === 'DELIVERED') return;
    const location = window.prompt(`Ubicación de ${part.sku}:`, part.location === 'Por asignar en bodega' ? 'A-01-01' : part.location);
    if (location?.trim()) await onDeliver(workOrder, part.request_id, location.trim());
  }
  return <div className="role-view"><header className="content-header"><div><span>Bodega</span><h1>Picking y entrega de repuestos</h1><p>Cada solicitud proviene de una OT y su entrega queda registrada para el cobro final.</p></div></header><div className="warehouse-ticket"><div className="ticket-heading"><div><ClipboardList /><span><strong>Cola real de picking</strong><small>Solicitudes creadas desde el detalle de la OT</small></span></div><b>{delivered}/{requests.length} entregados</b></div>{requests.map((request) => { const { part, workOrder } = request; const done = part.status === 'DELIVERED'; return <article className={done ? 'pick-row pick-row--done' : 'pick-row'} key={part.request_id}><span className="pick-code">{part.sku}</span><div><strong>{part.name}</strong><small>{workOrder.external_reference} · Cantidad {part.quantity} · {part.actor}</small></div><span className="pick-location"><MapPin /> {part.location}</span><button disabled={done} onClick={() => void deliver(request)}>{done ? <><CheckCircle2 /> Entregado</> : <><PackageCheck /> Registrar entrega</>}</button></article>; })}{requests.length === 0 && <p className="empty-bookings">No hay solicitudes pendientes. Abra una OT y pida un repuesto para crear el ticket.</p>}<footer><ShieldCheck /><span>La entrega actualiza la OT y conserva responsable, fecha y ubicación para auditoría y facturación.</span></footer></div></div>;
}

export function WarehouseView({ token, workOrders, onStatus }: { token: string; workOrders: WorkOrderCard[]; onStatus: (workOrder: WorkOrderCard, requestId: string, status: string, location: string, note?: string) => Promise<void> }) {
  const requests: WarehouseRequest[] = workOrders.flatMap((workOrder) => (workOrder.parts_required ?? []).filter((part) => part.request_id).map((part) => ({ workOrder, part })));
  const columns = [{ status: 'REQUESTED', label: 'Solicitado' }, { status: 'PICKING', label: 'En picking' }, { status: 'READY', label: 'Listo' }, { status: 'DELIVERED', label: 'Entregado a OT' }, { status: 'RETURN_REQUESTED', label: 'Por devolver' }, { status: 'RETURNED', label: 'Devuelto' }, { status: 'RECEIVED', label: 'Entrada confirmada' }];
  const next: Record<string, string> = { REQUESTED: 'PICKING', PICKING: 'READY', READY: 'DELIVERED', DELIVERED: 'RETURN_REQUESTED', RETURN_REQUESTED: 'RETURNED', RETURNED: 'RECEIVED' };
  async function advance(item: WarehouseRequest) { if (!item.part.request_id || !next[item.part.status]) return; const location = window.prompt('Ubicacion fisica:', item.part.location || 'A-01-01'); if (location) await onStatus(item.workOrder, item.part.request_id, next[item.part.status], location, `Cambio de ${item.part.status} a ${next[item.part.status]}`); }
  async function document(workOrder: WorkOrderCard, kind: string) { const blob = await getAdminDocument(token, `/api/v1/operations/finance/work-orders/${workOrder.id}/warehouse-documents/${kind}.pdf`); const url = URL.createObjectURL(blob); window.open(url, '_blank', 'noopener,noreferrer'); window.setTimeout(() => URL.revokeObjectURL(url), 60_000); }
  return <div className="role-view"><header className="content-header"><div><span>Bodega por OT</span><h1>Picking, entrega, devolucion y entrada</h1><p>Cada tarjeta conserva la OT, ubicacion, responsable y documento PDF.</p></div></header><div className="warehouse-kanban">{columns.map((column) => <section key={column.status}><header><h2>{column.label}</h2><b>{requests.filter(({ part }) => part.status === column.status).length}</b></header>{requests.filter(({ part }) => part.status === column.status).map((item) => <article key={item.part.request_id}><small>{item.workOrder.external_reference}</small><h3>{item.part.sku} · {item.part.name}</h3><p>Cantidad {item.part.quantity} · <MapPin /> {item.part.location}</p><div className="warehouse-card-actions"><button onClick={() => void document(item.workOrder, column.status === 'REQUESTED' ? 'picking-ticket' : column.status.includes('RETURN') ? 'return' : column.status === 'RECEIVED' ? 'receipt' : 'delivery')}><FileDown /> PDF</button>{next[column.status] && <button className="role-primary" onClick={() => void advance(item)}>{column.status.includes('RETURN') ? <RotateCcw /> : <PackageCheck />} Avanzar</button>}</div></article>)}</section>)}</div></div>;
}

export function AdminOverview({ summary, operations, staffUser }: { summary: ManagementSummary | null; operations: OperationsOverview; staffUser: StaffUser | null }) {
  const money = (value: string | number) => new Intl.NumberFormat('es-HN', { style: 'currency', currency: summary?.currency || 'HNL' }).format(Number(value));
  const pendingWarehouse = operations.reservations.filter((item) => !['RELEASED', 'CONSUMED'].includes(item.status)).length;
  const pendingApprovals = summary?.approvals_by_status.PENDING ?? 0;
  const routes = [
    { label: 'Personal y accesos', detail: 'Crear usuarios operativos, asignar rol, sucursal y código de acceso.', path: '/tallerv1/personal', icon: UserCog },
    { label: 'Catálogo y precios', detail: 'Costo de compra, factor importación, margen mínimo y ABC/XYZ.', path: '/tallerv1/catalogo', icon: ShoppingCart },
    { label: 'Plantillas de documentos', detail: 'Editar factura, cotización y formatos imprimibles sin tocar código.', path: '/tallerv1/documentos', icon: FileText },
    { label: 'Bodegas y reservas', detail: 'Existencias operativas, picking, devoluciones y trazabilidad por OT.', path: '/tallerv1/bodega', icon: Warehouse },
    { label: 'Configuración SmartDiag', detail: 'Empresa, sucursales, permisos y preferencias del taller.', path: '/tallerv1/configuracion', icon: Wrench },
  ];
  return <div className="role-view"><header className="content-header"><div><span>Administración</span><h1>Control integral SmartDiag504</h1><p>Una sola capa visual para operar; ERPNext trabaja al fondo como motor de inventario, finanzas, compras y RR. HH.</p></div><span className="erp-engine-status"><ShieldCheck /> Motor ERP interno</span></header>
    <div className="admin-kpis"><article><BadgeDollarSign /><span>Venta neta real<strong>{summary ? money(summary.net_sales) : 'Cargando…'}</strong></span></article><article><BarChart3 /><span>Ganancia bruta<strong>{summary ? money(summary.gross_profit) : 'Cargando…'}</strong></span></article><article><Box /><span>Movimientos ERP pendientes<strong>{summary?.erp_pending ?? '—'}</strong></span></article><article><ShieldCheck /><span>Autorizaciones pendientes<strong>{pendingApprovals}</strong></span></article></div>
    <section className="role-panel erp-boundary"><header><div><h2>Una interfaz; dos responsabilidades</h2><p>Ni el técnico ni la cajera necesitan entrar al escritorio estándar del ERP.</p></div></header><div><article><Wrench /><span><strong>Vistas SmartDiag por rol</strong><small>Diagnóstico, fotos, repuestos, cotización, cobro, picking, compras, personal y reportes se presentan en español y según permisos.</small></span></article><ArrowRight /><article><ShieldCheck /><span><strong>API de integración</strong><small>Valida contratos, permisos e idempotencia. Los errores quedan pendientes para reintento y nunca se muestran claves ni detalles internos.</small></span></article><ArrowRight /><article><BadgeDollarSign /><span><strong>ERPNext al fondo</strong><small>Conserva artículos, costos, bodegas, facturas, pagos, compras, empleados y libros; su frontend queda reservado a soporte técnico.</small></span></article></div></section>
    <section className="admin-directory"><header><div><h2>Administrar el taller</h2><p>Sesión actual: {staffUser?.full_name ?? 'Administrador'} · {staffUser?.role ?? 'MANAGER'}</p></div><span>{pendingWarehouse} reservas activas de bodega</span></header><div>{routes.map(({ label, detail, path, icon: Icon }) => <a key={path} href={path}><Icon /><span><strong>{label}</strong><small>{detail}</small><code>{path}</code></span><ArrowRight /></a>)}</div></section>
    <section className="role-panel inventory-policy"><header><div><h2>Política de compra y precio</h2><p>El piso incluye costo de compra × factor de importación y margen mínimo. Ninguna venta o descuento puede quedar debajo.</p></div><b>ABC = valor · XYZ = variabilidad</b></header><div className="inventory-policy-table"><span className="inventory-policy-head">Producto</span><span className="inventory-policy-head">Clase</span><span className="inventory-policy-head">Piso / sugerido</span><span className="inventory-policy-head">Recomendación</span>{(summary?.inventory_policy ?? []).slice(0, 12).map((item) => <article key={item.product_id}><span><strong>{item.name}</strong><small>{item.sku} · Stock {item.stock_qty}</small></span><b>{item.abc_class}{item.xyz_class}</b><span><strong>{money(item.minimum_sale_price)}</strong><small>Sugerido {money(item.suggested_sale_price)}</small></span><small>{item.recommendation}</small></article>)}</div>{!summary?.inventory_policy.length && <p>No hay suficiente catálogo valorizado para calcular la clasificación.</p>}</section>
    <section className="role-panel accounting-source"><ShieldCheck /><div><h2>Fuente de verdad sin exponer el ERP</h2><p><strong>{summary?.accounting_source ?? 'ERPNext'}</strong> conserva la contabilidad oficial. SmartDiag consulta ese backend y presenta reportes adecuados al negocio; no mantiene un segundo libro contable.</p></div></section>
  </div>;
}

export function MarketingView({ token }: { token: string }) {
  const initialDraft = { title: '', description: '', audience: 'Todos los vehículos', valid_from: '', valid_until: '', price_from: 0, call_to_action: 'Agenda hoy', tv_enabled: true, display_seconds: 12 };
  const [items, setItems] = useState<MarketingCampaign[]>([]);
  const [draft, setDraft] = useState(initialDraft);
  const [error, setError] = useState('');
  useEffect(() => { void getCampaigns(token).then(setItems).catch((cause: Error) => setError(cause.message)); }, [token]);
  async function add(event: React.FormEvent) {
    event.preventDefault();
    try {
      const created = await createCampaign(token, { ...draft, price_from: draft.price_from || undefined });
      setItems((current) => [created, ...current]); setDraft(initialDraft);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo crear la campaña.'); }
  }
  async function upload(item: MarketingCampaign, file?: File) { if (!file) return; try { const updated = await uploadCampaignMedia(token, item.id, file); setItems((current) => current.map((row) => row.id === updated.id ? updated : row)); } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo cargar el archivo.'); } }
  async function publish(item: MarketingCampaign) { try { const updated = await publishCampaign(token, item.id); setItems((current) => current.map((row) => row.id === updated.id ? updated : row)); } catch (cause) { setError(cause instanceof Error ? cause.message : 'No se pudo publicar.'); } }
  return <div className="role-view">
    <header className="content-header"><div><span>Publicidad</span><h1>Campañas y enlaces medibles</h1><p>Cree promociones, cargue imágenes o videos, publique y mida enlaces y contenido de TV.</p></div><a className="role-link" href="/tallerv1/publicida/tv" target="_blank" rel="noreferrer"><Tv /> Abrir pantalla TV</a></header>
    {error && <p className="global-error">{error}</p>}
    <div className="marketing-workspace"><form className="role-panel campaign-create" onSubmit={add}>
      <h2><Plus /> Nueva campaña</h2>
      <label>Título<input required value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} /></label>
      <label>Descripción<textarea required rows={3} value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></label>
      <label>Vehículos o público<input value={draft.audience} onChange={(event) => setDraft({ ...draft, audience: event.target.value })} /></label>
      <div><label>Desde<input type="date" value={draft.valid_from} onChange={(event) => setDraft({ ...draft, valid_from: event.target.value })} /></label><label>Hasta<input type="date" value={draft.valid_until} onChange={(event) => setDraft({ ...draft, valid_until: event.target.value })} /></label></div>
      <label>Precio desde<input type="number" min="0" value={draft.price_from} onChange={(event) => setDraft({ ...draft, price_from: Number(event.target.value) })} /></label>
      <label>Llamado a la acción<input value={draft.call_to_action} onChange={(event) => setDraft({ ...draft, call_to_action: event.target.value })} /></label>
      <div><label><input type="checkbox" checked={draft.tv_enabled} onChange={(event) => setDraft({ ...draft, tv_enabled: event.target.checked })} /> Mostrar en TV</label><label>Segundos<input type="number" min="5" max="120" value={draft.display_seconds} onChange={(event) => setDraft({ ...draft, display_seconds: Number(event.target.value) })} /></label></div>
      <button className="role-primary"><Megaphone /> Crear borrador</button>
    </form><section className="campaign-board">{items.map((item) => <article className="role-panel campaign-card" key={item.id}><div className="campaign-media">{item.media_url ? item.media_type === 'VIDEO' ? <video src={item.media_url} controls /> : <img src={item.media_url} alt={item.title} /> : <span><Image /><Video /><small>Sin archivo</small></span>}</div><div className="campaign-card-body"><header><span><small>{item.status} · {item.tv_enabled ? 'TV activa' : 'Sólo enlace'}</small><h2>{item.title}</h2></span><b><MousePointerClick /> {item.clicks} clics</b></header><p>{item.description}</p><small>{item.audience} · {item.display_seconds}s</small><div className="campaign-link"><Link2 /><code>{window.location.origin}{item.public_path}</code><button aria-label={`Copiar enlace ${item.title}`} onClick={() => void navigator.clipboard.writeText(`${window.location.origin}${item.public_path}`)}><Copy /></button></div><footer><label className="campaign-upload"><Upload /> Cargar imagen o video<input type="file" accept="image/jpeg,image/png,image/webp,video/mp4,video/webm" onChange={(event) => void upload(item, event.target.files?.[0])} /></label><button className={item.status === 'PUBLISHED' ? 'campaign-live' : ''} disabled={item.status === 'PUBLISHED'} onClick={() => void publish(item)}>{item.status === 'PUBLISHED' ? 'Publicada' : 'Publicar'}</button></footer></div></article>)}{!items.length && <div className="disabled-feature"><Megaphone /><h2>Sin campañas</h2><p>Cree la primera campaña con el formulario.</p></div>}</section></div>
  </div>;
}

export function LegacyFlowAnalytics({ cells }: { cells: FlowHeatmapCell[] }) {
  const peak = Math.max(1, ...cells.map((cell) => cell.count));
  const count = (module: string, actions: string[]) => cells.filter((cell) => cell.module === module && actions.includes(cell.action)).reduce((total, cell) => total + cell.count, 0);
  const stages = [
    { label: 'Captación web', module: 'RECEPTION', value: count('RECEPTION', ['BOOKING_CREATED']), icon: CalendarCheck },
    { label: 'Cita del cliente', module: 'CLIENT_PORTAL', value: count('CLIENT_PORTAL', ['APPOINTMENT_CREATED']), icon: CalendarCheck },
    { label: 'Confirmación', module: 'RECEPTION', value: count('RECEPTION', ['BOOKING_CONTACTED', 'BOOKING_CONFIRMED']), icon: CheckCircle2 },
    { label: 'OT y diagnóstico', module: 'WORK_ORDER', value: count('WORK_ORDER', ['WORK_ORDER_CREATED', 'STATUS_CHANGED']), icon: Wrench },
    { label: 'Cotización', module: 'QUOTES', value: count('QUOTES', ['QUOTE_CREATED', 'QUOTE_STATUS']), icon: ClipboardList },
    { label: 'Solicitud repuesto', module: 'TECHNICIAN', value: count('TECHNICIAN', ['PART_REQUESTED']), icon: ClipboardList },
    { label: 'Entrega bodega', module: 'WAREHOUSE', value: count('WAREHOUSE', ['PART_DELIVERED']), icon: PackageCheck },
    { label: 'Cobro', module: 'CASHIER', value: count('CASHIER', ['PAYMENT_RECORDED']), icon: BadgeDollarSign },
  ];
  return <div className="role-view"><header className="content-header"><div><span>Mejora continua</span><h1>Mapa de actividad por flujo</h1><p>Eventos reales guardados en PostgreSQL para detectar pasos frecuentes, abandonos y fricción.</p></div></header>
    <section className="flow-canvas role-panel"><h2>Captación o portal → cita → OT → cotización → repuesto → entrega → cobro</h2><div>{stages.map(({ label, module, value, icon: Icon }, index) => <span className={value ? 'flow-stage flow-stage--active' : 'flow-stage'} key={label}><i><Icon /></i><small>{module}</small><strong>{label}</strong><b>{value} eventos</b>{index < stages.length - 1 && <ArrowRight className="flow-arrow" />}</span>)}</div></section>
    <section className="flow-heatmap role-panel">{cells.length === 0 ? <p>Aún no hay eventos. Envíe una cita desde la landing para iniciar la medición.</p> : cells.map((cell) => <article key={`${cell.module}-${cell.action}`} style={{ '--heat': cell.count / peak } as CSSProperties}><div><strong>{cell.module}</strong><span>{cell.action.replaceAll('_', ' ')}</span></div><b>{cell.count}</b><small>Último: {new Date(cell.last_seen_at).toLocaleString('es-HN')}</small></article>)}</section></div>;
}

export function FlowAnalytics({ cells }: { cells: FlowHeatmapCell[] }) {
  const modules = ['ALL', ...Array.from(new Set(cells.map((cell) => cell.module)))];
  const [module, setModule] = useState('ALL'); const [selected, setSelected] = useState<FlowHeatmapCell | null>(null);
  const visible = module === 'ALL' ? cells : cells.filter((cell) => cell.module === module);
  const peak = Math.max(1, ...visible.map((cell) => cell.count));
  return <div className="role-view"><header className="content-header"><div><span>Mejora continua</span><h1>Mapa operativo de flujos</h1><p>Filtre un modulo y abra cada evento para revisar volumen, ultimo movimiento y punto de friccion.</p></div></header><nav className="flow-filters">{modules.map((item) => <button className={module === item ? 'active' : ''} onClick={() => { setModule(item); setSelected(null); }} key={item}>{item}</button>)}</nav><section className="flow-heatmap role-panel">{visible.map((cell) => <button className={selected === cell ? 'active' : ''} key={`${cell.module}-${cell.action}`} style={{ '--heat': cell.count / peak } as CSSProperties} onClick={() => setSelected(cell)}><div><strong>{cell.module}</strong><span>{cell.action.replaceAll('_', ' ')}</span></div><b>{cell.count}</b><small>Ultimo: {new Date(cell.last_seen_at).toLocaleString('es-HN')}</small></button>)}</section>{selected && <section className="role-panel flow-inspector"><h2>{selected.action.replaceAll('_', ' ')}</h2><p><b>{selected.count}</b> eventos registrados en PostgreSQL para el modulo {selected.module}.</p><p>Use esta frecuencia junto con los tiempos de la OT para decidir si el paso necesita menos campos, otra responsabilidad o automatizacion.</p></section>}</div>;
}

export function SocialHub() {
  const channels = [
    { name: 'Facebook e Instagram', icon: Instagram, required: 'Meta App ID, App Secret, página y token de acceso' },
    { name: 'WhatsApp Business', icon: MessageCircle, required: 'Phone Number ID, Business Account ID y token' },
    { name: 'Asistente del sitio', icon: Bot, required: 'Activo con IA local y RAG; las respuestas públicas permanecen auditadas' },
  ];
  return <div className="role-view"><header className="content-header"><div><span>Atención omnicanal</span><h1>Hub Social e IA</h1><p>Bandeja preparada para atender consultas; el inicio de sesión de clientes se administra por separado.</p></div></header><section className="social-grid">{channels.map(({ name, icon: Icon, required }) => <article className="role-panel" key={name}><Icon /><div><h2>{name}</h2><b>{name === 'Asistente del sitio' ? 'Activo' : 'Configuración pendiente'}</b><p>{required}</p></div></article>)}</section><section className="role-panel social-policy"><ShieldCheck /><div><h2>Acceso sencillo para clientes</h2><p>La opción recomendada es una pantalla de acceso alojada por un proveedor de identidad: correo con código de un solo uso y botones sociales opcionales. SmartDiag504 recibe un identificador único y no administra contraseñas de redes sociales.</p></div></section><section className="role-panel social-policy"><ShieldCheck /><div><h2>Control humano obligatorio</h2><p>La IA puede proponer respuestas con RAG, pero no publica, factura, cobra ni modifica inventario sin permisos explícitos y confirmación de una persona autorizada.</p></div></section></div>;
}

export function MarketingDisplay() {
  const branding = useBranding();
  const [items, setItems] = useState<MarketingCampaign[]>([]);
  const [index, setIndex] = useState(0);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    let active = true;
    const load = () => void getPublicCampaigns().then((campaigns) => { if (active) { setItems(campaigns.filter((item) => item.tv_enabled !== false)); setLoaded(true); } }).catch(() => { if (active) setLoaded(true); });
    load(); const refresh = window.setInterval(load, 60_000);
    return () => { active = false; window.clearInterval(refresh); };
  }, []);
  useEffect(() => {
    if (items.length < 2) return;
    const delay = Math.max(5, items[index]?.display_seconds || 12) * 1000;
    const timer = window.setTimeout(() => setIndex((current) => (current + 1) % items.length), delay);
    return () => window.clearTimeout(timer);
  }, [index, items]);
  const item = items[index % Math.max(1, items.length)];
  if (!item) return <main className="marketing-tv marketing-tv--empty"><img src={branding.logo_dark_url || branding.logo_url} alt={branding.display_name} /><div><p>{loaded ? 'Pantalla conectada' : 'Cargando campañas'}</p><h1>{branding.display_name}</h1><h2>{loaded ? 'No hay promociones publicadas para TV' : 'Preparando contenido'}</h2><span>Publique una campaña con imagen o video desde el módulo Publicidad.</span></div></main>;
  return <main className="marketing-tv marketing-tv--campaign" data-campaign={item.id}>
    <div className="marketing-tv__media">{item.media_url ? item.media_type === 'VIDEO' ? <video key={item.id} src={item.media_url} autoPlay muted loop playsInline /> : <img src={item.media_url} alt={item.title} /> : <span><Megaphone /></span>}</div>
    <div className="marketing-tv__content"><img className="marketing-tv__logo" src={branding.logo_dark_url || branding.logo_url} alt={branding.display_name} /><p>{item.audience}</p><h1>{item.title}</h1><h2>{item.description}</h2><span>{item.call_to_action || 'Agenda hoy'} · {branding.website.replace(/^https?:\/\//, '')}</span></div>
    {item.price_from ? <strong>Desde L {Number(item.price_from).toLocaleString('es-HN')}</strong> : <strong>Consulte hoy</strong>}
    <nav aria-label="Campañas activas">{items.map((campaign, position) => <i className={position === index ? 'active' : ''} key={campaign.id} />)}</nav>
  </main>;
}
