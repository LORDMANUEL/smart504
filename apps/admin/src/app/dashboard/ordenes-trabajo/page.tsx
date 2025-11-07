'use client';

import { useEffect, useState } from 'react';
import { ordenesTrabajo as otApi, WorkOrder } from '@ecommerce/sdk';
import { Button, Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@ecommerce/ui';
import Link from 'next/link';

export default function OrdenesTrabajoPage() {
  const [ordenes, setOrdenes] = useState<WorkOrder[]>([]);

  useEffect(() => {
    const fetchOrdenes = async () => {
      try {
        const data = await otApi.getAll();
        setOrdenes(data);
      } catch (error) {
        console.error('Failed to fetch ordenes de trabajo', error);
      }
    };
    fetchOrdenes();
  }, []);

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Órdenes de Trabajo</h1>
        {/* The primary creation path is from a quote, but a direct link can exist */}
        <Button asChild>
          <Link href="/dashboard/ordenes-trabajo/new">Crear OT Manual</Link>
        </Button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Vehículo</TableHead>
            <TableHead>Técnico</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Fecha</TableHead>
            <TableHead>Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {ordenes.map((orden) => (
            <TableRow key={orden.id}>
              <TableCell className="font-mono text-xs">{orden.id}</TableCell>
              <TableCell>{`${(orden.vehiculo as any).marca} ${(orden.vehiculo as any).modelo}`}</TableCell>
              <TableCell>{orden.tecnicoAsignadoId || 'No asignado'}</TableCell>
              <TableCell>{orden.estado}</TableCell>
              <TableCell>{new Date(orden.createdAt).toLocaleDateString()}</TableCell>
              <TableCell>
                <Button variant="ghost" size="sm" asChild>
                  <Link href={`/dashboard/ordenes-trabajo/${orden.id}`}>Gestionar</Link>
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
