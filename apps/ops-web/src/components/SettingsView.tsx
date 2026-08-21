import { type ChangeEvent, useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle2, Columns3, Download, FileSpreadsheet, KeyRound, LayoutGrid, Save, ShieldCheck, Upload, Warehouse } from 'lucide-react';
import { applyCatalogImport, confirmStaffMfa, disableStaffMfa, downloadCatalogTemplate, enrollStaffMfa, getProductionReadiness, getStaffMe, previewCatalogImport, revokeStaffSessions, saveWorkshopView, type ProductionReadiness } from '../lib/api';
import type { CatalogImportPreview, WorkshopViewSetting } from '../types';
import { BrandingSettings } from './BrandingSettings';

export function SettingsView({ token, setting, onChange }: { token: string; setting: WorkshopViewSetting; onChange: (setting: WorkshopViewSetting) => void }) {
  const [draft, setDraft] = useState(setting); const [message, setMessage] = useState('');
  const [catalogFile, setCatalogFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CatalogImportPreview | null>(null);
  const [catalogBusy, setCatalogBusy] = useState(false);
  const [catalogMessage, setCatalogMessage] = useState('');
  const [mfaEnabled, setMfaEnabled] = useState<boolean | null>(null);
  const [mfaEnrollment, setMfaEnrollment] = useState<{ secret: string; provisioning_uri: string } | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [securityMessage, setSecurityMessage] = useState('');
  const [readiness, setReadiness] = useState<ProductionReadiness | null>(null);
  useEffect(() => { void getStaffMe().then((profile) => setMfaEnabled(profile.mfa_enabled)).catch(() => setMfaEnabled(null)); }, []);
  useEffect(() => { void getProductionReadiness(token).then(setReadiness).catch(() => setReadiness(null)); }, [token]);
  async function save() { const saved = await saveWorkshopView(token, draft); onChange(saved); setMessage('Configuración guardada para todos los usuarios.'); }
  function selectCatalogFile(event: ChangeEvent<HTMLInputElement>) { setCatalogFile(event.target.files?.[0] ?? null); setPreview(null); setCatalogMessage(''); }
  async function validateCatalog() {
    if (!catalogFile) return;
    setCatalogBusy(true); setCatalogMessage('');
    try { setPreview(await previewCatalogImport(token, catalogFile)); }
    catch (error) { setCatalogMessage(error instanceof Error ? error.message : 'No se pudo validar el archivo.'); }
    finally { setCatalogBusy(false); }
  }
  async function confirmCatalog() {
    if (!catalogFile || !preview || preview.summary.errors) return;
    setCatalogBusy(true);
    try { await applyCatalogImport(token, catalogFile); setCatalogMessage('Catálogo aplicado en ERPNext correctamente.'); }
    catch (error) { setCatalogMessage(error instanceof Error ? error.message : 'No se pudo aplicar el catálogo.'); }
    finally { setCatalogBusy(false); }
  }
  async function beginMfa() { setMfaEnrollment(await enrollStaffMfa()); setSecurityMessage('Escanee la clave con su aplicacion autenticadora y confirme el codigo.'); }
  async function confirmMfa() { await confirmStaffMfa(mfaCode); setMfaEnabled(true); setMfaEnrollment(null); setMfaCode(''); setSecurityMessage('MFA activado. Inicie sesion nuevamente con su codigo.'); }
  async function disableMfa() { await disableStaffMfa(mfaCode); setMfaEnabled(false); setMfaCode(''); setSecurityMessage('MFA desactivado y sesiones anteriores revocadas.'); }
  async function revokeSessions() { await revokeStaffSessions(); setSecurityMessage('Todas sus sesiones fueron revocadas. Debe iniciar sesion nuevamente.'); }
  return <div className="settings-view"><header className="content-header"><div><span>Configuración operativa</span><h1>Configuración del taller</h1><p>Administre marca, vistas de trabajo, seguridad y catálogos controlados por ERPNext.</p></div></header>
    <BrandingSettings token={token} />
    <section className="setting-card production-readiness"><div className="setting-card__intro"><ShieldCheck /><div><h2>Preparación para producción</h2><p>Lista verificable de requisitos internos y aceptaciones externas. Un requisito pendiente nunca se presenta como terminado.</p></div>{readiness && <strong>{readiness.summary.ready}/{readiness.summary.total}</strong>}</div>
      {!readiness ? <p>No se pudo cargar la verificación protegida.</p> : <><div className="readiness-grid">{readiness.gates.map((gate) => <article className={gate.ready ? 'readiness-item readiness-item--ready' : 'readiness-item'} key={gate.code}>{gate.ready ? <CheckCircle2 /> : <AlertTriangle />}<span><b>{gate.label}</b><small>Responsable: {gate.owner}</small></span><em>{gate.ready ? 'LISTO' : 'PENDIENTE'}</em></article>)}</div><p className={readiness.production_ready ? 'success-copy' : 'global-error'}>{readiness.production_ready ? 'Todos los controles de salida están aprobados.' : 'Este entorno todavía no debe declararse productivo.'}</p></>}
    </section>
    <div className="setting-card"><div className="setting-card__intro"><Warehouse /><div><h2>Control de bahías</h2><p>Activa el mapa visual de espacios y permite asignar un código de bahía a cada OT.</p></div><label className="switch"><input aria-label="Activar control de bahías" type="checkbox" checked={draft.bays_enabled} onChange={(event) => setDraft({ bays_enabled: event.target.checked, default_view: event.target.checked ? draft.default_view : 'KANBAN' })} /><span /></label></div>
      <div className="view-options"><button className={draft.default_view === 'KANBAN' ? 'view-option view-option--active' : 'view-option'} onClick={() => setDraft({ ...draft, default_view: 'KANBAN' })}><Columns3 /><strong>Kanban</strong><span>Seis etapas operativas</span></button><button disabled={!draft.bays_enabled} className={draft.default_view === 'BAYS' ? 'view-option view-option--active' : 'view-option'} onClick={() => setDraft({ ...draft, default_view: 'BAYS' })}><LayoutGrid /><strong>Bahías</strong><span>Distribución física del taller</span></button></div>
      <button className="primary-action" onClick={save}><Save size={17} /> Guardar configuración</button>{message && <p className="success-copy">{message}</p>}</div>
    <section className="setting-card"><div className="setting-card__intro"><ShieldCheck /><div><h2>Seguridad de mi cuenta</h2><p>MFA usa códigos TOTP y la revocación invalida todas las sesiones abiertas.</p></div></div>
      {mfaEnabled === null ? <p>Ingrese con un usuario individual para administrar esta seguridad.</p> : <div className="catalog-import-actions">
        {!mfaEnabled && !mfaEnrollment && <button className="secondary-action" type="button" onClick={() => void beginMfa()}><KeyRound size={17} /> Configurar MFA</button>}
        {mfaEnrollment && <><label>Clave TOTP<input aria-label="Clave TOTP" readOnly value={mfaEnrollment.secret} /></label><label>Código de 6 dígitos<input aria-label="Confirmar código MFA" inputMode="numeric" maxLength={6} value={mfaCode} onChange={(event) => setMfaCode(event.target.value.replace(/\D/g, ''))} /></label><button className="primary-action" type="button" disabled={mfaCode.length !== 6} onClick={() => void confirmMfa()}>Confirmar MFA</button></>}
        {mfaEnabled && <><label>Código actual<input aria-label="Código MFA actual" inputMode="numeric" maxLength={6} value={mfaCode} onChange={(event) => setMfaCode(event.target.value.replace(/\D/g, ''))} /></label><button className="secondary-action" type="button" disabled={mfaCode.length !== 6} onClick={() => void disableMfa()}>Desactivar MFA</button></>}
        <button className="secondary-action" type="button" onClick={() => void revokeSessions()}>Revocar todas mis sesiones</button>
      </div>}
      {securityMessage && <p className="success-copy">{securityMessage}</p>}
    </section>
    <section className="catalog-import-card">
      <div className="catalog-import-card__heading"><FileSpreadsheet /><div><h2>Catálogo por vehículo</h2><p>Cargue manos de obra y repuestos para que cada OT muestre únicamente opciones compatibles con el carro seleccionado.</p></div></div>
      <div className="catalog-import-guide"><strong>La plantilla incluye</strong><span>Mano de obra: código, descripción, vehículo, tiempo, costo y precio al cliente.</span><span>Repuestos: código, descripción, OEM, vehículo, costo y precio al cliente.</span><small>Para usar un código en varios carros, repita el código en otra fila con la nueva compatibilidad.</small></div>
      <div className="catalog-import-actions">
        <button className="secondary-action" type="button" onClick={() => void downloadCatalogTemplate(token)}><Download size={17} /> Descargar plantilla Excel</button>
        <label className="file-control"><Upload size={18} /><span>{catalogFile?.name ?? 'Seleccionar archivo .xlsx'}</span><input aria-label="Archivo Excel del catálogo" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={selectCatalogFile} /></label>
        <button className="primary-action" type="button" disabled={!catalogFile || catalogBusy} onClick={() => void validateCatalog()}>{catalogBusy ? 'Validando…' : 'Validar archivo'}</button>
      </div>
      {preview && <div className={preview.summary.errors ? 'import-result import-result--error' : 'import-result'}>
        <div><CheckCircle2 /><strong>{preview.summary.labor} manos de obra</strong><strong>{preview.summary.parts} repuestos</strong><strong>{preview.summary.errors} errores</strong></div>
        {preview.errors.slice(0, 12).map((error, index) => <p key={`${error.sheet}-${error.row}-${index}`}><b>{error.sheet}, fila {error.row}, {error.column}:</b> {error.message}</p>)}
        {!preview.summary.errors && <button className="primary-action" type="button" disabled={catalogBusy} onClick={() => void confirmCatalog()}>Confirmar e importar a ERPNext</button>}
      </div>}
      {catalogMessage && <p className="success-copy">{catalogMessage}</p>}
    </section>
  </div>;
}
