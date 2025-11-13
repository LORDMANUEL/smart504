import { IsNotEmpty, IsObject, IsArray, ValidateNested, IsString, IsNumber, Min } from 'class-validator';
import { Type } from 'class-transformer';

class VehiculoDto {
  @IsString()
  @IsNotEmpty()
  marca: string;

  @IsString()
  @IsNotEmpty()
  modelo: string;

  @IsString()
  @IsNotEmpty()
  anio: string;

  @IsString()
  @IsOptional()
  motor?: string;

  @IsString()
  @IsOptional()
  vin?: string;
}

class LineaParteDto {
  @IsString()
  @IsNotEmpty()
  productoId: string;

  @IsNumber()
  @Min(1)
  cantidad: number;

  @IsNumber()
  precio: number;
}

class LineaManoObraDto {
  @IsString()
  @IsNotEmpty()
  descripcion: string;

  @IsNumber()
  @Min(0)
  tiempo: number; // In hours

  @IsNumber()
  @Min(0)
  costo: number;
}


export class CreateCotizacionDto {
  @IsObject()
  @ValidateNested()
  @Type(() => VehiculoDto)
  vehiculo: VehiculoDto;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => LineaParteDto)
  lineasPartes: LineaParteDto[];

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => LineaManoObraDto)
  lineasManoObra: LineaManoObraDto[];

  @IsString()
  @IsOptional()
  clienteId?: string;
}
