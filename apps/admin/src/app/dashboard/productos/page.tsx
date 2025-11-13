'use client';

import { useEffect, useState } from 'react';
import { productos as productosApi, Producto } from '@ecommerce/sdk';
import { Button, Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@ecommerce/ui';
import Link from 'next/link';
import { unparse } from 'papaparse';

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

  const handleExport = () => {
    const csv = unparse(productos);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'productos.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Product Management</h1>
        <div className="flex gap-2">
          <Button onClick={handleExport} variant="ghost">Exportar a CSV</Button>
          <Button asChild>
            <Link href="/dashboard/productos/new">Create Product</Link>
          </Button>
        </div>
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
