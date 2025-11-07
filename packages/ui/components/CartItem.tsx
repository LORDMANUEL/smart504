import * as React from 'react';
import { cn } from '../lib/utils';
import { Button } from './Button';
import { Input } from './Input';

interface CartItemProps {
  item: {
    productoId: string;
    nombre: string;
    precio: number;
    cantidad: number;
    sku: string;
    // Assuming you'll add an image URL to the cart item payload
    imageUrl?: string;
  };
  onUpdateQuantity: (productoId: string, cantidad: number) => void;
  onRemove: (productoId: string) => void;
  className?: string;
}

const CartItem = React.forwardRef<HTMLDivElement, CartItemProps>(
  ({ item, onUpdateQuantity, onRemove, className }, ref) => {
    return (
      <div ref={ref} className={cn('flex items-center gap-4 p-4 rounded-lg bg-gray-100 shadow-md', className)}>
        <img
          src={item.imageUrl || 'https://via.placeholder.com/100'}
          alt={item.nombre}
          className="w-24 h-24 object-cover rounded-md"
        />
        <div className="flex-grow">
          <p className="font-bold">{item.nombre}</p>
          <p className="text-sm text-gray-600">SKU: {item.sku}</p>
          <p className="text-lg font-semibold">L {item.precio.toFixed(2)}</p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min="1"
            value={item.cantidad}
            onChange={(e) => onUpdateQuantity(item.productoId, parseInt(e.target.value, 10))}
            className="w-20 text-center"
          />
        </div>
        <p className="text-lg font-bold w-24 text-right">
          L {(item.precio * item.cantidad).toFixed(2)}
        </p>
        <Button variant="destructive" size="icon" onClick={() => onRemove(item.productoId)}>
          X
        </Button>
      </div>
    );
  }
);
CartItem.displayName = 'CartItem';

export { CartItem };
