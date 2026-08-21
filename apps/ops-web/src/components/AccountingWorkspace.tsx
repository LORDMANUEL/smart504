import { useMemo, useState } from 'react';
import { BadgeCheck, BookOpen, FileCog, Landmark, Printer, Save, ShieldAlert } from 'lucide-react';
import { createManagementDocument, updateManagementDocumentStatus } from '../lib/api';
import type { ManagementDocument, ManagementSummary, OperationsOverview } from '../types';

type FiscalDraft = {
  branch_id: string; numbering_owner: 'ERPNEXT' | 'PREPRINTED'; legal_name: string; rtn: string;
  cai: string; document_kind: string; series_name: string; prefix: string; range_start: string;
  range_end: string; valid_from: string; valid_until: string; template_code: string; notes: string;
};

const emptyDraft = (branchId = ''): FiscalDraft => ({
  branch_id: branchId, numbering_owner: 'ERPNEXT', legal_name: '', rtn: '', cai: '',
  document_kind: 'FACTURA', series_name: '', prefix: '', range_start: '', range_end: '',
  valid_from: '', valid_until: '', template_code: 'INVOICE_DEFAULT', notes: '',
});

function fiscalMeta(document: ManagementDocument) {
  return document.metadata_json as Record<string, string | number | boolean | undefined>;
}

