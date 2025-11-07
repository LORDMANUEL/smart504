'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ordenesTrabajo as otApi, WorkOrder, User, users as usersApi } from '@ecommerce/sdk';
import { Button, Card, CardHeader, CardTitle, CardContent } from '@ecommerce/ui';
import { WorkOrderStatus, UserRole } from '@prisma/client';

export default function GestionOTPage() {
  const [orden, setOrden] = useState<WorkOrder | null>(null);
  const [tecnicos, setTecnicos] = useState<User[]>([]);
  const params = useParams();
  const id = params.id as string;

  const fetchData = async () => {
    if (!id) return;
    try {
      const [ordenData, allUsers] = await Promise.all([
        otApi.getOne(id),
        usersApi.getAll()
      ]);
      setOrden(ordenData);
      setTecnicos(allUsers.filter((u: User) => u.role === UserRole.TECNICO));
    } catch (error) {
      console.error('Failed to fetch data', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleUpdateStatus = async (estado: WorkOrderStatus) => {
    await otApi.update(id, { estado });
    // Refresh data
  };

  const handleAssignTecnico = async (tecnicoId: string) => {
    await otApi.update(id, { tecnicoAsignadoId: tecnicoId });
    fetchData(); // Refresh data
  };

  const handleConsumir = async (parte: any) => {
    if (window.confirm(`¿Confirmas el consumo de ${parte.cantidad}x ${parte.nombre}? Esta acción descontará el stock.`)) {
      try {
        await otApi.update(id, {
          consumosInventario: [{ productoId: parte.productoId, cantidad: parte.cantidad }]
        });
        // We could update the UI to show it's consumed, for now, we just alert.
        alert("Stock consumido con éxito.");
        fetchData(); // Refresh data
      } catch (error) {
        console.error("Failed to consume stock", error);
        alert("Error al consumir el stock. Es posible que no haya suficientes existencias.");
      }
    }
  };

  if (!orden) return <div>Cargando Orden de Trabajo...</div>;

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="md:col-span-2 space-y-6">
        <Card>
          <CardHeader><CardTitle>Detalles de la OT #{orden.id.substring(0,8)}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-bold">Vehículo</h4>
              <p>{orden.vehiculo ? `${(orden.vehiculo as any).marca} ${(orden.vehiculo as any).modelo} ${(orden.vehiculo as any).anio}` : 'N/A'}</p>
            </div>
             <div>
              <h4 className="font-bold mt-4">Líneas de Partes</h4>
              <Table>
                <TableHeader><TableRow><TableHead>Nombre</TableHead><TableHead>Cantidad</TableHead></TableRow></TableHeader>
                <TableBody>
                  {(orden.lineas as any)?.partes?.map((p: any, i: number) => (
                    <TableRow key={i}><TableCell>{p.nombre}</TableCell><TableCell>{p.cantidad}</TableCell></TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
             <div>
              <h4 className="font-bold mt-4">Líneas de Mano de Obra</h4>
              <Table>
                <TableHeader><TableRow><TableHead>Descripción</TableHead><TableHead>Tiempo</TableHead></TableRow></TableHeader>
                <TableBody>
                  {(orden.lineas as any)?.manoObra?.map((m: any, i: number) => (
                    <TableRow key={i}><TableCell>{m.descripcion}</TableCell><TableCell>{m.tiempo}h</TableCell></TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Consumo de Inventario</CardTitle></CardHeader>
          <CardContent>
            <Table>
                <TableHeader><TableRow><TableHead>SKU</TableHead><TableHead>Nombre</TableHead><TableHead>Cantidad</TableHead><TableHead>Acción</TableHead></TableRow></TableHeader>
                <TableBody>
                  {(orden.lineas as any)?.partes?.map((parte: any) => (
                    <TableRow key={parte.productoId}>
                      <TableCell>{parte.sku}</TableCell>
                      <TableCell>{parte.nombre}</TableCell>
                      <TableCell>{parte.cantidad}</TableCell>
                      <TableCell>
                        <Button size="sm" onClick={() => handleConsumir(parte)}>Consumir</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
      <div className="space-y-6">
        <Card>
          <CardHeader><CardTitle>Gestión</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label>Estado Actual: <strong>{orden.estado}</strong></label>
              <select onChange={e => handleUpdateStatus(e.target.value as WorkOrderStatus)} className="w-full mt-2">
                {Object.values(WorkOrderStatus).map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label>Técnico Asignado</label>
               <select onChange={e => handleAssignTecnico(e.target.value)} className="w-full mt-2">
                <option>Sin asignar</option>
                {tecnicos.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
