import { IsString, IsNotEmpty, IsNumber, IsOptional } from 'class-validator';

export class CreateStockDto {
  @IsString()
  @IsNotEmpty()
  productoId: string;

  @IsString()
  @IsNotEmpty()
  almacen: string;

  @IsString()
  @IsOptional()
  ubicacion?: string;

  @IsNumber()
  @IsNotEmpty()
  cantidad: number;

  @IsNumber()
  @IsOptional()
  min?: number;

  @IsNumber()
  @IsOptional()
  max?: number;
}
