// Re-export DTOs from the API
export * from '../../services/api/src/users/dto';
export * from '../../services/api/src/productos/dto';
export * from '../../services/api/src/stock/dto';

// Re-export generated Prisma types
// Note: This relies on the postinstall script having run for the api service
export type {
  UserRole,
  Usuario as User,
  Producto,
  Stock
} from '../../services/api/node_modules/.prisma/client';
