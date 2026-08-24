import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

const productPage = {
  items: [
    {
      id: 'p1', sku: 'FL-910S', name: 'Filtro de aceite FL-910S', description: 'Filtro original',
      brand: 'Motorcraft', category_id: null, display_price: '249.00', currency: 'HNL',
      stock_status: 'IN_STOCK', compatibility_note: 'Validar por VIN', erpnext_item_code: null,
      published: true, active: true, images: [],
    },
  ], total: 1, limit: 24, offset: 0,
};

beforeEach(() => {
  window.history.replaceState({}, '', '/lading');
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => new Response(JSON.stringify(String(input).endsWith('/api/v1/branding') ? {
    organization_id: 'SMARTDIAG504', display_name: 'SmartDiag504', legal_name: 'SmartDiag504', tax_id: '',
    address: 'Tegucigalpa, Honduras', phone: '', email: 'info@smartdiag504.com', website: 'https://taller.nexusmedi.org',
    primary_color: '#ED111C', accent_color: '#C3000B', surface_color: '#FFFFFF', text_color: '#17181C',
    logo_url: '/brand/smartdiag504-logo.png', logo_dark_url: '/brand/smartdiag504-logo.png', favicon_url: '/brand/smartdiag504-logo.png',
    seasonal_theme_enabled: true, seasonal_theme_code: 'PATRIA_SEPTEMBER',
    seasonal_theme_title: 'Mes de la patria', seasonal_theme_message: 'Celebramos Honduras y Centroamérica',
    document_footer: 'Documento generado desde SmartDiag504.', asset_history: [], updated_at: null,
  } : productPage), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })));
});

describe('SmartDiag504 public site', () => {
  it('presents workshop, parts and booking actions', async () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /diagnóstico preciso/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /reservar diagnóstico/i })).toHaveAttribute('href', '#reservar');
    expect(screen.getAllByRole('link', { name: /comprar repuestos/i })[0]).toHaveAttribute('href', '/lading/repuestos');
    expect(screen.getByText(/mes de la patria/i)).toBeInTheDocument();
    expect(screen.getByRole('complementary', { name: /honduras, mes de la patria/i })).toHaveClass('seasonal-banner--patria_september');
  });

  it('filters catalog by search text', async () => {
    window.history.replaceState({}, '', '/lading/repuestos');
    const user = userEvent.setup();
    render(<App />);
    const search = await screen.findByRole('searchbox', { name: /buscar repuesto/i });
    expect(await screen.findByText('Filtro de aceite FL-910S')).toBeInTheDocument();
    await user.type(search, 'filtro');
    expect(fetch).toHaveBeenLastCalledWith(expect.stringContaining('q=filtro'), expect.anything());
  });
});
