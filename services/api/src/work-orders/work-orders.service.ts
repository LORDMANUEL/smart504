import { Injectable, NotFoundException, BadRequestException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateWorkOrderDto } from './dto/create-work-order.dto';
import { UpdateWorkOrderDto } from './dto/update-work-order.dto';
import { QuoteStatus, WorkOrderStatus, InventoryMovementType } from '@prisma/client';

@Injectable()
export class WorkOrdersService {
  constructor(private prisma: PrismaService) {}

  async create(createWorkOrderDto: CreateWorkOrderDto) {
    const { cotizacionId, ...rest } = createWorkOrderDto;

    let lineas = {};

    if (cotizacionId) {
      const cotizacion = await this.prisma.cotizacion.findUnique({ where: { id: cotizacionId } });
      if (!cotizacion) {
        throw new NotFoundException(`Cotizacion with ID ${cotizacionId} not found`);
      }
      lineas = {
        manoObra: cotizacion.lineasManoObra,
        partes: cotizacion.lineasPartes,
      };
      // Mark quote as converted
      await this.prisma.cotizacion.update({
        where: { id: cotizacionId },
        data: { estado: QuoteStatus.CONVERTIDO_OT },
      });
    }

    return this.prisma.ordenDeTrabajo.create({
      data: {
        ...rest,
        cotizacionId,
        lineas,
        estado: WorkOrderStatus.PENDIENTE,
      },
    });
  }

  findAll() {
    return this.prisma.ordenDeTrabajo.findMany({
        orderBy: { createdAt: 'desc' },
    });
  }

  findOne(id: string) {
    return this.prisma.ordenDeTrabajo.findUnique({ where: { id } });
  }

  async update(id: string, updateWorkOrderDto: UpdateWorkOrderDto) {
    const { consumosInventario, ...rest } = updateWorkOrderDto;

    // Handle inventory consumption
    if (consumosInventario && consumosInventario.length > 0) {
      for (const consumo of consumosInventario) {
        await this.prisma.$transaction(async (tx) => {
          // 1. Find stock for the product in the main warehouse
          const stock = await tx.stock.findFirst({
            where: { productoId: consumo.productoId, almacen: 'Principal' }, // Assuming 'Principal' warehouse
          });

          if (!stock || stock.cantidad < consumo.cantidad) {
            throw new BadRequestException(`Insufficient stock for product ID ${consumo.productoId}`);
          }

          // 2. Decrease stock quantity
          await tx.stock.update({
            where: { id: stock.id },
            data: { cantidad: { decrement: consumo.cantidad } },
          });

          // 3. Create an inventory movement record
          await tx.inventarioMov.create({
            data: {
              productoId: consumo.productoId,
              tipo: InventoryMovementType.SALIDA,
              cantidad: consumo.cantidad,
              almacen: 'Principal',
              referencia: `OT-${id}`,
            }
          });
        });
      }
    }

    return this.prisma.ordenDeTrabajo.update({
      where: { id },
      data: rest,
    });
  }

  remove(id: string) {
    return this.prisma.ordenDeTrabajo.delete({ where: { id } });
  }
}
