'use client';

import { useEffect, useState } from 'react';
import { productos as productosApi, Producto } from '@ecommerce/sdk';
import { Button, Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@ecommerce/ui';
import Link from 'next/link';

export default function ProductosPage() {
  const [productos, setProductos] = useState<Producto[]>([]);

  useEffect(() => {
    const fetchProductos = async () => {
      try {
        const productList = await productosApi.getAll();
        setProductos(productList);
      } catch (error) {
        console.error('Failed to fetch productos', error);
      }
    };
    fetchProductos();
  }, []);

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Product Management</h1>
        <Button asChild>
          <Link href="/dashboard/productos/new">Create Product</Link>
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>SKU</TableHead>
            <TableHead>Name</TableHead>
            <TableHead>Brand</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Active</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {productos.map((producto) => (
            <TableRow key={producto.id}>
              <TableCell>{producto.sku}</TableCell>
              <TableCell>{producto.nombre}</TableCell>
              <TableCell>{producto.marca}</TableCell>
              <TableCell>{producto.categoria}</TableCell>
              <TableCell>{producto.precioBase}</TableCell>
              <TableCell>{producto.activo ? 'Yes' : 'No'}</TableCell>
              <TableCell>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/dashboard/productos/${producto.id}`}>Edit</Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
