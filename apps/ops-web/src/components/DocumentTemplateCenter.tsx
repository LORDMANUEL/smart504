import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Download, Eye, FileClock, FilePlus2, History, Printer, Save, Upload } from 'lucide-react';
import {
  createDocumentTemplate,
  createDocumentTemplateVersion,
  exportDocumentTemplate,
  getDocumentRenders,
  getDocumentTemplates,
  getOperationsOverview,
  importDocumentTemplateFiles,
  previewDocumentTemplate,
  publishDocumentTemplate,
  type DocumentTemplateDraft,
} from '../lib/api';
import type { Branch, DocumentRender, DocumentTemplate } from '../types';

const DEFAULT_HTML = `<header><img class="company-logo" src="{{ company.logo_data_uri }}" alt=""><h1>{{ company.name }}</h1><h2>{{ document.title }} {{ document.number }}</h2></header>
<section class="meta"><b>Cliente:</b> {{ customer.name }}<br><b>Vehiculo:</b> {{ vehicle.label }}<br><b>OT:</b> {{ work_order.number }}</section>
<table><thead><tr><th>Codigo</th><th>Descripcion</th><th>Cant.</th><th>Total</th></tr></thead><tbody>{{ quote.rows_html }}</tbody></table>
<section class="totals"><b>Total</b><strong>{{ quote.total }}</strong></section>
<footer>{{ document.notes }}</footer>`;
const DEFAULT_CSS = `body{font-family:Helvetica,Arial,sans-serif;color:#17181c;font-size:10pt}.company-logo{max-width:180px;max-height:72px;object-fit:contain}header{border-bottom:3px solid {{ company.primary_color }};padding-bottom:12px}h1{margin:0}h2{color:{{ company.primary_color }}}.meta{margin:18px 0;line-height:1.7}table{width:100%;border-collapse:collapse}th{background:#17181c;color:white;padding:8px;text-align:left}td{padding:8px;border-bottom:1px solid #ddd}.totals{display:flex;justify-content:flex-end;gap:24px;margin-top:20px;font-size:14pt}footer{margin-top:32px;color:#666}`;
const TYPES = ['QUOTE','INVOICE','DIAGNOSIS','WORK_ORDER','WARRANTY','EXIT_PASS','PICKING_TICKET','WAREHOUSE_DELIVERY','WAREHOUSE_RETURN','WAREHOUSE_RECEIPT','PAYSLIP'];
const VARIABLES = ['company.name','company.legal_name','company.tax_id','company.address','company.phone','company.email','company.website','company.logo_url','company.logo_data_uri','company.primary_color','company.accent_color','company.document_footer','document.number','document.date','document.title','customer.name','vehicle.label','vehicle.vin','work_order.number','work_order.status','work_order.diagnosis','quote.rows_html','quote.subtotal','quote.discount','quote.tax','quote.total','evidence.rows_html','warehouse.rows_html','document.notes'];

const DEFAULT_PRINT_PROFILE = { printer_type: 'BROWSER_PDF' as const, orientation: 'PORTRAIT' as const, margins_mm: { top: 10, right: 10, bottom: 10, left: 10 }, copies: 1, show_logo: true, preprinted_background: false };
const initialDraft: DocumentTemplateDraft = { code: '', name: '', document_type: 'QUOTE', paper_size: 'LETTER', print_profile: DEFAULT_PRINT_PROFILE, html_template: DEFAULT_HTML, css_text: DEFAULT_CSS, change_note: 'Formato inicial de la empresa', created_by: 'administrador' };

