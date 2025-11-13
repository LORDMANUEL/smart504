import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class CategoriasService {
  constructor(private prisma: PrismaService) {}

  findAll() {
    return this.prisma.producto.findMany({
      select: {
        categoria: true,
      },
      distinct: ['categoria'],
    });
  }
}
