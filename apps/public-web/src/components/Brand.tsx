import { useBranding } from '../lib/branding';

export function Brand({ compact = false }: { compact?: boolean }) {
  const branding = useBranding();
  return (
    <span className={`brand ${compact ? 'brand--compact' : ''}`} aria-label={branding.display_name}>
      <img
        className="brand__logo"
        src={branding.logo_url}
        alt={branding.display_name}
        width={compact ? 108 : 148}
        height={compact ? 42 : 58}
      />
    </span>
  );
}
