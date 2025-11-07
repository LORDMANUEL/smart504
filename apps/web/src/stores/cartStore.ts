import { create } from 'zustand';
import { carrito as cartApi, Cart, AddToCartDto, UpdateCartItemDto } from '@ecommerce/sdk';

interface CartState {
  cart: Cart | null;
  isLoading: boolean;
  error: string | null;
  fetchCart: () => Promise<void>;
  addItem: (item: AddToCartDto) => Promise<void>;
  updateItem: (productoId: string, item: UpdateCartItemDto) => Promise<void>;
  removeItem: (productoId: string) => Promise<void>;
  clearCart: () => void;
}

export const useCartStore = create<CartState>((set) => ({
  cart: null,
  isLoading: false,
  error: null,

  fetchCart: async () => {
    set({ isLoading: true, error: null });
    try {
      const cartData = await cartApi.get();
      set({ cart: cartData, isLoading: false });
    } catch (err) {
      set({ error: 'Failed to fetch cart', isLoading: false });
    }
  },

  addItem: async (item) => {
    set({ isLoading: true, error: null });
    try {
      const updatedCart = await cartApi.add(item);
      set({ cart: updatedCart, isLoading: false });
    } catch (err) {
      set({ error: 'Failed to add item to cart', isLoading: false });
    }
  },

  updateItem: async (productoId, item) => {
    set({ isLoading: true, error: null });
    try {
      const updatedCart = await cartApi.update(productoId, item);
      set({ cart: updatedCart, isLoading: false });
    } catch (err) {
      set({ error: 'Failed to update item in cart', isLoading: false });
    }
  },

  removeItem: async (productoId) => {
    set({ isLoading: true, error: null });
    try {
      const updatedCart = await cartApi.remove(productoId);
      set({ cart: updatedCart, isLoading: false });
    } catch (err) {
      set({ error: 'Failed to remove item from cart', isLoading: false });
    }
  },

  clearCart: () => {
    set({ cart: null });
  }
}));
