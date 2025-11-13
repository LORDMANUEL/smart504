import { IsString, IsOptional, IsNumberString } from 'class-validator';

export class FindAllProductosDto {
  @IsString()
  @IsOptional()
  categoria?: string;

  @IsString()
  @IsOptional()
  marca?: string;

  @IsString()
  @IsOptional()
  search?: string;

  @IsNumberString()
  @IsOptional()
  page?: string;

  @IsNumberString()
  @IsOptional()
  limit?: string;
}