export function DocumentTemplateCenter({ token }: { token: string }) {
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [renders, setRenders] = useState<DocumentRender[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [draft, setDraft] = useState<DocumentTemplateDraft>(initialDraft);
  const [preview, setPreview] = useState('');
  const [branches, setBranches] = useState<Branch[]>([]);
  const [htmlFile, setHtmlFile] = useState<File | null>(null);
  const [cssFile, setCssFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const selected = useMemo(() => templates.find((item) => item.id === selectedId), [templates, selectedId]);

  async function reload() {
    const [nextTemplates, nextRenders, operations] = await Promise.all([getDocumentTemplates(token), getDocumentRenders(token), getOperationsOverview(token)]);
    setTemplates(nextTemplates); setRenders(nextRenders); setBranches(operations.branches);
  }
  useEffect(() => { void reload().catch((error: Error) => setMessage(error.message)); }, [token]);

  function choose(item: DocumentTemplate) {
    const version = item.versions[0];
    setSelectedId(item.id);
    setDraft({ code: item.code, name: item.name, document_type: item.document_type, branch_id: item.branch_id,
      paper_size: version?.paper_size ?? 'LETTER', html_template: version?.html_template ?? DEFAULT_HTML,
      print_profile: version?.print_profile_json ?? DEFAULT_PRINT_PROFILE,
      css_text: version?.css_text ?? DEFAULT_CSS, change_note: `Actualizacion de ${item.name}`, created_by: 'administrador' });
    setPreview(''); setMessage('');
  }
  function newTemplate() { setSelectedId(''); setDraft({ ...initialDraft }); setPreview(''); setMessage(''); }
  async function run(action: () => Promise<void>) { setBusy(true); setMessage(''); try { await action(); } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo completar la accion'); } finally { setBusy(false); } }
  async function save() { await run(async () => { if (selected) { await createDocumentTemplateVersion(token, selected.id, { paper_size: draft.paper_size, print_profile: draft.print_profile, html_template: draft.html_template, css_text: draft.css_text, change_note: draft.change_note, created_by: draft.created_by }); setMessage('Nueva version guardada. Publiquela cuando termine la revision.'); } else { const created = await createDocumentTemplate(token, draft); setSelectedId(created.id); setMessage('Plantilla creada como borrador.'); } await reload(); }); }
  async function showPreview() { await run(async () => setPreview(await previewDocumentTemplate(token, draft))); }
  async function publish() { if (!selected) return; await run(async () => { const newest = Math.max(selected.current_version, ...selected.versions.map((item) => item.version)); await publishDocumentTemplate(token, selected.id, newest); await reload(); setMessage(`Version ${newest} publicada. Los documentos anteriores conservan su formato.`); }); }
  async function uploadFiles() { if (!htmlFile) return; await run(async () => { const imported = await importDocumentTemplateFiles(token, draft, htmlFile, cssFile ?? undefined, selected?.id); setSelectedId(imported.id); setHtmlFile(null); setCssFile(null); await reload(); setMessage(selected ? 'Formato reemplazado como nueva versión en borrador.' : 'Formato cargado como plantilla nueva.'); }); }

  return <div className="document-center">
    <header className="content-header"><div><span>Administración documental</span><h1>Centro único de formatos e impresión</h1><p>Cada empresa administra aquí cotizaciones, facturas, diagnósticos, OT, tickets y documentos de bodega. Reemplazar crea una versión; nunca altera documentos ya emitidos.</p></div><button className="role-link" onClick={newTemplate}><FilePlus2 /> Nueva plantilla</button></header>
    {message && <p className="document-message">{message}</p>}
    <div className="document-layout">
      <aside className="role-panel document-list"><header><h2>Plantillas</h2><b>{templates.length}</b></header>{templates.map((item) => <button className={selectedId === item.id ? 'active' : ''} key={item.id} onClick={() => choose(item)}><span><strong>{item.name}</strong><small>{item.document_type} · {item.code}</small></span><em>{item.published_version ? `v${item.published_version} publicada` : 'Borrador'}</em></button>)}{templates.length === 0 && <p>No hay plantillas. Cree la primera.</p>}</aside>
      <section className="role-panel document-editor">
        <div className="document-fields"><label>Código<input disabled={Boolean(selected)} value={draft.code} onChange={(event) => setDraft({ ...draft, code: event.target.value.toUpperCase().replace(/[^A-Z0-9_-]/g, '') })} /></label><label>Nombre<input disabled={Boolean(selected)} value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></label><label>Tipo<select disabled={Boolean(selected)} value={draft.document_type} onChange={(event) => setDraft({ ...draft, document_type: event.target.value })}>{TYPES.map((type) => <option key={type}>{type}</option>)}</select></label><label>Alcance<select disabled={Boolean(selected)} value={draft.branch_id ?? ''} onChange={(event) => setDraft({ ...draft, branch_id: event.target.value || null })}><option value="">Toda la empresa</option>{branches.map((branch) => <option value={branch.id} key={branch.id}>Sucursal: {branch.name}</option>)}</select></label></div>
        <fieldset className="print-profile"><legend><Printer /> Asistente de impresión</legend><p>¿Cómo imprimirá este documento? La configuración queda versionada junto al HTML y CSS.</p><div className="document-fields"><label>Salida<select value={draft.print_profile.printer_type} onChange={(event) => { const printer_type = event.target.value as typeof draft.print_profile.printer_type; const thermal = printer_type === 'THERMAL'; setDraft({ ...draft, paper_size: thermal ? 'THERMAL_80' : draft.paper_size.startsWith('THERMAL') ? 'LETTER' : draft.paper_size, print_profile: { ...draft.print_profile, printer_type } }); }}><option value="BROWSER_PDF">PDF / navegador</option><option value="LASER_INKJET">Impresora normal</option><option value="THERMAL">Térmica POS</option><option value="PREPRINTED">Hoja preimpresa</option></select></label><label>Papel<select value={draft.paper_size} onChange={(event) => setDraft({ ...draft, paper_size: event.target.value })}><option>LETTER</option><option>A4</option><option>THERMAL_80</option><option>THERMAL_58</option></select></label><label>Orientación<select value={draft.print_profile.orientation} onChange={(event) => setDraft({ ...draft, print_profile: { ...draft.print_profile, orientation: event.target.value as 'PORTRAIT' | 'LANDSCAPE' } })}><option value="PORTRAIT">Vertical</option><option value="LANDSCAPE">Horizontal</option></select></label><label>Copias<input type="number" min="1" max="5" value={draft.print_profile.copies} onChange={(event) => setDraft({ ...draft, print_profile: { ...draft.print_profile, copies: Number(event.target.value) } })} /></label></div><div className="print-margins">{(['top','right','bottom','left'] as const).map((side) => <label key={side}>Margen {side}<input type="number" min="0" max="50" step="0.5" value={draft.print_profile.margins_mm[side]} onChange={(event) => setDraft({ ...draft, print_profile: { ...draft.print_profile, margins_mm: { ...draft.print_profile.margins_mm, [side]: Number(event.target.value) } } })} /></label>)}</div><label className="enterprise-check"><input type="checkbox" checked={draft.print_profile.show_logo} onChange={(event) => setDraft({ ...draft, print_profile: { ...draft.print_profile, show_logo: event.target.checked } })} /> Mostrar logotipo</label><label className="enterprise-check"><input type="checkbox" checked={draft.print_profile.preprinted_background} onChange={(event) => setDraft({ ...draft, print_profile: { ...draft.print_profile, preprinted_background: event.target.checked } })} /> El papel ya trae membrete o formato preimpreso</label></fieldset>
        <section className="document-upload"><div><Upload /><span><strong>{selected ? 'Reemplazar formato' : 'Subir formato nuevo'}</strong><small>HTML UTF-8 obligatorio y CSS opcional. Se valida y guarda como borrador.</small></span></div><label>Archivo HTML<input type="file" accept=".html,.htm,text/html" onChange={(event) => setHtmlFile(event.target.files?.[0] ?? null)} /></label><label>Archivo CSS<input type="file" accept=".css,text/css" onChange={(event) => setCssFile(event.target.files?.[0] ?? null)} /></label><button disabled={busy || !htmlFile || !draft.code || !draft.name} onClick={() => void uploadFiles()}><Upload /> {selected ? 'Crear versión desde archivos' : 'Cargar plantilla'}</button></section>
        <label className="document-code">HTML seguro<textarea rows={15} value={draft.html_template} onChange={(event) => setDraft({ ...draft, html_template: event.target.value })} /></label>
        <label className="document-code">CSS de impresion<textarea rows={8} value={draft.css_text} onChange={(event) => setDraft({ ...draft, css_text: event.target.value })} /></label>
        <label>Nota de version<input value={draft.change_note} onChange={(event) => setDraft({ ...draft, change_note: event.target.value })} /></label>
        <div className="document-actions"><button disabled={busy || !draft.code || !draft.name} onClick={() => void save()}><Save /> {selected ? 'Guardar nueva versión' : 'Crear borrador'}</button><button disabled={busy} onClick={() => void showPreview()}><Eye /> Vista previa</button><button disabled={!preview} onClick={() => window.print()}><Printer /> Prueba de impresión</button><button disabled={busy || !selected} className="publish" onClick={() => void publish()}><CheckCircle2 /> Publicar última versión</button><button disabled={busy || !selected} onClick={() => selected && void exportDocumentTemplate(token, selected.id, selected.code)}><Download /> Descargar respaldo</button></div>
      </section>
      <aside className="role-panel variable-catalog"><h2>Variables permitidas</h2><p>Haga clic para copiar. Los scripts y recursos externos estan bloqueados.</p><div>{VARIABLES.map((variable) => <button key={variable} onClick={() => void navigator.clipboard.writeText(`{{ ${variable} }}`)}>{`{{ ${variable} }}`}</button>)}</div></aside>
    </div>
    {preview && <section className="role-panel document-preview"><header><h2><Eye /> Vista previa con datos de ejemplo</h2><button onClick={() => setPreview('')}>Cerrar</button></header><iframe title="Vista previa del documento" srcDoc={preview} sandbox="" /></section>}
    <section className="role-panel render-history"><header><h2><History /> Historial de documentos emitidos</h2><b>{renders.length}</b></header>{renders.slice(0, 30).map((item) => <article key={item.id}><FileClock /><span><strong>{item.business_reference}</strong><small>{item.document_type} · {new Date(item.created_at).toLocaleString('es-HN')}</small></span><code>{item.content_sha256.slice(0, 16)}…</code></article>)}{renders.length === 0 && <p>El historial aparecera cuando se genere el primer PDF.</p>}</section>
  </div>;
}
