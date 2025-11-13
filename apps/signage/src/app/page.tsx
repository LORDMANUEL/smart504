'use client';

import { useEffect, useState } from 'react';
import { ordenesTrabajo as otApi, WorkOrder } from '@ecommerce/sdk';
import { Card, CardHeader, CardTitle, CardContent } from '@ecommerce/ui';
import { WorkOrderStatus } from '@prisma/client';

export default function SignagePage() {
  const [ordenes, setOrdenes] = useState<WorkOrder[]>([]);

  const fetchOrdenes = async () => {
    try {
      const data = await otApi.getAll();
      // Filter for relevant statuses to display
      const filtered = data.filter((ot: WorkOrder) =>
        [WorkOrderStatus.EN_REPARACION, WorkOrderStatus.FINALIZADO].includes(ot.estado)
      );
      setOrdenes(filtered);
    } catch (error) {
      console.error('Failed to fetch work orders', error);
    }
  };

  useEffect(() => {
    fetchOrdenes();
    const interval = setInterval(fetchOrdenes, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const enReparacion = ordenes.filter(o => o.estado === WorkOrderStatus.EN_REPARACION);
  const listosParaRetirar = ordenes.filter(o => o.estado === WorkOrderStatus.FINALIZADO);

  return (
    <main className="min-h-screen bg-gray-900 text-white p-8 grid grid-cols-2 gap-8">
      <div>
        <h1 className="text-4xl font-bold mb-6 text-center text-yellow-400">En Reparación</h1>
        <div className="space-y-4">
          {enReparacion.map(ot => (
            <Card key={ot.id} className="bg-gray-800 border-yellow-400 border-2">
              <CardContent className="p-4">
                <p className="text-xl font-bold">{(ot.vehiculo as any)?.marca} {(ot.vehiculo as any)?.modelo}</p>
                <p className="text-sm text-gray-400">ID: ...{ot.id.slice(-6)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
      <div>
        <h1 className="text-4xl font-bold mb-6 text-center text-green-400">Listo para Retirar</h1>
        <div className="space-y-4">
          {listosParaRetirar.map(ot => (
            <Card key={ot.id} className="bg-gray-800 border-green-400 border-2">
              <CardContent className="p-4">
                <p className="text-xl font-bold">{(ot.vehiculo as any)?.marca} {(ot.vehiculo as any)?.modelo}</p>
                 <p className="text-sm text-gray-400">ID: ...{ot.id.slice(-6)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </main>
  );
}
