import axios from 'axios';

// Re-export DTOs and types from the new types package
export * from '@ecommerce/types';
import {
  CreateUserDto, UpdateUserDto,
  CreateProductoDto, UpdateProductoDto,
  CreateStockDto, UpdateStockDto,
  FindAllProductosDto,
  AddToCartDto, UpdateCartItemDto,
  CreateCotizacionDto, UpdateCotizacionDto,
  CreateWorkOrderDto, UpdateWorkOrderDto
} from '@ecommerce/types';


const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3333',
  headers: {
    'Content-Type': 'application/json',
  },
});

let accessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

apiClient.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth Endpoints
export const auth = {
  login: async (credentials: { email: string; password: string }) => {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },
  register: async (userData: CreateUserDto) => {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },
  getProfile: async () => {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  },
};

// Work Orders Endpoints
export const ordenesTrabajo = {
  getAll: async () => {
    const response = await apiClient.get('/ordenes-trabajo');
    return response.data;
  },
  getOne: async (id: string) => {
    const response = await apiClient.get(`/ordenes-trabajo/${id}`);
    return response.data;
  },
  create: async (data: CreateWorkOrderDto) => {
    const response = await apiClient.post('/ordenes-trabajo', data);
    return response.data;
  },
  update: async (id: string, data: UpdateWorkOrderDto) => {
    const response = await apiClient.patch(`/ordenes-trabajo/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await apiClient.delete(`/ordenes-trabajo/${id}`);
    return response.data;
  },
};

// Quotes Endpoints
export const cotizaciones = {
  getAll: async () => {
    const response = await apiClient.get('/cotizaciones');
    return response.data;
  },
  getOne: async (id: string) => {
    const response = await apiClient.get(`/cotizaciones/${id}`);
    return response.data;
  },
  create: async (data: CreateCotizacionDto) => {
    const response = await apiClient.post('/cotizaciones', data);
    return response.data;
  },
  update: async (id: string, data: UpdateCotizacionDto) => {
    const response = await apiClient.patch(`/cotizaciones/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await apiClient.delete(`/cotizaciones/${id}`);
    return response.data;
  },
};

// Cart Endpoints
export const carrito = {
  get: async () => {
    const response = await apiClient.get('/carrito');
    return response.data;
  },
  add: async (data: AddToCartDto) => {
    const response = await apiClient.post('/carrito', data);
    return response.data;
  },
  update: async (productoId: string, data: UpdateCartItemDto) => {
    const response = await apiClient.patch(`/carrito/${productoId}`, data);
    return response.data;
  },
  remove: async (productoId: string) => {
    const response = await apiClient.delete(`/carrito/${productoId}`);
    return response.data;
  },
};

// Catalog Endpoints
export const productos = {
  getAll: async (params?: FindAllProductosDto) => {
    const response = await apiClient.get('/productos', { params });
    return response.data;
  },
  getOne: async (id: string) => {
    const response = await apiClient.get(`/productos/${id}`);
    return response.data;
  },
  create: async (data: CreateProductoDto) => {
    const response = await apiClient.post('/productos', data);
    return response.data;
  },
  update: async (id: string, data: UpdateProductoDto) => {
    const response = await apiClient.patch(`/productos/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await apiClient.delete(`/productos/${id}`);
    return response.data;
  },
};

export const categorias = {
  getAll: async () => {
    const response = await apiClient.get('/categorias');
    return response.data;
  },
};

export const marcas = {
  getAll: async () => {
    const response = await apiClient.get('/marcas');
    return response.data;
  },
};

export const stock = {
  create: async (data: CreateStockDto) => {
    const response = await apiClient.post('/stock', data);
    return response.data;
  },
  update: async (id: string, data: UpdateStockDto) => {
    const response = await apiClient.patch(`/stock/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await apiClient.delete(`/stock/${id}`);
    return response.data;
  },
};

// User Endpoints
export const users = {
  getAll: async () => {
    const response = await apiClient.get('/users');
    return response.data;
  },
  getOne: async (id: string) => {
    const response = await apiClient.get(`/users/${id}`);
    return response.data;
  },
  create: async (userData: CreateUserDto) => {
    const response = await apiClient.post('/users', userData);
    return response.data;
  },
  update: async (id: string, updates: UpdateUserDto) => {
    const response = await apiClient.patch(`/users/${id}`, updates);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await apiClient.delete(`/users/${id}`);
    return response.data;
  },
};
