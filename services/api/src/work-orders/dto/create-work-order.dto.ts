import { IsString, IsNotEmpty, IsOptional, IsObject, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { VehiculoDto } from '../../cotizaciones/dto/create-cotizacion.dto';

export class CreateWorkOrderDto {
  @IsString()
  @IsOptional()
  cotizacionId?: string;

  @IsObject()
  @ValidateNested()
  @Type(() => VehiculoDto)
  vehiculo: VehiculoDto;

  @IsString()
  @IsOptional()
  tecnicoAsignadoId?: string;

  // Symptoms and other initial details can be added here
  @IsString()
  @IsOptional()
  descripcionProblema?: string;
}
