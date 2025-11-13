import { Controller, Get, Post, Body, Patch, Param, Delete, UseGuards, Req } from '@nestjs/common';
import { CartService } from './cart.service';
import { AddToCartDto } from './dto/add-to-cart.dto';
import { UpdateCartItemDto } from './dto/update-cart-item.dto';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';

@Controller('carrito')
@UseGuards(JwtAuthGuard)
export class CartController {
  constructor(private readonly cartService: CartService) {}

  @Get()
  getCart(@Req() req) {
    // req.user is populated by JwtAuthGuard
    return this.cartService.getCart(req.user.id);
  }

  @Post()
  addItem(@Req() req, @Body() addToCartDto: AddToCartDto) {
    return this.cartService.addItem(req.user.id, addToCartDto);
  }

  @Patch(':productoId')
  updateItem(
    @Req() req,
    @Param('productoId') productoId: string,
    @Body() updateCartItemDto: UpdateCartItemDto,
  ) {
    return this.cartService.updateItem(req.user.id, productoId, updateCartItemDto);
  }

  @Delete(':productoId')
  removeItem(@Req() req, @Param('productoId') productoId: string) {
    return this.cartService.removeItem(req.user.id, productoId);
  }
}
