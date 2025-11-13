import * as React from 'react';
import { cn } from '../lib/utils';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './Card';
import { Button } from './Button';

interface ProductCardProps {
  product: {
    id: string;
    nombre: string;
    precioBase: number;
    fotos: string; // JSON string of URLs
    // Add other product properties as needed
  };
  className?: string;
}

const ProductCard = React.forwardRef<HTMLDivElement, ProductCardProps>(
  ({ product, className }, ref) => {
    const imageUrl = JSON.parse(product.fotos || '[]')[0] || 'https://via.placeholder.com/150';

    return (
      <Card ref={ref} className={cn('flex flex-col', className)}>
        <CardHeader>
          <img src={imageUrl} alt={product.nombre} className="w-full h-48 object-cover rounded-t-lg" />
        </CardHeader>
        <CardContent className="flex-grow">
          <CardTitle className="text-base font-semibold">{product.nombre}</CardTitle>
          <p className="text-lg font-bold mt-2">L {product.precioBase.toFixed(2)}</p>
        </CardContent>
        <CardFooter>
          <Button className="w-full">Ver Detalles</Button>
        </CardFooter>
      </Card>
    );
  }
);
ProductCard.displayName = 'ProductCard';

export { ProductCard };
