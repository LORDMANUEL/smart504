import { IsNotEmpty, IsString, IsNumber, Min } from 'class-validator';

export class AddToCartDto {
  @IsString()
  @IsNotEmpty()
  productoId: string;

  @IsNumber()
  @Min(1)
  cantidad: number;
}
