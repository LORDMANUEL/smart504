import { IsString, IsOptional, IsEnum, IsArray, IsNumber } from 'class-validator';
import { WorkOrderStatus } from '@prisma/client';

class ConsumoInventarioDto {
    @IsString()
    productoId: string;

    @IsNumber()
    cantidad: number;
}

export class UpdateWorkOrderDto {
  @IsString()
  @IsOptional()
  tecnicoAsignadoId?: string;

  @IsEnum(WorkOrderStatus)
  @IsOptional()
  estado?: WorkOrderStatus;

  @IsArray()
  @IsOptional()
  consumosInventario?: ConsumoInventarioDto[];

  // You could add fields for photos, signatures, etc.
}
