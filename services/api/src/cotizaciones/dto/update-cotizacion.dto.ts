import { IsArray, ValidateNested, IsString, IsObject, IsOptional, IsEnum } from 'class-validator';
import { Type } from 'class-transformer';
import { CreateCotizacionDto, VehiculoDto, LineaParteDto, LineaManoObraDto } from './create-cotizacion.dto';
import { QuoteStatus } from '@prisma/client';

export class UpdateCotizacionDto {
  @IsObject()
  @ValidateNested()
  @Type(() => VehiculoDto)
  @IsOptional()
  vehiculo?: VehiculoDto;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => LineaParteDto)
  @IsOptional()
  lineasPartes?: LineaParteDto[];

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => LineaManoObraDto)
  @IsOptional()
  lineasManoObra?: LineaManoObraDto[];

  @IsString()
  @IsOptional()
  clienteId?: string;

  @IsEnum(QuoteStatus)
  @IsOptional()
  estado?: QuoteStatus;
}
