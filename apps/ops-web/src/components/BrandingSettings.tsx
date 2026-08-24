import { useEffect, useState, type ChangeEvent, type CSSProperties } from 'react';
import { ImageUp, Palette, Save } from 'lucide-react';
import { getAdminBranding, updateBranding, uploadBrandAsset } from '../lib/api';
import { fallbackBranding, publishBranding } from '../lib/branding';
import type { BrandingProfile } from '../types';

type AssetType = 'LOGO' | 'LOGO_DARK' | 'FAVICON';
const assetLabels: Record<AssetType, string> = { LOGO: 'Logo claro', LOGO_DARK: 'Logo para fondos oscuros', FAVICON: 'Ícono del navegador' };

export function BrandingSettings({ token }: { token: string }) {
  const [draft, setDraft] = useState<BrandingProfile>(fallbackBranding);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => { void getAdminBranding(token).then(setDraft).catch((error) => setMessage(error instanceof Error ? error.message : 'No se pudo cargar la marca.')); }, [token]);
  function field<K extends keyof BrandingProfile>(key: K, value: BrandingProfile[K]) { setDraft((current) => ({ ...current, [key]: value })); }
  async function save() {
    setBusy(true); setMessage('');
    try {
      const saved = await updateBranding(token, {
        display_name: draft.display_name, legal_name: draft.legal_name, tax_id: draft.tax_id,
        address: draft.address, phone: draft.phone, email: draft.email, website: draft.website,
        primary_color: draft.primary_color, accent_color: draft.accent_color,
        surface_color: draft.surface_color, text_color: draft.text_color,
        document_footer: draft.document_footer,
        seasonal_theme_enabled: draft.seasonal_theme_enabled,
        seasonal_theme_code: draft.seasonal_theme_code,
        seasonal_theme_title: draft.seasonal_theme_title,
        seasonal_theme_message: draft.seasonal_theme_message,
      });
      setDraft(saved); publishBranding(saved); setMessage('Marca guardada y aplicada a la operación.');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo guardar la marca.'); }
    finally { setBusy(false); }
  }
  async function upload(event: ChangeEvent<HTMLInputElement>, assetType: AssetType) {
    const file = event.target.files?.[0]; if (!file) return;
    setBusy(true); setMessage('');
    try {
      const saved = await uploadBrandAsset(token, assetType, file);
      setDraft(saved); publishBranding(saved); setMessage(`${assetLabels[assetType]} reemplazado y aplicado.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'No se pudo subir la imagen.'); }
    finally { setBusy(false); event.target.value = ''; }
  }
  const previewStyle = { '--preview-primary': draft.primary_color, '--preview-accent': draft.accent_color, '--preview-surface': draft.surface_color, '--preview-text': draft.text_color } as CSSProperties;
  return <section className="setting-card branding-settings">
    <div className="setting-card__intro"><Palette /><div><h2>Marca de la empresa</h2><p>Un solo lugar para logos, colores y datos que usan la landing, operaciones, TV y documentos publicados.</p></div></div>
    <div className="branding-settings__layout">
      <div className="branding-settings__form">
        <label>Nombre visible<input value={draft.display_name} onChange={(event) => field('display_name', event.target.value)} /></label>
        <label>Razón social<input value={draft.legal_name} onChange={(event) => field('legal_name', event.target.value)} /></label>
        <label>RTN<input value={draft.tax_id} onChange={(event) => field('tax_id', event.target.value)} /></label>
        <label>Dirección<input value={draft.address} onChange={(event) => field('address', event.target.value)} /></label>
        <label>Teléfono<input value={draft.phone} onChange={(event) => field('phone', event.target.value)} /></label>
        <label>Correo<input type="email" value={draft.email ?? ''} onChange={(event) => field('email', event.target.value || null)} /></label>
        <label>Sitio web<input value={draft.website} onChange={(event) => field('website', event.target.value)} /></label>
        <label className="branding-settings__footer">Pie de documentos<textarea rows={3} value={draft.document_footer} onChange={(event) => field('document_footer', event.target.value)} /></label>
        <fieldset className="seasonal-theme-settings">
          <legend>Tema mensual de la landing</legend>
          <label className="seasonal-theme-toggle"><input type="checkbox" checked={draft.seasonal_theme_enabled} onChange={(event) => field('seasonal_theme_enabled', event.target.checked)} /> Activar tema temporal</label>
          <label>Tema<select value={draft.seasonal_theme_code} onChange={(event) => field('seasonal_theme_code', event.target.value as BrandingProfile['seasonal_theme_code'])}><option value="NONE">Sin tema</option><option value="JANUARY_NEW_YEAR">Enero · Nuevo año</option><option value="FEBRUARY_FRIENDSHIP">Febrero · Confianza</option><option value="MARCH_MAINTENANCE">Marzo · Mantenimiento</option><option value="APRIL_ROAD_SAFETY">Abril · Seguridad vial</option><option value="MAY_FAMILY">Mayo · Familia</option><option value="JUNE_ENVIRONMENT">Junio · Ambiente</option><option value="JULY_TRAVEL">Julio · Viajes</option><option value="AUGUST_WORKSHOP">Agosto · Taller</option><option value="PATRIA_SEPTEMBER">Septiembre patrio · Honduras y Centroamérica</option><option value="OCTOBER_PREVENTION">Octubre · Prevención</option><option value="NOVEMBER_SAVINGS">Noviembre · Ahorro</option><option value="DECEMBER_HOLIDAYS">Diciembre · Viajes seguros</option></select></label>
          <label>Título<input value={draft.seasonal_theme_title} placeholder="Mes de la patria" onChange={(event) => field('seasonal_theme_title', event.target.value)} /></label>
          <label className="branding-settings__footer">Mensaje<input value={draft.seasonal_theme_message} placeholder="Celebramos nuestra identidad centroamericana" onChange={(event) => field('seasonal_theme_message', event.target.value)} /></label>
          <small>El tema sólo cambia decoración y animaciones de la landing; no altera tienda, formularios, precios ni accesibilidad.</small>
        </fieldset>
        <div className="branding-colors">
          <label>Principal<input type="color" value={draft.primary_color} onChange={(event) => field('primary_color', event.target.value.toUpperCase())} /><code>{draft.primary_color}</code></label>
          <label>Acento<input type="color" value={draft.accent_color} onChange={(event) => field('accent_color', event.target.value.toUpperCase())} /><code>{draft.accent_color}</code></label>
          <label>Superficie<input type="color" value={draft.surface_color} onChange={(event) => field('surface_color', event.target.value.toUpperCase())} /><code>{draft.surface_color}</code></label>
          <label>Texto<input type="color" value={draft.text_color} onChange={(event) => field('text_color', event.target.value.toUpperCase())} /><code>{draft.text_color}</code></label>
        </div>
        <button className="primary-action" type="button" disabled={busy} onClick={() => void save()}><Save size={17} /> Guardar y aplicar marca</button>
      </div>
      <aside className="branding-preview" style={previewStyle}>
        <span>Vista previa</span><div><img src={draft.logo_url} alt={draft.display_name} /><small>{draft.legal_name}</small><h3>{draft.display_name}</h3><p>{draft.address}<br />{draft.phone} · {draft.email}</p><button type="button">Acción principal</button></div>
        {(Object.keys(assetLabels) as AssetType[]).map((assetType) => <label className="brand-upload" key={assetType}><ImageUp /><span><strong>{assetLabels[assetType]}</strong><small>PNG, JPG o WebP · máximo 4 MB</small></span><input aria-label={`Subir ${assetLabels[assetType]}`} type="file" accept="image/png,image/jpeg,image/webp" disabled={busy} onChange={(event) => void upload(event, assetType)} /></label>)}
      </aside>
    </div>
    {message ? <p className="success-copy" role="status">{message}</p> : null}
  </section>;
}
