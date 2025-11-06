import { IsString, IsNumber, IsOptional, IsBoolean, IsJSON } from 'class-validator';

export class UpdateProductoDto {
  @IsString()
  @IsOptional()
  sku?: string;

  @IsString()
  @IsOptional()
  oem?: string;

  @IsString()
  @IsOptional()
  nombre?: string;

  @IsString()
  @IsOptional()
  marca?: string;

  @IsString()
  @IsOptional()
  categoria?: string;

  @IsString()
  @IsOptional()
  descripcion?: string;

  @IsJSON()
  @IsOptional()
  fotos?: string;

  @IsNumber()
  @IsOptional()
  precioBase?: number;

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
