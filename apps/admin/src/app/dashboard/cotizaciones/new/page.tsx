'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { cotizaciones as cotizacionesApi, productos as productosApi, CreateCotizacionDto, Producto } from '@ecommerce/sdk';
import { Button, Input, Card, CardHeader, CardTitle, CardContent, CardFooter, Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@ecommerce/ui';

// Define the types for the form lines locally for simplicity
type LineaParte = { productoId: string; nombre: string; sku: string; cantidad: number; precio: number; };
type LineaManoObra = { descripcion: string; tiempo: number; costo: number; };

export default function NewCotizacionPage() {
  const [vehiculo, setVehiculo] = useState({ marca: '', modelo: '', anio: '' });
  const [lineasPartes, setLineasPartes] = useState<LineaParte[]>([]);
  const [lineasManoObra, setLineasManoObra] = useState<LineaManoObra[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<Producto[]>([]);

  const router = useRouter();

  const handleParteChange = (index: number, field: keyof LineaParte, value: any) => {
    const updated = [...lineasPartes];
    updated[index] = { ...updated[index], [field]: value };
    setLineasPartes(updated);
  };

  const handleManoDeObraChange = (index: number, field: keyof LineaManoObra, value: any) => {
    const updated = [...lineasManoDeObra];
    updated[index] = { ...updated[index], [field]: value };
    setLineasManoDeObra(updated);
  };

  const handleSearch = async () => {
    if (!searchTerm) return;
    const result = await productosApi.getAll({ search: searchTerm, limit: '5' });
    setSearchResults(result.data);
  };

  const addParte = (producto: Producto) => {
    setLineasPartes(prev => [...prev, {
      productoId: producto.id,
      nombre: producto.nombre,
      sku: producto.sku,
      cantidad: 1,
      precio: producto.precioBase
    }]);
  };

  const addManoDeObra = () => {
    setLineasManoObra(prev => [...prev, { descripcion: 'Nuevo Servicio', tiempo: 1, costo: 100 }]);
  }

  const handleCreate = async () => {
    const dto: CreateCotizacionDto = {
      vehiculo,
      lineasPartes: lineasPartes.map(({ productoId, cantidad, precio }) => ({ productoId, cantidad, precio })),
      lineasManoObra,
    };
    try {
      await cotizacionesApi.create(dto);
      router.push('/dashboard/cotizaciones');
    } catch (error) {
      console.error("Failed to create cotizacion", error);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><CardTitle>Información del Vehículo</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-3 gap-4">
          <Input placeholder="Marca" value={vehiculo.marca} onChange={e => setVehiculo(v => ({...v, marca: e.target.value}))} />
          <Input placeholder="Modelo" value={vehiculo.modelo} onChange={e => setVehiculo(v => ({...v, modelo: e.target.value}))} />
          <Input placeholder="Año" value={vehiculo.anio} onChange={e => setVehiculo(v => ({...v, anio: e.target.value}))} />
        </CardContent>
      </Card>

      {/* Partes */}
      <Card>
        <CardHeader><CardTitle>Partes y Repuestos</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <Input placeholder="Buscar por SKU, nombre..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
            <Button onClick={handleSearch}>Buscar</Button>
          </div>
          {searchResults.length > 0 && (
            <ul className="border rounded-lg p-2 mb-4">
              {searchResults.map(p => <li key={p.id} className="flex justify-between items-center p-1"><span>{p.nombre} ({p.sku})</span><Button size="sm" onClick={() => addParte(p)}>Añadir</Button></li>)}
            </ul>
          )}
          <Table>
            <TableHeader><TableRow><TableHead>SKU</TableHead><TableHead>Nombre</TableHead><TableHead>Cantidad</TableHead><TableHead>Precio</TableHead><TableHead>Subtotal</TableHead></TableRow></TableHeader>
            <TableBody>
              {lineasPartes.map((linea, index) => (
                <TableRow key={index}>
                  <TableCell>{linea.sku}</TableCell>
                  <TableCell>{linea.nombre}</TableCell>
                  <TableCell><Input type="number" value={linea.cantidad} onChange={e => handleParteChange(index, 'cantidad', parseInt(e.target.value) || 0)} className="w-20" /></TableCell>
                  <TableCell><Input type="number" value={linea.precio} onChange={e => handleParteChange(index, 'precio', parseFloat(e.target.value) || 0)} className="w-24" /></TableCell>
                  <TableCell>L {(linea.cantidad * linea.precio).toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Mano de Obra */}
      <Card>
        <CardHeader className="flex flex-row justify-between items-center">
            <CardTitle>Mano de Obra</CardTitle>
            <Button onClick={addManoDeObra}>Añadir Servicio</Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader><TableRow><TableHead>Descripción</TableHead><TableHead>Tiempo (H)</TableHead><TableHead>Costo</TableHead></TableRow></TableHeader>
            <TableBody>
              {lineasManoObra.map((linea, index) => (
                <TableRow key={index}>
                  <TableCell><Input value={linea.descripcion} onChange={e => handleManoDeObraChange(index, 'descripcion', e.target.value)} /></TableCell>
                  <TableCell><Input type="number" value={linea.tiempo} onChange={e => handleManoDeObraChange(index, 'tiempo', parseFloat(e.target.value) || 0)} className="w-20" /></TableCell>
                  <TableCell><Input type="number" value={linea.costo} onChange={e => handleManoDeObraChange(index, 'costo', parseFloat(e.target.value) || 0)} className="w-24" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={() => router.back()}>Cancelar</Button>
        <Button onClick={handleCreate}>Guardar Cotización</Button>
      </div>
    </div>
  );
}
