import { FormEvent, useMemo, useState } from 'react';
import { CheckCircle2, LoaderCircle, Minus, PackageCheck, X } from 'lucide-react';
import { createStoreOrder } from '../lib/api';
import type { Product, StoreOrder } from '../types';

type CheckoutDrawerProps = {
  open: boolean;
  cart: Product[];
  onClose: () => void;
  onRemove: (productId: string) => void;
  onCompleted: (order: StoreOrder) => void;
  initialPromoCode?: string;
};

function formatMoney(value: number | string, currency = 'HNL') {
  return new Intl.NumberFormat('es-HN', { style: 'currency', currency }).format(Number(value));
}

export function CheckoutDrawer({ open, cart, onClose, onRemove, onCompleted, initialPromoCode = '' }: CheckoutDrawerProps) {
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [createdOrder, setCreatedOrder] = useState<StoreOrder | null>(null);

  const lines = useMemo(() => {
    const grouped = new Map<string, { product: Product; quantity: number }>();
    for (const product of cart) {
      const current = grouped.get(product.id);
      grouped.set(product.id, { product, quantity: (current?.quantity ?? 0) + 1 });
    }
    return Array.from(grouped.values());
  }, [cart]);

  const total = useMemo(
    () => lines.reduce((sum, line) => sum + Number(line.product.display_price) * line.quantity, 0),
    [lines],
  );

  if (!open) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (lines.length === 0) {
      setState('error');
      setMessage('Agregue al menos un repuesto antes de enviar la solicitud.');
      return;
    }
    const form = new FormData(event.currentTarget);
    setState('sending');
    setMessage('');
    try {
      const order = await createStoreOrder({
        customer_name: String(form.get('customer_name') ?? ''),
        phone: String(form.get('phone') ?? ''),
        email: String(form.get('email') ?? '') || undefined,
        vehicle_vin: String(form.get('vehicle_vin') ?? '') || undefined,
        notes: String(form.get('notes') ?? '') || undefined,
        promo_code: String(form.get('promo_code') ?? '') || undefined,
        idempotency_key: crypto.randomUUID(),
        items: lines.map((line) => ({ product_id: line.product.id, quantity: line.quantity })),
      });
      setCreatedOrder(order);
      setState('sent');
      onCompleted(order);
    } catch (error) {
      setState('error');
      setMessage(error instanceof Error ? error.message : 'No fue posible enviar la solicitud.');
    }
  }

  return (
    <div className="checkout-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.currentTarget === event.target) onClose();
    }}>
      <aside className="checkout-drawer" role="dialog" aria-modal="true" aria-labelledby="checkout-title">
        <header className="checkout-drawer__header">
          <div>
            <small>Tienda SmartDiag504</small>
            <h2 id="checkout-title">Solicitud de repuestos</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Cerrar pedido"><X /></button>
        </header>

        {state === 'sent' && createdOrder ? (
          <div className="checkout-success" role="status">
            <CheckCircle2 size={44} />
            <h3>Solicitud recibida</h3>
            <p>La referencia de su pedido es:</p>
            <strong>{createdOrder.order_number}</strong>
            <p>Validaremos existencia, compatibilidad por VIN y forma de entrega antes de facturar.</p>
            <button className="button button--gold" type="button" onClick={onClose}>Cerrar</button>
          </div>
        ) : (
          <form onSubmit={submit} className="checkout-form">
            <div className="checkout-lines">
              {lines.map(({ product, quantity }) => (
                <div className="checkout-line" key={product.id}>
                  <div>
                    <strong>{quantity} × {product.name}</strong>
                    <span>{product.sku} · {formatMoney(product.display_price, product.currency)}</span>
                  </div>
                  <button type="button" onClick={() => onRemove(product.id)} aria-label={`Quitar ${product.name}`}>
                    <Minus size={16} />
                  </button>
                </div>
              ))}
            </div>
            <div className="checkout-total"><span>Subtotal estimado</span><strong>{formatMoney(total)}</strong></div>
            <label className="checkout-promo">Código de descuento<input name="promo_code" defaultValue={initialPromoCode} maxLength={40} autoCapitalize="characters" placeholder="Ej. PATRIA504" /></label>
            <p className="checkout-note"><PackageCheck size={17} /> El pedido queda pendiente de confirmación. No se descuenta inventario ni se factura hasta validarlo con el equipo.</p>

            <div className="checkout-fields">
              <label>Nombre completo<input name="customer_name" required autoComplete="name" /></label>
              <label>Teléfono<input name="phone" required autoComplete="tel" /></label>
              <label>Correo (opcional)<input name="email" type="email" autoComplete="email" /></label>
              <label>VIN (opcional)<input name="vehicle_vin" maxLength={40} autoCapitalize="characters" /></label>
              <label className="checkout-fields__wide">Notas<textarea name="notes" rows={3} placeholder="Modelo, año, retiro en taller o consulta adicional" /></label>
            </div>
            <button className="button button--gold checkout-submit" type="submit" disabled={state === 'sending'}>
              {state === 'sending' ? <LoaderCircle className="spin" size={18} /> : <PackageCheck size={18} />}
              Enviar solicitud de pedido
            </button>
            {message && <p className="form-message form-message--error" role="alert">{message}</p>}
          </form>
        )}
      </aside>
    </div>
  );
}
