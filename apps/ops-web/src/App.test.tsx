import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const board = {
  columns: [
    ['CREATED', 'OT creada'],
    ['QUOTED_BY_TECHNICIAN', 'OT cotizada por técnico'],
    ['PENDING_CUSTOMER_APPROVAL', 'OT pendiente aprobación cliente'],
    ['PENDING_PARTS', 'OT pendiente de repuestos'],
    ['READY_TO_INVOICE', 'OT finalizada para facturar'],
    ['INVOICED', 'OT facturada'],
  ].map(([status, label], index) => ({
    status, label, cards: index === 0 ? [{
      id: 'wo-1', external_reference: 'OT-0001', customer_id: 'c1', vehicle_id: 'v1',
      title: 'Diagnóstico transmisión', technician_name: 'Carlos', bay_code: null, status,
      quote_total: null, invoice_reference: null, promised_at: null, version: 1,
      created_at: '2026-08-12T10:00:00Z', updated_at: '2026-08-12T10:00:00Z',
      vehicle_label: 'Ford Escape 2020 · HAA0001', customer_name: 'Ana López',
      parts_required: [{
        request_id: 'request-1', product_id: 'product-1', sku: 'F150-FIL-2018',
        name: 'Filtro de aceite', quantity: 1, note: '', status: 'REQUESTED',
        actor: 'tecnico-demo', requested_at: '2026-08-13T10:00:00Z',
        stock_status: 'IN_STOCK', location: 'Por asignar en bodega',
      }],
    }] : [],
  })),
};

beforeEach(() => {
  window.history.replaceState({}, '', '/tallerv1/login');
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith('/api/v1/branding')) return new Response(JSON.stringify({
      organization_id: 'SMARTDIAG504', display_name: 'SmartDiag504', legal_name: 'SmartDiag504', tax_id: '',
      address: 'Tegucigalpa, Honduras', phone: '', email: 'info@smartdiag504.com', website: 'https://taller.nexusmedi.org',
      primary_color: '#ED111C', accent_color: '#C3000B', surface_color: '#FFFFFF', text_color: '#17181C',
      logo_url: '/brand/smartdiag504-logo.png', logo_dark_url: '/brand/smartdiag504-logo.png', favicon_url: '/brand/smartdiag504-logo.png',
      document_footer: 'Documento generado desde SmartDiag504.', asset_history: [], updated_at: null,
    }), { status: 200 });
    if (url.includes('/operations/settings/workshop')) {
      return new Response(JSON.stringify({ default_view: 'KANBAN', bays_enabled: false }), { status: 200 });
    }
    if (url.includes('/work-orders/board')) return new Response(JSON.stringify(board.columns.map(({ status, label, cards }) => ({ status, label, work_orders: cards }))), { status: 200 });
    if (url.includes('/operations/labor-catalog')) return new Response(JSON.stringify([
      { code: 'MO-DIAG-001', description: 'Diagnóstico electrónico completo', hours: '1.500', price: '1200.00' },
    ]), { status: 200 });
    if (url.includes('/labor-entries')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/admin/catalog/products')) return new Response(JSON.stringify([
      { id: 'escape-part', sku: 'ESC-FIL-2020', name: 'Filtro Escape', short_description: null, description: null, brand: null, category_id: null, price: '285.00', currency: 'HNL', stock_status: 'IN_STOCK', stock_qty: '8', compatibility_notes: 'Ford Escape 2020', source_system: 'LOCAL', source_reference: null, active: true, images: [] },
      { id: 'civic-part', sku: 'CIV-FIL-2008', name: 'Filtro Civic', short_description: null, description: null, brand: null, category_id: null, price: '250.00', currency: 'HNL', stock_status: 'IN_STOCK', stock_qty: '8', compatibility_notes: 'Honda Civic 2008', source_system: 'LOCAL', source_reference: null, active: true, images: [] },
    ]), { status: 200 });
    if (url.includes('/cluster/heartbeats')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/flow-events/heatmap')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/finance/counter-sales/context')) return new Response(JSON.stringify({
      branches: [{ id: 'branch-1', code: 'MAIN', name: 'Sucursal principal' }],
      warehouses: [{ id: 'warehouse-1', branch_id: 'branch-1', code: 'MAIN-STOCK', name: 'Bodega principal' }],
      products: [{ id: 'escape-part', sku: 'ESC-FIL-2020', name: 'Filtro Escape', price: '285.00', stock_qty: '8', stock_status: 'IN_STOCK' }],
    }), { status: 200 });
    if (url.includes('/operations/finance/counter-sales')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/finance/approval-requests')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/finance/quotes')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/finance/cash-summary')) return new Response(JSON.stringify({ session: null, payments: [], totals_by_method: {}, total_collected: '0' }), { status: 200 });
    if (url.includes('/operations/documents/templates')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/documents/renders')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/staff/compensation-profiles')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/staff/technicians')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/staff/users')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/staff/access-events')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/control/overview')) return new Response(JSON.stringify({
      branches: [], warehouses: [], reservations: [], transfers: [], shipments: [],
      quality_cases: [], leads: [], management_documents: [],
    }), { status: 200 });
    if (url.includes('/admin/store/orders')) return new Response(JSON.stringify([]), { status: 200 });
    if (url.includes('/operations/bookings')) return new Response(JSON.stringify([{
      id: 'booking-1', full_name: 'Laura Demo', phone: '99990000', email: 'laura@example.com',
      vehicle_summary: 'Ford Escape 2020', service_requested: 'Diagnóstico electrónico',
      preferred_date: '2026-08-20', concern: 'Luz de motor encendida', status: 'NEW', source: 'WEB',
      created_at: '2026-08-13T10:00:00Z', updated_at: '2026-08-13T10:00:00Z',
    }]), { status: 200 });
    return new Response(JSON.stringify({}), { status: 200 });
  }));
});

