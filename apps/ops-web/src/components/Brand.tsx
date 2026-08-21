import { useBranding } from '../lib/branding';

export function Brand({ compact = false }: { compact?: boolean }) {
  const branding = useBranding();
  return (
    <span className={`ops-brand ${compact ? 'ops-brand--compact' : ''}`} aria-label={`${branding.display_name} Operaciones`}>
      <img
        className="ops-brand__logo"
        src={branding.logo_dark_url || branding.logo_url}
        alt={branding.display_name}
        width={compact ? 102 : 132}
        height={compact ? 40 : 52}
      />
      <small>{branding.display_name} · OPERACIONES</small>
    </span>
  );
}
