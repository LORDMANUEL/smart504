import { useEffect, useMemo, useState } from 'react';
import { BookOpen, Box, Calculator, Camera, CarFront, Clock3, FileClock, PackagePlus, Printer, Search, Upload, UserRound, Wrench, X } from 'lucide-react';
import { getAdminDocument, getLaborCatalog, getStaffTechnicians, getWorkOrderEvidence, getWorkOrderLabor, recordWorkOrderLabor, registerWorkOrderCheckIn, registerWorkOrderQuality, updateWorkOrderTimer, uploadWorkOrderEvidence, type WorkOrderEvidence } from '../lib/api';
import type { LaborCatalogItem, Product, StaffTechnician, WorkOrderCard, WorkOrderLaborEntry } from '../types';

type Tab = 'summary' | 'reception' | 'time' | 'labor' | 'evidence' | 'parts' | 'quality' | 'history' | 'manuals';

export function WorkOrderDetail({
  workOrder,
  token,
  products,
  busy,
  onClose,
  onRequestPart,
}: {
  workOrder: WorkOrderCard;
  token: string;
  products: Product[];
  busy: boolean;
  onClose: () => void;
  onRequestPart: (product: Product, quantity: number, note: string) => Promise<void>;
}) {
  const [tab, setTab] = useState<Tab>('summary');
  const [query, setQuery] = useState('');
  const [note, setNote] = useState('Validar compatibilidad por VIN antes de entregar.');
  const [evidence, setEvidence] = useState<WorkOrderEvidence[]>([]);
  const [caption, setCaption] = useState('');
  const [evidenceError, setEvidenceError] = useState('');
  const [technicians, setTechnicians] = useState<StaffTechnician[]>([]);
  const [labor, setLabor] = useState<WorkOrderLaborEntry[]>([]);
  const [laborCatalog, setLaborCatalog] = useState<LaborCatalogItem[]>([]);
  const [laborError, setLaborError] = useState('');
  const [laborDraft, setLaborDraft] = useState({ technician_id: '', service_code: '', rate_kind: 'STANDARD' as 'STANDARD' | 'SPECIALIZED' });
  const [events, setEvents] = useState(workOrder.events ?? []);
  const [operationMessage, setOperationMessage] = useState('');
  const [timerState, setTimerState] = useState<'STOPPED' | 'START' | 'PAUSE' | 'RESUME'>(() => { const last = [...(workOrder.events ?? [])].reverse().find((item) => item.event_type.startsWith('WORK_TIMER_')); return (last?.event_type.replace('WORK_TIMER_', '') as 'START' | 'PAUSE' | 'RESUME' | 'STOPPED') ?? 'STOPPED'; });
  useEffect(() => { void getWorkOrderEvidence(token, workOrder.id).then(setEvidence).catch((error: Error) => setEvidenceError(error.message)); }, [token, workOrder.id]);
  useEffect(() => { void Promise.all([getStaffTechnicians(token), getWorkOrderLabor(token, workOrder.id), getLaborCatalog(token)]).then(([staff, entries, catalog]) => { setTechnicians(staff); setLabor(entries); setLaborCatalog(catalog); }).catch((error: Error) => setLaborError(error.message)); }, [token, workOrder.id]);
  async function addEvidence(file?: File) {
    if (!file || caption.trim().length < 3) { setEvidenceError('Escriba una descripcion de la pieza o hallazgo.'); return; }
    try { const created = await uploadWorkOrderEvidence(token, workOrder.id, file, caption.trim()); setEvidence((items) => [...items, created]); setCaption(''); setEvidenceError(''); }
    catch (error) { setEvidenceError(error instanceof Error ? error.message : 'No se pudo cargar la foto.'); }
  }
  async function printDiagnosis() {
    const blob = await getAdminDocument(token, `/api/v1/operations/finance/work-orders/${workOrder.id}/documents/diagnosis.pdf`);
    const url = URL.createObjectURL(blob); window.open(url, '_blank', 'noopener,noreferrer'); window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }
  async function addLabor(event: React.FormEvent) {
    event.preventDefault(); setLaborError('');
    try {
      const created = await recordWorkOrderLabor(token, workOrder.id, { ...laborDraft, actor: 'tecnico-operaciones' });
      setLabor((items) => [...items, created]);
      setLaborDraft((current) => ({ ...current, service_code: '' }));
    } catch (error) { setLaborError(error instanceof Error ? error.message : 'No se pudo registrar la mano de obra.'); }
  }
  async function applyOperation(action: () => Promise<WorkOrderCard>, message: string) { try { const updated = await action(); setEvents(updated.events ?? []); setOperationMessage(message); } catch (error) { setOperationMessage(error instanceof Error ? error.message : 'No se pudo guardar la operación.'); } }
  async function saveCheckIn(event: React.FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); await applyOperation(() => registerWorkOrderCheckIn(token, workOrder.id, { mileage_km: Number(form.get('mileage_km')), fuel_percent: Number(form.get('fuel_percent')), accessories: String(form.get('accessories') || '').split(',').map((item) => item.trim()).filter(Boolean), exterior_notes: String(form.get('exterior_notes') || ''), customer_name: String(form.get('customer_name') || ''), customer_accepted: form.get('customer_accepted') === 'on' }), 'Ingreso 360 guardado y firmado.'); }
  async function timer(action: 'START' | 'PAUSE' | 'RESUME' | 'STOP') { await applyOperation(() => updateWorkOrderTimer(token, workOrder.id, action, 'Registro desde la OT'), `Cronómetro: ${action}.`); setTimerState(action === 'STOP' ? 'STOPPED' : action); }
  async function saveQuality(event: React.FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); const result = String(form.get('result')) as 'PASS' | 'FAIL'; await applyOperation(() => registerWorkOrderQuality(token, workOrder.id, { checklist: { niveles: form.get('niveles') === 'on', frenos: form.get('frenos') === 'on', luces: form.get('luces') === 'on', limpieza: form.get('limpieza') === 'on' }, road_test_required: form.get('road_test_required') === 'on', road_test_result: String(form.get('road_test_result')) as 'NOT_REQUIRED' | 'PASS' | 'FAIL', notes: String(form.get('notes') || ''), result }), `Control de calidad: ${result}.`); }
  const compatibleProducts = useMemo(() => {
    const normalize = (value: string) => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/f[\s-]?150/g, 'f150').replace(/[^a-z0-9]+/g, ' ');
    const fitments = [
      ['ford', 'escape', '2020'],
      ['ford', 'f150', '2020'],
      ['honda', 'civic', '2008'],
    ];
    const vehicleText = normalize(workOrder.vehicle_label);
    const vehicleFitment = fitments.find((tokens) => tokens.every((token) => vehicleText.includes(token)));
    return products.filter((product) => {
      const productText = normalize(`${product.sku} ${product.name} ${product.compatibility_note ?? ''}`);
      const explicitFitment = fitments.find((tokens) => tokens.every((token) => productText.includes(token)));
      return !explicitFitment || !vehicleFitment || explicitFitment === vehicleFitment;
    });
  }, [products, workOrder.vehicle_label]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return compatibleProducts.slice(0, 12);
    return compatibleProducts.filter((product) => `${product.sku} ${product.name} ${product.compatibility_note ?? ''}`.toLowerCase().includes(normalized)).slice(0, 20);
  }, [compatibleProducts, query]);
  const vehicleQuery = encodeURIComponent(workOrder.vehicle_label);
  const tabs: Array<[Tab, string]> = [['summary', 'Resumen'], ['reception', 'Ingreso 360'], ['time', 'Cronómetro'], ['labor', `Mano de obra (${labor.length})`], ['evidence', `Fotos (${evidence.length})`], ['parts', 'Repuestos'], ['quality', 'Calidad'], ['history', 'Historial'], ['manuals', 'Manuales']];

  return <div className="ot-detail-backdrop" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) onClose(); }}>
    <section className="ot-detail" role="dialog" aria-modal="true" aria-label={`Detalle de OT ${workOrder.external_reference}`}>
      <header className="ot-detail__header"><div><small>ORDEN DE TRABAJO</small><h1>{workOrder.external_reference} · {workOrder.vehicle_label}</h1><p>{workOrder.title}</p></div><button aria-label="Cerrar detalle" onClick={onClose}><X /></button></header>
      <nav className="ot-detail__tabs" role="tablist">{tabs.map(([id, label]) => <button role="tab" aria-selected={tab === id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)} key={id}>{label}</button>)}</nav>
      <div className="ot-detail__body">
        {operationMessage && <p role="status" className="operation-message">{operationMessage}</p>}
        {tab === 'summary' && <div className="ot-summary-grid">
          <article><CarFront /><span><small>Vehículo</small><strong>{workOrder.vehicle_label}</strong></span></article>
          <article><UserRound /><span><small>Cliente</small><strong>{workOrder.customer_name}</strong></span></article>
          <article><Wrench /><span><small>Técnico</small><strong>{workOrder.technician_name ?? 'Sin asignar'}</strong></span></article>
          <article><Clock3 /><span><small>Estado</small><strong>{workOrder.status.replaceAll('_', ' ')}</strong></span></article>
          <section className="ot-narrative"><h2>Motivo de ingreso</h2><p>{workOrder.concern ?? workOrder.title}</p><h2>Diagnóstico</h2><p>{workOrder.diagnosis ?? 'Pendiente de documentar por el técnico.'}</p></section>
        </div>}
        {tab === 'reception' && <form className="ot-labor" onSubmit={saveCheckIn}><header><CarFront /><div><h2>Ingreso 360 y aceptación</h2><p>Registre kilometraje, combustible, accesorios y daños previos; agregue las fotos en Evidencia.</p></div></header><label>Kilometraje<input required name="mileage_km" type="number" min="0" defaultValue="0" /></label><label>Combustible %<input required name="fuel_percent" type="number" min="0" max="100" defaultValue="50" /></label><label>Accesorios entregados<input name="accessories" placeholder="Llave, documentos, llanta de repuesto" /></label><label>Estado exterior<textarea name="exterior_notes" rows={3} /></label><label>Nombre del cliente<input required name="customer_name" defaultValue={workOrder.customer_name} /></label><label className="check-setting"><input required name="customer_accepted" type="checkbox" /> El cliente confirma el estado registrado y autoriza el ingreso.</label><button className="role-primary">Guardar ingreso firmado</button></form>}
        {tab === 'time' && <section className="ot-labor"><header><Clock3 /><div><h2>Tiempo real de la OT</h2><p>Las pausas no suman tiempo productivo; detener cierra el bloque auditable.</p></div></header><div className="warehouse-card-actions"><button disabled={timerState !== 'STOPPED'} onClick={() => void timer('START')}>Iniciar</button><button disabled={!['START','RESUME'].includes(timerState)} onClick={() => void timer('PAUSE')}>Pausar</button><button disabled={timerState !== 'PAUSE'} onClick={() => void timer('RESUME')}>Continuar</button><button disabled={timerState === 'STOPPED'} onClick={() => void timer('STOP')}>Detener</button></div><div className="labor-register">{events.filter((item) => item.event_type.startsWith('WORK_TIMER_')).map((item) => <article key={item.id}><span><strong>{item.event_type.replace('WORK_TIMER_', '')}</strong><small>{item.actor} · {new Date(item.created_at).toLocaleString('es-HN')}</small></span></article>)}</div></section>}
        {tab === 'labor' && <section className="ot-labor"><header><Calculator /><div><h2>Seleccionar mano de obra del catálogo</h2><p>El técnico sólo selecciona servicios aprobados; descripción y duración vienen protegidas desde el catálogo.</p></div></header>{laborError && <p className="global-error">{laborError}</p>}<form onSubmit={addLabor}><label>Técnico<select required value={laborDraft.technician_id} onChange={(event) => setLaborDraft({ ...laborDraft, technician_id: event.target.value })}><option value="">Seleccione</option>{technicians.map((item) => <option value={item.id} key={item.id}>{item.employee_code} · {item.full_name}</option>)}</select></label><label>Servicio del catálogo<select required value={laborDraft.service_code} onChange={(event) => setLaborDraft({ ...laborDraft, service_code: event.target.value })}><option value="">Seleccione mano de obra</option>{laborCatalog.map((item) => <option value={item.code} key={item.code}>{item.code} · {item.description} · {item.hours} h</option>)}</select></label><label>Tipo de hora<select value={laborDraft.rate_kind} onChange={(event) => setLaborDraft({ ...laborDraft, rate_kind: event.target.value as 'STANDARD' | 'SPECIALIZED' })}><option value="STANDARD">Hora normal</option><option value="SPECIALIZED">Hora especializada</option></select></label><button className="role-primary" disabled={busy}><Clock3 /> Agregar a la cotización técnica</button></form><div className="labor-register">{labor.map((entry) => <article key={entry.id}><span><strong>{entry.service_code} · {entry.description}</strong><small>{entry.technician_name} · {entry.rate_kind === 'SPECIALIZED' ? 'Especializada' : 'Normal'} · {entry.hours} h</small></span><b>L {Number(entry.sale_total).toFixed(2)}</b></article>)}{!labor.length && <p className="muted-copy">Todavía no hay mano de obra cotizada en esta OT.</p>}</div></section>}
        {tab === 'evidence' && <section className="ot-evidence"><header><div><Camera /><span><h2>Evidencia del diagnostico</h2><p>Fotografias de piezas, danos, antes/despues y control de calidad.</p></span></div><button className="role-primary" onClick={() => void printDiagnosis()}><Printer /> Imprimir diagnostico</button></header>{evidenceError && <p className="global-error">{evidenceError}</p>}<div className="evidence-upload"><label>Descripcion visible en el informe<input value={caption} onChange={(event) => setCaption(event.target.value)} placeholder="Ej. Pastilla delantera derecha con desgaste irregular" /></label><label className="campaign-upload"><Upload /> Tomar o cargar foto<input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={(event) => void addEvidence(event.target.files?.[0])} /></label></div><div className="evidence-grid">{evidence.map((item) => <article key={item.id}><img src={item.media_url} alt={item.caption} /><div><b>{item.caption}</b><small>{item.category} · {item.actor} · {new Date(item.created_at).toLocaleString('es-HN')}</small></div></article>)}{!evidence.length && <p className="muted-copy">Todavia no hay fotografias en esta OT.</p>}</div></section>}
        {tab === 'parts' && <div className="ot-parts-layout">
          <section><h2>Repuestos solicitados</h2><div className="requested-parts">{(workOrder.parts_required ?? []).map((part, index) => <article key={`${part.sku}-${index}`}><Box /><div><strong>{part.quantity ?? part.qty ?? 1} × {part.name || part.sku}</strong><small>{part.sku} · {part.status || 'Registro histórico'} · {part.location || 'Ubicación no registrada'}</small>{part.note && <p>{part.note}</p>}</div></article>)}{!(workOrder.parts_required ?? []).length && <p className="muted-copy">Aún no se han solicitado repuestos para esta OT.</p>}</div></section>
          <section className="part-request"><h2>Solicitar desde catálogo</h2><label><Search /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar código, nombre o vehículo" /></label><textarea value={note} onChange={(event) => setNote(event.target.value)} rows={2} aria-label="Nota para bodega" />
            <div className="part-search-results">{filtered.map((product) => <article key={product.id}><div><code>{product.sku}</code><strong>{product.name}</strong><small>{product.compatibility_note ?? 'Validar por VIN'} · Existencia {product.stock_qty}</small></div><button disabled={busy} onClick={() => void onRequestPart(product, 1, note)}><PackagePlus /> Pedir</button></article>)}</div>
          </section>
        </div>}
        {tab === 'quality' && <form className="ot-labor" onSubmit={saveQuality}><header><Wrench /><div><h2>Control de calidad obligatorio</h2><p>Debe aprobarlo supervisión antes de pasar la OT a facturación.</p></div></header>{['niveles','frenos','luces','limpieza'].map((item) => <label className="check-setting" key={item}><input name={item} type="checkbox" /> {item}</label>)}<label className="check-setting"><input name="road_test_required" type="checkbox" /> Requiere prueba de ruta</label><label>Resultado prueba de ruta<select name="road_test_result"><option value="NOT_REQUIRED">No aplica</option><option value="PASS">Aprobada</option><option value="FAIL">Fallida</option></select></label><label>Resultado final<select name="result"><option value="PASS">Aprobado</option><option value="FAIL">Rechazado</option></select></label><label>Observaciones<textarea name="notes" rows={3} /></label><button className="role-primary">Firmar control de calidad</button></form>}
        {tab === 'history' && <section className="ot-history"><h2>Historial auditable</h2>{events.map((event) => <article key={event.id}><FileClock /><div><strong>{event.event_type.replaceAll('_', ' ')}</strong><p>{event.reason}</p><small>{event.actor} · {new Date(event.created_at).toLocaleString('es-HN')}</small></div></article>)}</section>}
        {tab === 'manuals' && <section className="manual-search"><BookOpen /><h2>Ayuda técnica y manuales</h2><p>Use la identificación del vehículo como punto de partida. Confirme siempre motor, versión y VIN antes de aplicar un procedimiento.</p><div>
          <a target="_blank" rel="noreferrer" href={`https://www.google.com/search?q=${vehicleQuery}+manual+del+propietario+PDF+fabricante`}>Buscar manual del fabricante</a>
          <a target="_blank" rel="noreferrer" href={`https://www.google.com/search?q=${vehicleQuery}+manual+de+taller+procedimiento+t%C3%A9cnico`}>Buscar procedimiento de taller</a>
          <a target="_blank" rel="noreferrer" href={`https://www.google.com/search?q=${vehicleQuery}+bolet%C3%ADn+t%C3%A9cnico+TSB`}>Buscar boletines técnicos</a>
          <a target="_blank" rel="noreferrer" href="https://www.nhtsa.gov/recalls">Consultar campañas y recalls</a>
        </div><small>Los enlaces abren fuentes externas; SmartDiag504 no copia ni presenta manuales como propios.</small></section>}
      </div>
    </section>
  </div>;
}
