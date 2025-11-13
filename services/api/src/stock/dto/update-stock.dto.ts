import { IsString, IsNumber, IsOptional } from 'class-validator';

export class UpdateStockDto {
  @IsString()
  @IsOptional()
  almacen?: string;

  @IsString()
  @IsOptional()
  ubicacion?: string;

  @IsNumber()
  @IsOptional()
  cantidad?: number;

  @IsNumber()
  @IsOptional()
  min?: number;

  @IsNumber()
  @IsOptional()
  max?: number;
}
