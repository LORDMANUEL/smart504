# E-Commerce de Repuestos + Taller (HN/CCA)

Este es un monorepo para una solución completa de E-Commerce y gestión de talleres, construida con un stack moderno de TypeScript.

## Stack Tecnológico

- **Monorepo:** pnpm workspaces
- **Frontend:** Next.js 14 (App Router)
- **Backend:** NestJS 10
- **Base de Datos:** PostgreSQL
- **ORM:** Prisma
- **Cache & Colas:** Redis (con BullMQ)
- **UI:** Tailwind CSS (con un tema de neumorfismo opcional)

## Requisitos Previos

- Node.js (v18 o superior)
- pnpm (v8 o superior)
- PostgreSQL
- Redis

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd ecommerce-repuestos-taller
   ```

2. **Instalar dependencias:**
   ```bash
   pnpm install:all
   ```

3. **Configurar variables de entorno:**
   Crea un archivo `.env` en la raíz del proyecto, basándote en el `.env.example`. Asegúrate de configurar la URL de la base de datos y de Redis.

4. **Migrar y poblar la base de datos:**
   ```bash
   pnpm db:migrate
   pnpm db:seed
   ```

## Desarrollo

Para iniciar todos los servicios y aplicaciones en modo de desarrollo, ejecuta:

```bash
pnpm dev
```

Esto iniciará las aplicaciones `web`, `admin` y `signage`, así como los servicios `api` y `worker`, en modo de observación.

## Scripts Disponibles

- `pnpm install:all`: Instala todas las dependencias del monorepo.
- `pnpm build`: Construye todas las aplicaciones y servicios para producción.
- `pnpm dev`: Inicia todos los servicios en modo de desarrollo.
- `pnpm lint`: Ejecuta el linter en todos los paquetes.
- `pnpm test`: Ejecuta las pruebas en todos los paquetes.
- `pnpm db:migrate`: Aplica las migraciones de la base de datos.
- `pnpm db:seed`: Puebla la base de datos con datos de demostración.
- `pnpm docker:dev`: (Opcional) Inicia los servicios de base de datos y caché con Docker.
- `pnpm docker:stop`: (Opcional) Detiene los servicios de Docker.

## Estructura del Monorepo

- `apps/`: Contiene las aplicaciones de cara al usuario.
  - `web/`: Tienda, landing pages y cotizador.
  - `admin/`: Panel de administración.
  - `signage/`: Aplicación para pantallas y kioscos.
- `services/`: Contiene los servicios de backend.
  - `api/`: La API principal de NestJS.
  - `worker/`: Un servicio para trabajos en segundo plano (emails, PDFs, etc.).
- `packages/`: Contiene el código y las configuraciones compartidas.
  - `ui/`: Componentes de React compartidos.
  - `sdk/`: Cliente de TypeScript para la API.
  - `config/`: Configuraciones compartidas (ESLint, TypeScript).
