'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { productos as productosApi, CreateProductoDto } from '@ecommerce/sdk';
import { Button, Input, Card, CardHeader, CardTitle, CardContent, CardFooter } from '@ecommerce/ui';

export default function NewProductoPage() {
  const [formData, setFormData] = useState<CreateProductoDto>({
    sku: '',
    nombre: '',
    marca: '',
    categoria: '',
    precioBase: 0,
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await productosApi.create(formData);
      router.push('/dashboard/productos');
    } catch (err) {
      setError('Failed to create product. Please check the details.');
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Product</CardTitle>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Input name="sku" placeholder="SKU" value={formData.sku} onChange={handleChange} required />
          <Input name="nombre" placeholder="Name" value={formData.nombre} onChange={handleChange} required />
          <Input name="marca" placeholder="Brand" value={formData.marca} onChange={handleChange} required />
          <Input name="categoria" placeholder="Category" value={formData.categoria} onChange={handleChange} required />
          <Input name="precioBase" type="number" placeholder="Price" value={formData.precioBase} onChange={handleChange} required />
          <Input name="oem" placeholder="OEM (Optional)" value={formData.oem || ''} onChange={handleChange} />
          <textarea name="descripcion" placeholder="Description (Optional)" value={formData.descripcion || ''} onChange={handleChange} className="w-full h-24 p-3 rounded-lg bg-gray-100 shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff] md:col-span-2" />
        </CardContent>
        <CardFooter className="flex justify-end space-x-2">
          <Button type="button" variant="ghost" onClick={() => router.back()}>Cancel</Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Product'}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
