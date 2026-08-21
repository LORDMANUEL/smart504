import { useEffect, useState } from 'react';
import { getBranding } from './api';
import type { BrandingProfile } from '../types';

export const fallbackBranding: BrandingProfile = {
  organization_id: 'SMARTDIAG504', display_name: 'SmartDiag504', legal_name: 'SmartDiag504', tax_id: '',
  address: 'Tegucigalpa, Honduras', phone: '', email: 'info@smartdiag504.com', website: 'https://taller.nexusmedi.org',
  primary_color: '#ED111C', accent_color: '#C3000B', surface_color: '#FFFFFF', text_color: '#17181C',
  logo_url: '/brand/smartdiag504-logo.png', logo_dark_url: '/brand/smartdiag504-logo.png', favicon_url: '/brand/smartdiag504-logo.png',
  document_footer: 'Documento generado desde SmartDiag504.', asset_history: [], updated_at: null,
};

let brandingRequest: Promise<BrandingProfile> | null = null;

function accessibleOnWhite(color: string): string {
  const match = /^#([0-9a-f]{6})$/i.exec(color);
  if (!match) return '#9f0009';
  let channels = [0, 2, 4].map((index) => Number.parseInt(match[1].slice(index, index + 2), 16));
  const luminance = (values: number[]) => values.map((value) => value / 255).map((value) => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4).reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
  while (1.05 / (luminance(channels) + .05) < 4.5) channels = channels.map((value) => Math.max(0, Math.floor(value * .94)));
  return `#${channels.map((value) => value.toString(16).padStart(2, '0')).join('')}`;
}

export function applyBranding(profile: BrandingProfile) {
  const root = document.documentElement;
  const accessiblePrimary = accessibleOnWhite(profile.primary_color);
  const accessibleAccent = accessibleOnWhite(profile.accent_color);
  root.style.setProperty('--brand-primary', profile.primary_color);
  root.style.setProperty('--brand-accent', profile.accent_color);
  root.style.setProperty('--brand-surface', profile.surface_color);
  root.style.setProperty('--brand-text', profile.text_color);
  root.style.setProperty('--blue', accessiblePrimary);
  root.style.setProperty('--gold', accessiblePrimary);
  root.style.setProperty('--red', accessibleAccent);
  document.title = `${profile.display_name} | Operaciones`;
  let favicon = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
  if (!favicon) { favicon = document.createElement('link'); favicon.rel = 'icon'; document.head.appendChild(favicon); }
  favicon.href = profile.favicon_url;
}

export function publishBranding(profile: BrandingProfile) {
  brandingRequest = Promise.resolve(profile);
  applyBranding(profile);
  window.dispatchEvent(new CustomEvent<BrandingProfile>('smartdiag-branding-updated', { detail: profile }));
}

export function useBranding() {
  const [profile, setProfile] = useState(fallbackBranding);
  useEffect(() => {
    brandingRequest ??= getBranding();
    void brandingRequest.then((value) => { applyBranding(value); setProfile(value); }).catch(() => applyBranding(fallbackBranding));
    const onUpdate = (event: Event) => setProfile((event as CustomEvent<BrandingProfile>).detail);
    window.addEventListener('smartdiag-branding-updated', onUpdate);
    return () => window.removeEventListener('smartdiag-branding-updated', onUpdate);
  }, []);
  return profile;
}
