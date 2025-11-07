'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { productos as productosApi, Producto } from '@ecommerce/sdk';
import { Button, Card, CardContent, CardHeader, CardTitle } from '@ecommerce/ui';

export default function ProductoDetailPage() {
  const [producto, setProducto] = useState<Producto | null>(null);
  const params = useParams();
  const id = params.id as string;

  useEffect(() => {
    const fetchProducto = async () => {
      try {
        const productData = await productosApi.getOne(id);
        setProducto(productData);
      } catch (error) {
        console.error('Failed to fetch product', error);
      }
    };
    if (id) {
      fetchProducto();
    }
  }, [id]);

  if (!producto) return <div>Loading...</div>;

  const images = JSON.parse(producto.fotos || '[]');
  const compatibilidad = JSON.parse(producto.compatibilidad || '[]');

  return (
    <Card>
      <CardContent className="grid md:grid-cols-2 gap-8 p-8">
        <div>
          <img src={images[0] || 'https://via.placeholder.com/400'} alt={producto.nombre} className="w-full rounded-lg" />
          {/* Add a gallery for multiple images here */}
        </div>
        <div>
          <h1 className="text-3xl font-bold mb-4">{producto.nombre}</h1>
          <p className="text-gray-600 mb-2">SKU: {producto.sku}</p>
          <p className="text-gray-600 mb-4">OEM: {producto.oem || 'N/A'}</p>
          <p className="text-4xl font-bold mb-6">L {producto.precioBase.toFixed(2)}</p>
          <p className="mb-6">{producto.descripcion}</p>
          <Button size="lg" className="w-full">Agregar al Carrito</Button>
        </div>
      </CardContent>

      {compatibilidad.length > 0 && (
        <CardContent className="p-8 border-t">
          <CardTitle className="mb-4">Compatibilidad de Vehículo</CardTitle>
          <ul>
            {compatibilidad.map((v: any, i: number) => (
              <li key={i} className="text-gray-700">{v.marca} {v.modelo} {v.anio} ({v.motor})</li>
            ))}
          </ul>
        </CardContent>
      )}
    </Card>
  );
}
