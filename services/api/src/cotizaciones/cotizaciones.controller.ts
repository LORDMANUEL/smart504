import { Controller, Get, Post, Body, Patch, Param, Delete, UseGuards } from '@nestjs/common';
import { CotizacionesService } from './cotizaciones.service';
import { CreateCotizacionDto } from './dto/create-cotizacion.dto';
import { UpdateCotizacionDto } from './dto/update-cotizacion.dto';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { RolesGuard } from '../auth/roles.guard';
import { Roles } from '../auth/roles.decorator';
import { UserRole } from '@prisma/client';

@Controller('cotizaciones')
@UseGuards(JwtAuthGuard, RolesGuard)
export class CotizacionesController {
  constructor(private readonly cotizacionesService: CotizacionesService) {}

  @Post()
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.VENTAS)
  create(@Body() createCotizacionDto: CreateCotizacionDto) {
    return this.cotizacionesService.create(createCotizacionDto);
  }

  @Get()
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.VENTAS)
  findAll() {
    return this.cotizacionesService.findAll();
  }

  // A public endpoint to view a quote by ID could be added later
  @Get(':id')
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.VENTAS)
  findOne(@Param('id') id: string) {
    return this.cotizacionesService.findOne(id);
  }

  @Patch(':id')
  @Roles(UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.VENTAS)
  update(@Param('id') id: string, @Body() updateCotizacionDto: UpdateCotizacionDto) {
    return this.cotizacionesService.update(id, updateCotizacionDto);
  }

  @Delete(':id')
  @Roles(UserRole.ADMIN, UserRole.GERENTE)
  remove(@Param('id') id: string) {
    return this.cotizacionesService.remove(id);
  }
}
