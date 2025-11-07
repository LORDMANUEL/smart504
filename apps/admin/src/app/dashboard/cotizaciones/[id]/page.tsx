'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { cotizaciones as cotizacionesApi, ordenesTrabajo as otApi, Cotizacion } from '@ecommerce/sdk';
import { Button, Card, CardHeader, CardTitle, CardContent } from '@ecommerce/ui';
import { PDFDownloadLink } from '@react-pdf/renderer';
import { CotizacionPDF } from '../../../components/CotizacionPDF';
import { useRouter } from 'next/navigation';

export default function EditCotizacionPage() {
  const [cotizacion, setCotizacion] = useState<Cotizacion | null>(null);
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();

  const handleConvertToOT = async () => {
    if (!cotizacion) return;
    try {
      const nuevaOT = await otApi.create({
        cotizacionId: cotizacion.id,
        vehiculo: cotizacion.vehiculo as any,
      });
      router.push(`/dashboard/ordenes-trabajo/${nuevaOT.id}`);
    } catch (error) {
      console.error("Failed to convert to OT", error);
      // Show an error message to the user
    }
  };

  useEffect(() => {
    const fetchCotizacion = async () => {
      try {
        const data = await cotizacionesApi.getOne(id);
        setCotizacion(data);
      } catch (error) {
        console.error('Failed to fetch cotizacion', error);
      }
    };
    if (id) {
      fetchCotizacion();
    }
  }, [id]);

  if (!cotizacion) {
    return <div>Cargando cotización...</div>;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row justify-between items-center">
        <CardTitle>Detalles de la Cotización #{cotizacion.id.substring(0, 8)}</CardTitle>
        <div className="flex gap-2">
          <PDFDownloadLink
            document={<CotizacionPDF cotizacion={cotizacion} />}
            fileName={`cotizacion-${cotizacion.id}.pdf`}
          >
            {({ loading }) => (
              <Button disabled={loading} variant="ghost">
                {loading ? 'Generando PDF...' : 'Descargar PDF'}
              </Button>
            )}
          </PDFDownloadLink>
          <Button onClick={handleConvertToOT}>Convertir a OT</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="font-bold text-lg mb-2">Vehículo</h3>
          <p>{(cotizacion.vehiculo as any).marca} {(cotizacion.vehiculo as any).modelo} {(cotizacion.vehiculo as any).anio}</p>
        </div>
        <div>
          <h3 className="font-bold text-lg mb-2">Partes</h3>
          <Table>
            <TableHeader><TableRow><TableHead>Nombre</TableHead><TableHead>Cantidad</TableHead><TableHead>Precio</TableHead><TableHead>Subtotal</TableHead></TableRow></TableHeader>
            <TableBody>
              {(cotizacion.lineasPartes as any[]).map((p, i) => (
                <TableRow key={i}>
                  <TableCell>{p.nombre}</TableCell>
                  <TableCell>{p.cantidad}</TableCell>
                  <TableCell>L {p.precio.toFixed(2)}</TableCell>
                  <TableCell>L {(p.cantidad * p.precio).toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div>
          <h3 className="font-bold text-lg mb-2">Mano de Obra</h3>
           <Table>
            <TableHeader><TableRow><TableHead>Descripción</TableHead><TableHead>Tiempo</TableHead><TableHead>Costo</TableHead></TableRow></TableHeader>
            <TableBody>
              {(cotizacion.lineasManoObra as any[]).map((m, i) => (
                <TableRow key={i}>
                  <TableCell>{m.descripcion}</TableCell>
                  <TableCell>{m.tiempo}h</TableCell>
                  <TableCell>L {m.costo.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold">Total: L {cotizacion.total.toFixed(2)}</p>
        </div>
      </CardContent>
    </Card>
  );
}
