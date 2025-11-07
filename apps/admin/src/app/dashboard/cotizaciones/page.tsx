'use client';

import { useEffect, useState } from 'react';
import { cotizaciones as cotizacionesApi, Cotizacion } from '@ecommerce/sdk';
import { Button, Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@ecommerce/ui';
import Link from 'next/link';

export default function CotizacionesPage() {
  const [cotizaciones, setCotizaciones] = useState<Cotizacion[]>([]);

  useEffect(() => {
    const fetchCotizaciones = async () => {
      try {
        const data = await cotizacionesApi.getAll();
        setCotizaciones(data);
      } catch (error) {
        console.error('Failed to fetch cotizaciones', error);
      }
    };
    fetchCotizaciones();
  }, []);

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Gestión de Cotizaciones</h1>
        <Button asChild>
          <Link href="/dashboard/cotizaciones/new">Crear Cotización</Link>
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Vehículo</TableHead>
            <TableHead>Total</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Fecha</TableHead>
            <TableHead>Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {cotizaciones.map((cotizacion) => (
            <TableRow key={cotizacion.id}>
              <TableCell className="font-mono text-xs">{cotizacion.id}</TableCell>
              <TableCell>{`${(cotizacion.vehiculo as any).marca} ${(cotizacion.vehiculo as any).modelo}`}</TableCell>
              <TableCell>L {cotizacion.total.toFixed(2)}</TableCell>
              <TableCell>{cotizacion.estado}</TableCell>
              <TableCell>{new Date(cotizacion.createdAt).toLocaleDateString()}</TableCell>
              <TableCell>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/dashboard/cotizaciones/${cotizacion.id}`}>Ver/Editar</Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
