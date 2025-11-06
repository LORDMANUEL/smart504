import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class MarcasService {
  constructor(private prisma: PrismaService) {}

  findAll() {
    return this.prisma.producto.findMany({
      select: {
        marca: true,
      },
      distinct: ['marca'],
    });
  }
}
