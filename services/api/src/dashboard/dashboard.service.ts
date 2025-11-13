import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { WorkOrderStatus } from '@prisma/client';

@Injectable()
export class DashboardService {
  constructor(private prisma: PrismaService) {}

  async getSummary() {
    const [totalFacturado, otsCompletadas, totalClientes, totalProductos] = await this.prisma.$transaction([
        this.prisma.factura.aggregate({
            _sum: {
                // Assuming 'totales' is a JSON field with a 'total' number property
                // This is a simplified approach. A raw query might be needed if totals are complex JSON.
                // For now, let's assume we can query it directly or have a numeric total field.
                // total: true, // This won't work directly on JSON. We'll simulate.
            },
        }),
        this.prisma.ordenDeTrabajo.count({
            where: { estado: WorkOrderStatus.ENTREGADO },
        }),
        this.prisma.cliente.count(),
        this.prisma.producto.count({
            where: { activo: true },
        }),
    ]);

    // Simulate aggregation for JSON field
    const facturas = await this.prisma.factura.findMany();
    const totalSales = facturas.reduce((sum, f) => sum + (f.totales as any).total, 0);

    return {
      totalSales,
      otsCompletadas: otsCompletadas || 0,
      totalClientes: totalClientes || 0,
      totalProductos: totalProductos || 0,
    };
  }
}
