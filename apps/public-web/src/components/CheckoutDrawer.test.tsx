import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CheckoutDrawer } from './CheckoutDrawer';
import { createStoreOrder } from '../lib/api';
import type { Product } from '../types';

vi.mock('../lib/api', () => ({ createStoreOrder: vi.fn() }));

const product: Product = {
  id: 'product-1',
  sku: 'FL-001',
  name: 'Filtro de aceite',
  description: 'Filtro de prueba',
  brand: 'Motorcraft',
  category_id: null,
  display_price: '350.00',
  currency: 'HNL',
  stock_status: 'IN_STOCK',
  compatibility_note: 'Validar por VIN',
  erpnext_item_code: null,
  published: true,
  active: true,
  images: [],
};

describe('CheckoutDrawer', () => {
  beforeEach(() => {
    vi.mocked(createStoreOrder).mockReset();
  });

  it('persists a parts order request and shows its reference', async () => {
    vi.mocked(createStoreOrder).mockResolvedValue({
      id: 'order-1',
      order_number: 'WEB-20260812-ABC12345',
      status: 'PENDING_CONFIRMATION',
      currency: 'HNL',
      subtotal: '700.00',
      items: [],
    });
    const user = userEvent.setup();

    render(
      <CheckoutDrawer
        open
        cart={[product, product]}
        onClose={() => undefined}
        onRemove={() => undefined}
        onCompleted={() => undefined}
      />,
    );

    expect(screen.getByText('2 × Filtro de aceite')).toBeInTheDocument();
    await user.type(screen.getByLabelText('Nombre completo'), 'Luis Rivera');
    await user.type(screen.getByLabelText('Teléfono'), '+504 9999-9999');
    await user.type(screen.getByLabelText('VIN (opcional)'), '1FMCU0GDXLUA00001');
    await user.click(screen.getByRole('button', { name: 'Enviar solicitud de pedido' }));

    await waitFor(() => expect(createStoreOrder).toHaveBeenCalledTimes(1));
    expect(vi.mocked(createStoreOrder).mock.calls[0][0].items).toEqual([
      { product_id: 'product-1', quantity: 2 },
    ]);
    expect(await screen.findByText('WEB-20260812-ABC12345')).toBeInTheDocument();
  });
});
