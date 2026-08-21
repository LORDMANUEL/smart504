import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CustomerPortal } from './CustomerExperience';

describe('authenticated customer calendar', () => {
  beforeEach(() => {
    sessionStorage.setItem('smartdiag-client-session', 'authenticated');
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => Promise.resolve({ ok: true, json: async () => url.includes('/compatible-parts') ? [{
      id: 'part-1', sku: 'FLT-ESC-2020', name: 'Filtro persistente Escape', short_description: 'Filtro real', description: null,
      category_id: null, brand: 'SmartSelect', price: '525.00', currency: 'HNL', stock_status: 'IN_STOCK', active: true,
      compatibility_notes: 'Ford Escape 2020', source_system: 'ERPNEXT', source_reference: 'FLT-ESC-2020', images: [],
    }] : url.includes('/dashboard') ? {
      profile: { full_name: 'Cliente demo', email: 'cliente@example.com', username: 'cliente.demo', mfa_enabled: false, loyalty_enabled: true, loyalty_points: 245, credit_requested: false, credit_status: 'NO_SOLICITADO' },
      vehicles: [{ id: 'escape', label: 'Ford Escape 2020', make: 'Ford', model: 'Escape', model_year: 2020, engine: '2.0', plate: 'HAA5040', vin: '1FMCU0G6XLUA12545', mileage_km: 86000, photo_url: '/vehicles/ford-escape-2020.png', maintenance: { status: 'PRÓXIMO', next_service_km: 86800, oil_last_km: 81800, oil_next_km: 86800 }, history: [], advice: [] }],
      alerts: [], quotes: [], invoices: [],
    } : [] })));
  });

  afterEach(() => {
    cleanup();
    sessionStorage.clear();
    vi.unstubAllGlobals();
  });

  it('offers an authenticated appointment without sending the user to the public form', async () => {
    const user = userEvent.setup();
    render(<CustomerPortal />);
    const link = await screen.findByRole('link', { name: /agendar cita/i });
    expect(link).toHaveAttribute('href', '#appointments');
    await user.click(link);
    await waitFor(() => expect(screen.getByRole('heading', { name: /reservar en el calendario/i })).toBeInTheDocument());
    expect(screen.getByText(/vinculada a su cuenta/i)).toBeInTheDocument();
  });

  it('loads compatible parts from the authenticated catalog instead of fixtures', async () => {
    const user = userEvent.setup();
    render(<CustomerPortal />);
    await user.click(await screen.findByRole('link', { name: /repuestos compatibles/i }));
    expect(await screen.findByText('Filtro persistente Escape')).toBeInTheDocument();
    expect(screen.getByText(/FLT-ESC-2020/)).toBeInTheDocument();
  });
});