describe('SmartDiag504 operations', () => {
  it('renders the six canonical work order stages', async () => {
    render(<App initialToken="test-admin-token" />);
    for (const label of [
      'OT creada', 'OT cotizada por técnico', 'OT pendiente aprobación cliente',
      'OT pendiente de repuestos', 'OT finalizada para facturar', 'OT facturada',
    ]) expect(await screen.findByText(label)).toBeInTheDocument();
    expect(screen.getByText('Ford Escape 2020 · HAA0001')).toBeInTheDocument();
  });

  it('keeps bays disabled until the administrator enables them', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click((await screen.findAllByRole('button', { name: /bahías/i }))[0]);
    expect(screen.getByText(/vista de bahías está desactivada/i)).toBeInTheDocument();
  });

  it('offers product and image administration', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /catálogo/i }));
    expect(screen.getByRole('button', { name: /crear producto/i })).toBeInTheDocument();
    expect(screen.getAllByText('Filtro Escape').length).toBeGreaterThan(0);
  });

  it('shows a separate counter sales workflow', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /mostrador/i }));
    expect(await screen.findByRole('heading', { name: 'Mostrador' })).toBeInTheDocument();
    expect(screen.getByText(/Abra Caja antes de vender/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Agregar Filtro Escape/i })).toBeInTheDocument();
    expect(screen.getByText(/Ventas y devoluciones/i)).toBeInTheDocument();
  });

  it('opens an order and exposes parts, history and manual search', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /abrir ot ot-0001/i }));
    expect(screen.getByRole('dialog', { name: /detalle de ot/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /repuestos/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /manuales/i })).toBeInTheDocument();
    await user.click(screen.getByRole('tab', { name: /repuestos/i }));
    expect(screen.getByText('Filtro Escape')).toBeInTheDocument();
    expect(screen.queryByText('Filtro Civic')).not.toBeInTheDocument();
    await user.click(screen.getByRole('tab', { name: /Mano de obra/i }));
    expect(screen.getByText(/Seleccionar mano de obra/i)).toBeInTheDocument();
  });

  it('lists web bookings for reception', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /citas/i }));
    expect(await screen.findByText('Laura Demo')).toBeInTheDocument();
    expect(screen.getByText('Ford Escape 2020')).toBeInTheDocument();
  });

  it('shows persistent OT part requests in the warehouse picking queue', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /bodega/i }));
    expect(await screen.findByText(/Filtro de aceite/)).toBeInTheDocument();
    expect(screen.getByText(/OT-0001/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /avanzar/i })).toBeInTheDocument();
  });

  it('groups the flow map inside processes and quality', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    const moduleNavigation = await screen.findByRole('navigation', { name: /módulos de operación/i });
    expect(within(moduleNavigation).queryByRole('button', { name: /mapa de flujos/i })).not.toBeInTheDocument();
    await user.click(within(moduleNavigation).getByRole('button', { name: /procesos y calidad/i }));
    const processNavigation = screen.getByRole('navigation', { name: /secciones de procesos y calidad/i });
    await user.click(within(processNavigation).getByRole('button', { name: /mapa de flujos/i }));
    expect(screen.getByRole('heading', { name: /mapa operativo de flujos/i })).toBeInTheDocument();
    expect(within(moduleNavigation).getByRole('button', { name: /procesos y calidad/i })).toHaveClass('nav-item--active');
  });

  it('opens the configurable document and print center', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /documentos/i }));
    expect(await screen.findByRole('heading', { name: /centro único de formatos e impresión/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /nueva plantilla/i })).toBeInTheDocument();
    expect(screen.getByText(/variables permitidas/i)).toBeInTheDocument();
  });

  it('opens staff, role and access administration', async () => {
    const user = userEvent.setup();
    render(<App initialToken="test-admin-token" />);
    await user.click(await screen.findByRole('button', { name: /personal y accesos/i }));
    expect(await screen.findByRole('heading', { name: /personal, roles y accesos/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /crear acceso individual/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Costos y tarifas de técnicos/i })).toBeInTheDocument();
    expect(screen.getByText(/bitácora de accesos/i)).toBeInTheDocument();
  });
});
