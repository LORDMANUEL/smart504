import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CreateStockDto } from './dto/create-stock.dto';
import { UpdateStockDto } from './dto/update-stock.dto';

@Injectable()
export class StockService {
  constructor(private prisma: PrismaService) {}

  create(createStockDto: CreateStockDto) {
    return this.prisma.stock.create({ data: createStockDto });
  }

  findAll() {
    return this.prisma.stock.findMany();
  }

  async findOne(id: string) {
    const stock = await this.prisma.stock.findUnique({ where: { id } });
    if (!stock) {
      throw new NotFoundException(`Stock with ID ${id} not found`);
    }
    return stock;
  }

  update(id: string, updateStockDto: UpdateStockDto) {
    return this.prisma.stock.update({
      where: { id },
      data: updateStockDto,
    });
  }

  remove(id: string) {
    return this.prisma.stock.delete({ where: { id } });
  }
}
