import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { SettingsView } from './SettingsView';

vi.mock('../lib/api', () => ({
  saveWorkshopView: vi.fn(),
  downloadCatalogTemplate: vi.fn(),
  previewCatalogImport: vi.fn().mockResolvedValue({
    summary: { labor: 2, parts: 3, errors: 0 }, labor: [], parts: [], errors: [],
  }),
  applyCatalogImport: vi.fn(),
  getStaffMe: vi.fn().mockResolvedValue({ mfa_enabled: false }),
  enrollStaffMfa: vi.fn(),
  confirmStaffMfa: vi.fn(),
  disableStaffMfa: vi.fn(),
  revokeStaffSessions: vi.fn(),
  getProductionReadiness: vi.fn().mockResolvedValue({
    environment: 'test', organization_id: 'SMARTDIAG504', production_ready: false,
    summary: { ready: 4, total: 9 }, gates: [],
  }),
  getAdminBranding: vi.fn().mockResolvedValue({
    organization_id: 'SMARTDIAG504', display_name: 'SmartDiag504', legal_name: 'SmartDiag504', tax_id: '',
    address: 'Tegucigalpa, Honduras', phone: '', email: 'info@smartdiag504.com', website: 'https://taller.nexusmedi.org',
    primary_color: '#ED111C', accent_color: '#C3000B', surface_color: '#FFFFFF', text_color: '#17181C',
    logo_url: '/brand/smartdiag504-logo.png', logo_dark_url: '/brand/smartdiag504-logo.png', favicon_url: '/brand/smartdiag504-logo.png',
    document_footer: 'Documento generado desde SmartDiag504.', asset_history: [], updated_at: null,
  }),
  updateBranding: vi.fn(),
  uploadBrandAsset: vi.fn(),
}));

describe('SettingsView catalog import', () => {
  it('shows the required workbook fields and previews an xlsx file', async () => {
    const user = userEvent.setup();
    render(<SettingsView token="test" setting={{ default_view: 'KANBAN', bays_enabled: false }} onChange={vi.fn()} />);

    expect(screen.getByText('Catálogo por vehículo')).toBeInTheDocument();
    expect(screen.getByText(/código, descripción, vehículo, tiempo, costo y precio/i)).toBeInTheDocument();

    const input = screen.getByLabelText('Archivo Excel del catálogo');
    await user.upload(input, new File(['xlsx'], 'catalogo.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }));
    await user.click(screen.getByRole('button', { name: /validar archivo/i }));

    expect(await screen.findByText('2 manos de obra')).toBeInTheDocument();
    expect(screen.getByText('3 repuestos')).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /configurar mfa/i })).toBeInTheDocument();
  });
});
