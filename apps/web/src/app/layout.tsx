import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Header, HeaderNav, HeaderTitle, Footer, SearchBar } from '@ecommerce/ui';
import Link from 'next/link';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'E-Commerce de Repuestos',
  description: 'La mejor selección de repuestos para tu vehículo.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className={`${inter.className} bg-gray-100`}>
        <Header>
            <HeaderTitle>Repuestos HN</HeaderTitle>
            <HeaderNav>
                <Link href="/">Inicio</Link>
                <Link href="/catalogo">Catálogo</Link>
                <Link href="/taller">Taller</Link>
                <Link href="/contacto">Contacto</Link>
            </HeaderNav>
            <div className="flex flex-1 items-center justify-end space-x-4">
                <SearchBar placeholder="Buscar por SKU, OEM..." />
                {/* Add cart and user icons here */}
            </div>
        </Header>
        <main className="container mx-auto py-8">
            {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
