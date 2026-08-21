import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { StoreOrdersView } from './StoreOrdersView';
import type { StoreOrder } from '../types';

const order: StoreOrder = {
  id: 'order-1',
  order_number: 'WEB-20260812-ABCD1234',
  customer_name: 'Ana López',
  phone: '+504 9999-0000',
  email: 'ana@example.com',
  vehicle_vin: '1FTFW1ET1EFA00001',
  notes: 'Confirmar compatibilidad antes de despachar.',
  status: 'PENDING_CONFIRMATION',
  currency: 'HNL',
  subtotal: '1450.00',
  erpnext_sales_order_id: null,
  created_at: '2026-08-12T10:00:00Z',
  updated_at: '2026-08-12T10:00:00Z',
  items: [{
    id: 'line-1', product_id: 'product-1', sku: 'FL-910S', name: 'Filtro de aceite',
    quantity: 2, unit_price: '725.00', line_total: '1450.00',
  }],
};

describe('StoreOrdersView', () => {
  it('shows the customer, order reference and requested parts', () => {
    render(<StoreOrdersView orders={[order]} busy={false} onStatusChange={vi.fn()} />);
    expect(screen.getByText('WEB-20260812-ABCD1234')).toBeInTheDocument();
    expect(screen.getByText('Ana López')).toBeInTheDocument();
    expect(screen.getByText(/2 × filtro de aceite/i)).toBeInTheDocument();
    expect(screen.getByText(/pendiente de confirmación/i)).toBeInTheDocument();
  });

  it('requires an ERPNext reference before marking an order as synced', async () => {
    const user = userEvent.setup();
    const onStatusChange = vi.fn();
    render(<StoreOrdersView orders={[order]} busy={false} onStatusChange={onStatusChange} />);

    await user.click(screen.getByRole('button', { name: /web-20260812-abcd1234 ana lópez/i }));
    await user.selectOptions(screen.getByLabelText(/estado de web-20260812-abcd1234/i), 'SYNCED');
    await user.click(screen.getByRole('button', { name: /guardar estado/i }));

    expect(onStatusChange).not.toHaveBeenCalled();
    expect(screen.getByText(/ingrese la orden de venta de erpnext/i)).toBeInTheDocument();
  });
});
