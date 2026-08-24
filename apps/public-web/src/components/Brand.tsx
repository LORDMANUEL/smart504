import { useBranding } from '../lib/branding';

export function Brand({ compact = false }: { compact?: boolean }) {
  const branding = useBranding();
  const logoSource = branding.seasonal_theme_enabled && branding.seasonal_theme_code === 'PATRIA_SEPTEMBER'
    ? '/brand/smartdiag504-logo-patria.png'
    : branding.logo_url;
  return (
    <span className={`brand ${compact ? 'brand--compact' : ''}`} aria-label={branding.display_name}>
      <img
        className="brand__logo"
        src={logoSource}
        alt={branding.display_name}
        width={compact ? 108 : 148}
        height={compact ? 42 : 58}
        onError={(event) => {
          event.currentTarget.onerror = null;
          event.currentTarget.src = '/brand/smartdiag504-logo.png';
        }}
      />
    </span>
  );
}
