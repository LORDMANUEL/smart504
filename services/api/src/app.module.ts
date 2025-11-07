import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { AuthModule } from './auth/auth.module';
import { ConfigModule } from '@nestjs/config';
import { PrismaModule } from './prisma/prisma.module';
import { UsersModule } from './users/users.module';
import { StockModule } from './stock/stock.module';
import { MarcasModule } from './marcas/marcas.module';
import { CategoriasModule } from './categorias/categorias.module';
import { ProductosModule } from './productos/productos.module';
import { CartModule } from './cart/cart.module';
import { CotizacionesModule } from './cotizaciones/cotizaciones.module';
import { WorkOrdersModule } from './work-orders/work-orders.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    AuthModule,
    PrismaModule,
    UsersModule,
    ProductosModule,
    CategoriasModule,
    MarcasModule,
    StockModule,
    CartModule,
    CotizacionesModule,
    WorkOrdersModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
