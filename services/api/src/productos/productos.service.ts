import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateProductoDto } from './dto/create-producto.dto';
import { UpdateProductoDto } from './dto/update-producto.dto';
import { FindAllProductosDto } from './dto/findall-producto.dto';
import { Prisma } from '@prisma/client';

@Injectable()
export class ProductosService {
  constructor(private prisma: PrismaService) {}

  create(createProductoDto: CreateProductoDto) {
    return this.prisma.producto.create({ data: createProductoDto });
  }

  async findAll(query: FindAllProductosDto) {
    const { page = '1', limit = '10', categoria, marca, search } = query;
    const pageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);
    const skip = (pageNum - 1) * limitNum;

    const where: Prisma.ProductoWhereInput = {};
    if (categoria) where.categoria = categoria;
    if (marca) where.marca = marca;
    if (search) {
      where.OR = [
        { nombre: { contains: search, mode: 'insensitive' } },
        { sku: { contains: search, mode: 'insensitive' } },
        { oem: { contains: search, mode: 'insensitive' } },
      ];
    }

    const [productos, total] = await this.prisma.$transaction([
      this.prisma.producto.findMany({
        where,
        skip,
        take: limitNum,
        include: { stocks: true },
      }),
      this.prisma.producto.count({ where }),
    ]);

    return {
      data: productos,
      total,
      page: pageNum,
      limit: limitNum,
      totalPages: Math.ceil(total / limitNum),
    };
  }

  async findOne(id: string) {
    const producto = await this.prisma.producto.findUnique({
      where: { id },
      include: { stocks: true },
    });
    if (!producto) {
      throw new NotFoundException(`Producto with ID ${id} not found`);
    }
    return producto;
  }

  update(id: string, updateProductoDto: UpdateProductoDto) {
    return this.prisma.producto.update({
      where: { id },
      data: updateProductoDto,
    });
  }

  remove(id: string) {
    return this.prisma.producto.delete({ where: { id } });
  }
}