export function AccountingWorkspace({ token, overview, summary, onReload }: { token: string; overview: OperationsOverview; summary: ManagementSummary | null; onReload: () => Promise<void> }) {
  const [draft, setDraft] = useState<FiscalDraft>(() => emptyDraft(overview.branches[0]?.id));
  const [confirmed, setConfirmed] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const fiscalDocuments = useMemo(() => overview.management_documents.filter((item) => item.document_type === 'FISCAL_CONFIGURATION'), [overview.management_documents]);

  function field<K extends keyof FiscalDraft>(name: K, value: FiscalDraft[K]) { setDraft((current) => ({ ...current, [name]: value })); }
  async function save(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setMessage('');
    try {
      await createManagementDocument(token, {
        branch_id: draft.branch_id,
        document_type: 'FISCAL_CONFIGURATION',
        number: draft.series_name,
        status: 'DRAFT',
        valid_from: draft.valid_from ? `${draft.valid_from}T00:00:00Z` : null,
        valid_until: draft.valid_until ? `${draft.valid_until}T23:59:59Z` : null,
        metadata_json: {
          numbering_owner: draft.numbering_owner,
          legal_name: draft.legal_name.trim(), rtn: draft.rtn.trim(), cai: draft.cai.trim(),
          document_kind: draft.document_kind, prefix: draft.prefix.trim(),
          range_start: draft.numbering_owner === 'PREPRINTED' ? Number(draft.range_start) : null,
          range_end: draft.numbering_owner === 'PREPRINTED' ? Number(draft.range_end) : null,
          template_code: draft.template_code.trim(), notes: draft.notes.trim(),
          sequence_policy: draft.numbering_owner === 'ERPNEXT' ? 'ERPNext emite y conserva el correlativo; SmartDiag sólo presenta el documento.' : 'La hoja preimpresa conserva el correlativo físico; SmartDiag registra la referencia utilizada.',
        },
      });
      setDraft(emptyDraft(draft.branch_id)); await onReload(); setMessage('Borrador fiscal guardado. El contador debe revisarlo y activarlo.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo guardar la configuración fiscal.'); }
    finally { setBusy(false); }
  }

  async function setStatus(document: ManagementDocument, status: 'ACTIVE' | 'EXPIRED') {
    setBusy(true); setMessage('');
    try {
      await updateManagementDocumentStatus(token, document.id, { status, accountant_confirmed: status === 'ACTIVE' && confirmed[document.id], note: status === 'ACTIVE' ? 'Revisión contable confirmada desde SmartDiag504' : 'Serie cerrada desde el módulo contable' });
      await onReload(); setMessage(status === 'ACTIVE' ? 'Configuración fiscal activada; cualquier serie anterior quedó cerrada.' : 'Configuración fiscal cerrada.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo cambiar el estado.'); }
    finally { setBusy(false); }
  }

  return <div className="accounting-workspace role-view">
    <header className="content-header"><div><span>Contabilidad y fiscalidad</span><h1>Configuración del contador</h1><p>Defina quién controla la numeración y cómo se imprime. SmartDiag no mantiene un segundo libro ni inventa comprobantes fiscales.</p></div><span className="erp-engine-status"><Landmark /> Fuente contable: {summary?.accounting_source ?? 'ERPNext'}</span></header>
    {message && <p className="document-message">{message}</p>}
    <section className="accounting-boundary role-panel"><ShieldAlert /><div><h2>Una sola numeración activa por sucursal</h2><p><b>ERPNext:</b> el ERP genera el correlativo y SmartDiag imprime su documento. <b>Hoja preimpresa:</b> el contador registra CAI/rango y el número físico usado; SmartDiag no genera otra numeración.</p></div></section>
    <div className="accounting-layout">
      <form className="role-panel fiscal-form" onSubmit={save}><header><FileCog /><div><h2>Nueva configuración fiscal</h2><p>Se guarda primero como borrador.</p></div></header>
        <div className="fiscal-fields">
          <label>Sucursal<select required value={draft.branch_id} onChange={(event) => field('branch_id', event.target.value)}><option value="">Seleccione</option>{overview.branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.code} · {branch.name}</option>)}</select></label>
          <label>Dueño de numeración<select value={draft.numbering_owner} onChange={(event) => field('numbering_owner', event.target.value as FiscalDraft['numbering_owner'])}><option value="ERPNEXT">ERPNext</option><option value="PREPRINTED">Hoja preimpresa</option></select></label>
          <label>Razón social<input required value={draft.legal_name} onChange={(event) => field('legal_name', event.target.value)} /></label>
          <label>RTN<input required value={draft.rtn} onChange={(event) => field('rtn', event.target.value)} /></label>
          <label>Tipo de documento<select value={draft.document_kind} onChange={(event) => field('document_kind', event.target.value)}><option>FACTURA</option><option>TICKET</option><option>NOTA_CREDITO</option><option>NOTA_DEBITO</option><option>PROFORMA</option></select></label>
          <label>Nombre de serie<input required value={draft.series_name} placeholder="FACTURA PRINCIPAL 2026" onChange={(event) => field('series_name', event.target.value)} /></label>
          <label>CAI aprobado<input value={draft.cai} onChange={(event) => field('cai', event.target.value)} /></label>
          <label>Prefijo<input value={draft.prefix} onChange={(event) => field('prefix', event.target.value)} placeholder="000-001-01" /></label>
          {draft.numbering_owner === 'PREPRINTED' && <><label>Rango inicial<input required type="number" min="1" value={draft.range_start} onChange={(event) => field('range_start', event.target.value)} /></label><label>Rango final<input required type="number" min="1" value={draft.range_end} onChange={(event) => field('range_end', event.target.value)} /></label></>}
          <label>Vigente desde<input type="date" value={draft.valid_from} onChange={(event) => field('valid_from', event.target.value)} /></label>
          <label>Fecha límite<input type="date" value={draft.valid_until} onChange={(event) => field('valid_until', event.target.value)} /></label>
          <label>Código de plantilla<input required value={draft.template_code} onChange={(event) => field('template_code', event.target.value.toUpperCase())} /></label>
          <label className="fiscal-notes">Observaciones<textarea rows={3} value={draft.notes} onChange={(event) => field('notes', event.target.value)} /></label>
        </div><button className="role-primary" disabled={busy}><Save /> Guardar borrador para revisión</button>
      </form>
      <section className="role-panel fiscal-register"><header><BookOpen /><div><h2>Series y formatos</h2><p>{fiscalDocuments.length} configuraciones registradas</p></div></header>
        {fiscalDocuments.map((document) => { const meta = fiscalMeta(document); return <article key={document.id} className={`fiscal-record fiscal-record--${document.status.toLowerCase()}`}><header><div><small>{String(meta.document_kind ?? 'DOCUMENTO')} · {String(meta.numbering_owner ?? 'SIN DEFINIR')}</small><h3>{document.number}</h3></div><b>{document.status}</b></header><dl><div><dt>Razón social</dt><dd>{String(meta.legal_name ?? '—')}</dd></div><div><dt>RTN</dt><dd>{String(meta.rtn ?? '—')}</dd></div><div><dt>CAI / prefijo</dt><dd>{String(meta.cai ?? 'Pendiente')} · {String(meta.prefix ?? '—')}</dd></div><div><dt>Plantilla</dt><dd>{String(meta.template_code ?? '—')}</dd></div></dl>{document.status === 'DRAFT' && <><label className="accountant-confirm"><input type="checkbox" checked={Boolean(confirmed[document.id])} onChange={(event) => setConfirmed((current) => ({ ...current, [document.id]: event.target.checked }))} /> Confirmo que el contador revisó CAI, rango, fechas, impuestos y formato.</label><button disabled={busy || !confirmed[document.id]} onClick={() => void setStatus(document, 'ACTIVE')}><BadgeCheck /> Activar y cerrar serie anterior</button></>}{document.status === 'ACTIVE' && <button className="fiscal-expire" disabled={busy} onClick={() => void setStatus(document, 'EXPIRED')}><Printer /> Cerrar serie</button>}</article>; })}
        {!fiscalDocuments.length && <p className="empty-bookings">No hay configuración fiscal. Cree un borrador junto con el contador.</p>}
      </section>
    </div>
  </div>;
}
