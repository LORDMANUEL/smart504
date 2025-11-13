import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { AddToCartDto } from './dto/add-to-cart.dto';
import { UpdateCartItemDto } from './dto/update-cart-item.dto';
import { OrderStatus } from '@prisma/client';

@Injectable()
export class CartService {
  constructor(private prisma: PrismaService) {}

  async getCart(userId: string) {
    let cart = await this.prisma.pedido.findFirst({
      where: {
        clienteId: userId,
        estado: OrderStatus.CARRITO,
      },
    });

    if (!cart) {
      cart = await this.prisma.pedido.create({
        data: {
          clienteId: userId,
          estado: OrderStatus.CARRITO,
          items: [],
        },
      });
    }
    return cart;
  }

  async addItem(userId: string, itemDto: AddToCartDto) {
    const { productoId, cantidad } = itemDto;
    const cart = await this.getCart(userId);

    const producto = await this.prisma.producto.findUnique({ where: { id: productoId } });
    if (!producto) {
      throw new NotFoundException(`Producto with ID ${productoId} not found`);
    }

    const items = (cart.items as any[]) || [];
    const existingItemIndex = items.findIndex(item => item.productoId === productoId);

    if (existingItemIndex > -1) {
      items[existingItemIndex].cantidad += cantidad;
    } else {
      items.push({
        productoId,
        sku: producto.sku,
        nombre: producto.nombre,
        cantidad,
        precio: producto.precioBase
      });
    }

    return this.prisma.pedido.update({
      where: { id: cart.id },
      data: { items },
    });
  }

  async updateItem(userId: string, productoId: string, itemDto: UpdateCartItemDto) {
    const { cantidad } = itemDto;
    const cart = await this.getCart(userId);
    const items = (cart.items as any[]) || [];

    const itemIndex = items.findIndex(item => item.productoId === productoId);
    if (itemIndex === -1) {
      throw new NotFoundException(`Producto with ID ${productoId} not in cart`);
    }

    items[itemIndex].cantidad = cantidad;

    return this.prisma.pedido.update({
      where: { id: cart.id },
      data: { items },
    });
  }

  async removeItem(userId: string, productoId: string) {
    const cart = await this.getCart(userId);
    const items = (cart.items as any[]) || [];

    const updatedItems = items.filter(item => item.productoId !== productoId);

    if (items.length === updatedItems.length) {
        throw new NotFoundException(`Producto with ID ${productoId} not in cart`);
    }

    return this.prisma.pedido.update({
      where: { id: cart.id },
      data: { items: updatedItems },
    });
  }
}
