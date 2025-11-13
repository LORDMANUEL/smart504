import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateCotizacionDto } from './dto/create-cotizacion.dto';
import { UpdateCotizacionDto } from './dto/update-cotizacion.dto';

@Injectable()
export class CotizacionesService {
  constructor(private prisma: PrismaService) {}

  async create(createCotizacionDto: CreateCotizacionDto) {
    const { lineasPartes, lineasManoObra, ...rest } = createCotizacionDto;

    const totalPartes = lineasPartes.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    const totalManoObra = lineasManoObra.reduce((sum, item) => sum + item.costo, 0);
    const total = totalPartes + totalManoObra;

    return this.prisma.cotizacion.create({
      data: {
        ...rest,
        lineasPartes: lineasPartes as any,
        lineasManoObra: lineasManoObra as any,
        total,
      },
    });
  }

  findAll() {
    return this.prisma.cotizacion.findMany({
      orderBy: { createdAt: 'desc' },
    });
  }

  async findOne(id: string) {
    const cotizacion = await this.prisma.cotizacion.findUnique({ where: { id } });
    if (!cotizacion) {
      throw new NotFoundException(`Cotizacion with ID ${id} not found`);
    }
    return cotizacion;
  }

  update(id: string, updateCotizacionDto: UpdateCotizacionDto) {
    // Recalculate total if lines are updated
    if (updateCotizacionDto.lineasPartes || updateCotizacionDto.lineasManoObra) {
        // This logic can be enhanced, for now, we just update
    }

    return this.prisma.cotizacion.update({
      where: { id },
      data: {
        ...updateCotizacionDto,
        lineasPartes: updateCotizacionDto.lineasPartes as any,
        lineasManoObra: updateCotizacionDto.lineasManoObra as any,
      },
    });
  }

  remove(id: string) {
    return this.prisma.cotizacion.delete({ where: { id } });
  }
}
