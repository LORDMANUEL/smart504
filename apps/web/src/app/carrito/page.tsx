'use client';

import { useCartStore } from '../stores/cartStore';
import { CartItem, CartSummary, Button } from '@ecommerce/ui';
import Link from 'next/link';

export default function CarritoPage() {
  const { cart, isLoading, updateItem, removeItem } = useCartStore();

  if (isLoading && !cart) {
    return <div>Cargando carrito...</div>;
  }

  const items = (cart?.items as any[]) || [];

  if (items.length === 0) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Tu Carrito está Vacío</h1>
        <Button asChild>
          <Link href="/catalogo">Explorar Productos</Link>
        </Button>
      </div>
    );
  }

  const subtotal = items.reduce((sum, item) => sum + item.precio * item.cantidad, 0);
  const impuestos = subtotal * 0.15; // Parametrizable
  const total = subtotal + impuestos;

  return (
    <div className="grid lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-4">
        <h1 className="text-2xl font-bold">Tu Carrito</h1>
        {items.map((item) => (
          <CartItem
            key={item.productoId}
            item={item}
            onUpdateQuantity={(productoId, cantidad) => updateItem(productoId, { cantidad })}
            onRemove={removeItem}
          />
        ))}
      </div>
      <div>
        <CartSummary subtotal={subtotal} impuestos={impuestos} total={total} />
      </div>
    </div>
  );
}
