// Re-export DTOs from the API
export * from '../../services/api/src/users/dto';
export * from '../../services/api/src/productos/dto';
export * from '../../services/api/src/stock/dto';
export * from '../../services/api/src/cart/dto';
export * from '../../services/api/src/cotizaciones/dto';
export * from '../../services/api/src/work-orders/dto';

// Re-export generated Prisma types
// Note: This relies on the postinstall script having run for the api service
export type {
  UserRole,
  Usuario as User,
  Producto,
  Stock,
  Pedido as Cart,
  Cotizacion,
  OrdenDeTrabajo as WorkOrder
} from '../../services/api/node_modules/.prisma/client';
