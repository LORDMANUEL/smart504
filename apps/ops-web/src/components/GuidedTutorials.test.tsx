import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { GuidedTutorials } from './GuidedTutorials';
import { GuidedOnboarding } from './GuidedOnboarding';

describe('GuidedTutorials', () => {
  beforeEach(() => localStorage.clear());

  it('moves through a role guide and remembers completed steps', async () => {
    const user = userEvent.setup();
    render(<GuidedTutorials />);

    expect(screen.getByRole('heading', { name: 'Guía interactiva SmartDiag504' })).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /marcar completado/i }));
    expect(screen.getByText('25%')).toBeInTheDocument();
    expect(localStorage.getItem('smartdiag-guide-progress:owner')).toBe('[0]');
    await user.click(screen.getByRole('button', { name: /siguiente/i }));
    expect(screen.getByRole('heading', { name: 'Crear personal SmartDiag' })).toBeInTheDocument();
  });

  it('exposes the storefront and ERP administrative links', () => {
    render(<GuidedTutorials />);
    expect(screen.getByRole('link', { name: /tienda de repuestos/i })).toHaveAttribute('href', '/lading/repuestos');
    expect(screen.getByRole('link', { name: /erpnext administrativo/i })).toHaveAttribute('href', 'https://erp.nexusmedi.org/app');
  });
});

describe('GuidedOnboarding', () => {
  it('teaches the cashier flow and can be skipped', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<GuidedOnboarding role="CASHIER" open onClose={onClose} />);
    expect(screen.getByRole('heading', { name: 'Mostrador y caja' })).toBeInTheDocument();
    expect(screen.getByText(/solicitud a compras/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /omitir recorrido/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });
});
