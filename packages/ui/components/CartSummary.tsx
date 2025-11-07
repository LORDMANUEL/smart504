import * as React from 'react';
import { cn } from '../lib/utils';
import { Button } from './Button';
import { Card, CardContent, CardHeader, CardTitle } from './Card';

interface CartSummaryProps {
  subtotal: number;
  impuestos: number;
  total: number;
  className?: string;
}

const CartSummary = React.forwardRef<HTMLDivElement, CartSummaryProps>(
  ({ subtotal, impuestos, total, className }, ref) => {
    return (
      <Card ref={ref} className={cn('p-6', className)}>
        <CardHeader>
          <CardTitle>Resumen de la Orden</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex justify-between">
            <span>Subtotal</span>
            <span>L {subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span>Impuestos</span>
            <span>L {impuestos.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold text-lg">
            <span>Total</span>
            <span>L {total.toFixed(2)}</span>
          </div>
          <Button size="lg" className="w-full mt-4">
            Proceder al Pago
          </Button>
        </CardContent>
      </Card>
    );
  }
);
CartSummary.displayName = 'CartSummary';

export { CartSummary };
