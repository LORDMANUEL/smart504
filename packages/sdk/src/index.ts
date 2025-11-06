import axios from 'axios';

// Re-export DTOs and types from the new types package
export * from '@ecommerce/types';
import {
  CreateUserDto, UpdateUserDto,
  CreateProductoDto, UpdateProductoDto,
  CreateStockDto, UpdateStockDto
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

// Catalog Endpoints
export const productos = {
  getAll: async () => {
    const response = await apiClient.get('/productos');
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
