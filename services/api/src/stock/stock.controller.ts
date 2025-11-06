import { Controller, Get, Post, Body, Patch, Param, Delete, UseGuards } from '@nestjs/common';
import { StockService } from './stock.service';
import { CreateStockDto } from './dto/create-stock.dto';
import { UpdateStockDto } from './dto/update-stock.dto';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { RolesGuard } from '../auth/roles.guard';
import { Roles } from '../auth/roles.decorator';
import { UserRole } from '@prisma/client';

@Controller('stock')
@UseGuards(JwtAuthGuard, RolesGuard)
export class StockController {
  constructor(private readonly stockService: StockService) {}

  @Post()
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.BODEGA)
  create(@Body() createStockDto: CreateStockDto) {
    return this.stockService.create(createStockDto);
  }

  @Get()
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.BODEGA, UserRole.VENTAS)
  findAll() {
    return this.stockService.findAll();
  }

  @Get(':id')
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.BODEGA, UserRole.VENTAS)
  findOne(@Param('id') id: string) {
    return this.stockService.findOne(id);
  }

  @Patch(':id')
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.BODEGA)
  update(@Param('id') id: string, @Body() updateStockDto: UpdateStockDto) {
    return this.stockService.update(id, updateStockDto);
  }

  @Delete(':id')
  @Roles(UserRole.ADMIN, UserRole.GERENTE)
  remove(@Param('id') id: string) {
    return this.stockService.remove(id);
  }
}
