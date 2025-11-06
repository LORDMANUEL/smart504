'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { productos as productosApi, stock as stockApi, UpdateProductoDto, Producto, Stock } from '@ecommerce/sdk';
import { Button, Input, Card, CardHeader, CardTitle, CardContent, CardFooter, Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@ecommerce/ui';

export default function EditProductoPage() {
  const [producto, setProducto] = useState<Producto & { stocks: Stock[] } | null>(null);
  const [formData, setFormData] = useState<Partial<UpdateProductoDto>>({});
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;

  useEffect(() => {
    const fetchProducto = async () => {
      try {
        const productData = await productosApi.getOne(id);
        setProducto(productData);
        setFormData(productData);
      } catch (err) {
        setError('Failed to fetch product data.');
      }
    };
    if (id) {
      fetchProducto();
    }
  }, [id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value,
    }));
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await productosApi.update(id, formData);
      router.push('/dashboard/productos');
    } catch (err) {
      setError('Failed to update product.');
      setIsLoading(false);
    }
  };

  const handleStockUpdate = async (stockItem: Stock) => {
    const newQuantity = prompt('Enter new quantity:', stockItem.cantidad.toString());
    if (newQuantity !== null) {
      const quantity = parseInt(newQuantity, 10);
      if (!isNaN(quantity)) {
        try {
          await stockApi.update(stockItem.id, { cantidad: quantity });
          // Refresh product data
          const updatedProduct = await productosApi.getOne(id);
          setProducto(updatedProduct);
        } catch (err) {
          setError('Failed to update stock.');
        }
      }
    }
  };

  if (!producto) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>Edit Product: {producto.nombre}</CardTitle>
        </CardHeader>
        <form onSubmit={handleUpdate}>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input name="sku" placeholder="SKU" value={formData.sku || ''} onChange={handleChange} required />
            <Input name="nombre" placeholder="Name" value={formData.nombre || ''} onChange={handleChange} required />
            <Input name="marca" placeholder="Brand" value={formData.marca || ''} onChange={handleChange} required />
            <Input name="categoria" placeholder="Category" value={formData.categoria || ''} onChange={handleChange} required />
            <Input name="precioBase" type="number" placeholder="Price" value={formData.precioBase || 0} onChange={handleChange} required />
            <Input name="oem" placeholder="OEM (Optional)" value={formData.oem || ''} onChange={handleChange} />
            <textarea name="descripcion" placeholder="Description (Optional)" value={formData.descripcion || ''} onChange={handleChange} className="w-full h-24 p-3 rounded-lg bg-gray-100 shadow-[inset_5px_5px_10px_#bebebe,inset_-5px_-5px_10px_#ffffff] md:col-span-2" />
          </CardContent>
          <CardFooter className="flex justify-end space-x-2">
            <Button type="button" variant="ghost" onClick={() => router.back()}>Cancel</Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Updating...' : 'Update Product'}
            </Button>
          </CardFooter>
        </form>
      </Card>

      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>Stock Management</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Warehouse</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Quantity</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {producto.stocks.map((stockItem) => (
                <TableRow key={stockItem.id}>
                  <TableCell>{stockItem.almacen}</TableCell>
                  <TableCell>{stockItem.ubicacion}</TableCell>
                  <TableCell>{stockItem.cantidad}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={() => handleStockUpdate(stockItem)}>Edit</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
