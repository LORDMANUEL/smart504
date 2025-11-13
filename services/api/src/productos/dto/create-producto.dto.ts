import { IsString, IsNotEmpty, IsNumber, IsOptional, IsBoolean, IsJSON } from 'class-validator';

export class CreateProductoDto {
  @IsString()
  @IsNotEmpty()
  sku: string;

  @IsString()
  @IsOptional()
  oem?: string;

  @IsString()
  @IsNotEmpty()
  nombre: string;

  @IsString()
  @IsNotEmpty()
  marca: string;

  @IsString()
  @IsNotEmpty()
  categoria: string;

  @IsString()
  @IsOptional()
  descripcion?: string;

  @IsJSON()
  @IsOptional()
  fotos?: string;

  @IsNumber()
  @IsNotEmpty()
  precioBase: number;

  @IsJSON()
  @IsOptional()
  impuestos?: string;

  @IsJSON()
  @IsOptional()
  compatibilidad?: string;

  @IsBoolean()
  @IsOptional()
  activo?: boolean;
}
