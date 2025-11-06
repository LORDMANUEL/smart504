import { PrismaClient } from '@prisma/client';
import { hash } from 'bcrypt';

const prisma = new PrismaClient();

async function main() {
  console.log('Start seeding ...');

  const password = await hash('password123', 10);

  // Create Users
  const admin = await prisma.usuario.create({
    data: {
      email: 'admin@example.com',
      name: 'Admin User',
      password,
      role: 'ADMIN',
    },
  });

  const tecnico = await prisma.usuario.create({
    data: {
      email: 'tecnico@example.com',
      name: 'Carlos Técnico',
      password,
      role: 'TECNICO',
    },
  });

  console.log('Created users');

  // Create Clientes
  const clienteB2C = await prisma.cliente.create({
    data: {
      tipo: 'B2C',
      nombre: 'Juan Perez',
      rtn: '08011990123456',
      contactos: JSON.stringify([{ nombre: 'Juan Perez', telefono: '98765432', email: 'juan.perez@email.com' }]),
      direcciones: JSON.stringify([{ tipo: 'casa', direccion: 'Col. Las Acacias, Casa 123' }]),
    },
  });

  console.log('Created clientes');

  // Create Productos & Stock
  for (let i = 1; i <= 100; i++) {
    const producto = await prisma.producto.create({
      data: {
        sku: `SKU-00${i}`,
        oem: `OEM-00${i}`,
        nombre: `Repuesto Genérico ${i}`,
        marca: `Marca ${i % 5 + 1}`,
        categoria: `Categoría ${i % 10 + 1}`,
        descripcion: `Descripción detallada para el repuesto ${i}.`,
        precioBase: parseFloat((Math.random() * 100 + 10).toFixed(2)),
        compatibilidad: JSON.stringify([
          { marca: 'Toyota', modelo: 'Corolla', anio: '2020', motor: '1.8L' },
          { marca: 'Honda', modelo: 'Civic', anio: '2019', motor: '1.5T' },
        ]),
        stocks: {
          create: {
            almacen: 'Principal',
            ubicacion: `Estante ${i % 10}`,
            cantidad: Math.floor(Math.random() * 50) + 1,
            min: 5,
            max: 50,
          },
        },
      },
    });
  }

  console.log('Created 100 productos with stock');

  const firstProduct = await prisma.producto.findFirst({
    orderBy: { createdAt: 'asc' },
  });

  if (!firstProduct) {
    console.error('No products found to seed orders, quotes, etc.');
    return;
  }

  // Create an Orden de Trabajo
  const ot = await prisma.ordenDeTrabajo.create({
    data: {
      vehiculo: JSON.stringify({ marca: 'Toyota', modelo: 'Corolla', anio: '2020', vin: 'VIN123456789' }),
      tecnicoAsignadoId: tecnico.id,
      estado: 'EN_REPARACION',
      lineas: JSON.stringify({
        manoObra: [{ descripcion: 'Cambio de aceite', tiempo: 1, costo: 50.0 }],
        partes: [{ productoId: firstProduct.id, sku: firstProduct.sku, cantidad: 1, precio: firstProduct.precioBase }],
      }),
      consumosInventario: JSON.stringify([{ productoId: firstProduct.id, cantidad: 1, fecha: new Date() }]),
    }
  });

  console.log('Created Orden de Trabajo');

  // Create Factura for the OT
  await prisma.factura.create({
    data: {
      clienteId: clienteB2C.id,
      ordenDeTrabajoId: ot.id,
      serie: 'F-001',
      correlativo: '00001',
      lineas: JSON.stringify([
        { descripcion: 'Cambio de aceite', cantidad: 1, precio: 50.0 },
        { descripcion: `Filtro de aceite ${firstProduct.sku}`, cantidad: 1, precio: firstProduct.precioBase },
      ]),
      impuestos: JSON.stringify({ nombre: 'ISV', tasa: 0.15, monto: (50 + firstProduct.precioBase) * 0.15 }),
      totales: JSON.stringify({ subtotal: 50 + firstProduct.precioBase, impuestos: (50 + firstProduct.precioBase) * 0.15, total: (50 + firstProduct.precioBase) * 1.15 }),
    }
  });

  console.log('Created Factura');

  console.log('Seeding finished.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
