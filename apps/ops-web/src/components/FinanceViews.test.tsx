import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CashierModule, CashierView, QuotesView } from './FinanceViews';
import type { CashSummary, Quote, WorkOrderCard } from '../types';

const workOrder = {
  id: 'wo-1', external_reference: 'OT-DEMO-005', vehicle_label: 'Ford Escape 2020',
} as WorkOrderCard;

const quote = {
  id: 'quote-1', number: 'COT-DEMO-0183', work_order_id: 'wo-1', status: 'APPROVED',
  subtotal: '4585.00', discount: '0.00', tax: '0.00', total: '4585.00', lines: [], notes: null,
  created_by: 'demo', approved_by: 'demo', approved_at: '2026-08-13T12:00:00Z',
  created_at: '2026-08-13T12:00:00Z', updated_at: '2026-08-13T12:00:00Z',
} satisfies Quote;

describe('finance views', () => {
  it('configures quote lines with cost and customer price', () => {
    render(<QuotesView workOrders={[workOrder]} quotes={[]} busy={false} onCreate={vi.fn()} onStatus={vi.fn()} />);
    expect(screen.getByRole('heading', { name: /cotizaciones por vin, cliente u ot/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/^costo$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^precio$/i)).toBeInTheDocument();
  });

  it('opens cash and exposes POS only after an active session', () => {
    const onOpen = vi.fn();
    const closed = { session: null, total_collected: '0.00', totals_by_method: {}, payments: [] } as CashSummary;
    const { rerender } = render(<CashierView workOrders={[workOrder]} quotes={[quote]} summary={closed} busy={false} onOpen={onOpen} onPay={vi.fn()} onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /abrir caja/i }));
    expect(onOpen).toHaveBeenCalledWith('1000');

    const open = { ...closed, session: { id: 'cash-1', status: 'OPEN', opening_balance: '1000.00', opened_by: 'demo', closed_by: null, counted_cash: null, expected_cash: null, difference: null, opened_at: '2026-08-13T12:00:00Z', closed_at: null } } satisfies CashSummary;
    rerender(<CashierView workOrders={[workOrder]} quotes={[quote]} summary={open} busy={false} onOpen={onOpen} onPay={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('heading', { name: /cobrar ot seleccionada/i })).toBeInTheDocument();
    expect(screen.getByText(/movimientos del turno/i)).toBeInTheDocument();
    expect(screen.getByText(/arqueo y cierre/i)).toBeInTheDocument();
  });

  it('keeps the last closed reconciliation visible', () => {
    const closed = { session: { id: 'cash-1', status: 'CLOSED', opening_balance: '1000.00', opened_by: 'demo', closed_by: 'demo', counted_cash: '1000.00', expected_cash: '1000.00', difference: '0.00', opened_at: '2026-08-13T12:00:00Z', closed_at: '2026-08-13T13:00:00Z' }, total_collected: '100.00', totals_by_method: { CARD: '100.00' }, payments: [] } satisfies CashSummary;
    render(<CashierModule workOrders={[workOrder]} quotes={[quote]} summary={closed} busy={false} onOpen={vi.fn()} onPay={vi.fn()} onClose={vi.fn()} />);
    expect(screen.getByRole('heading', { name: /reporte del último turno cerrado/i })).toBeInTheDocument();
    expect(screen.getByText(/diferencia/i)).toBeInTheDocument();
  });
});
