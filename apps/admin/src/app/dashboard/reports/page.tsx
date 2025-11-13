'use client';

import { useEffect, useState } from 'react';
import { dashboard as dashboardApi } from '@ecommerce/sdk';
import { Card, CardHeader, CardTitle, CardContent } from '@ecommerce/ui';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SummaryData {
  totalSales: number;
  otsCompletadas: number;
  totalClientes: number;
  totalProductos: number;
}

const exampleData = [
  { name: 'Ene', Ventas: 4000 },
  { name: 'Feb', Ventas: 3000 },
  { name: 'Mar', Ventas: 5000 },
];

export default function ReportsPage() {
  const [summary, setSummary] = useState<SummaryData | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await dashboardApi.getSummary();
        setSummary(data);
      } catch (error) {
        console.error('Failed to fetch summary data', error);
      }
    };
    fetchSummary();
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard Principal</h1>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader><CardTitle>Ventas Totales</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">L {summary?.totalSales.toFixed(2) || '0.00'}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>OTs Completadas</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">{summary?.otsCompletadas || 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Clientes Registrados</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">{summary?.totalClientes || 0}</p></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Productos Activos</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-bold">{summary?.totalProductos || 0}</p></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Ventas Mensuales (Ejemplo)</CardTitle></CardHeader>
        <CardContent style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <BarChart data={exampleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Ventas" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
