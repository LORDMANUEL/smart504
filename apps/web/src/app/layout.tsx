'use client';

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Header, HeaderNav, HeaderTitle, HeaderCart, Footer, SearchBar } from '@ecommerce/ui';
import Link from 'next/link';
import { useCartStore } from '../stores/cartStore';
import { useAuthStore } from '../stores/authStore';
import { useEffect } from 'react';

const inter = Inter({ subsets: ['latin'] });

// Metadata cannot be in a client component, so we keep it separate or define it statically.
// export const metadata: Metadata = { ... };

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { cart, fetchCart, clearCart } = useCartStore();
  const { user, logout: logoutUser } = useAuthStore();

  useEffect(() => {
    if (user) {
      fetchCart();
    } else {
      clearCart();
    }
  }, [user, fetchCart, clearCart]);

  const handleLogout = () => {
    logoutUser();
    clearCart();
  };

  const itemCount = cart?.items ? (cart.items as any[]).reduce((sum, item) => sum + item.cantidad, 0) : 0;

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
                <HeaderCart itemCount={itemCount} />
                {user ? (
                  <div>
                    <span>{user.name}</span>
                    <Button onClick={handleLogout} variant="ghost" size="sm">Logout</Button>
                  </div>
                ) : (
                  <Button asChild>
                    <Link href="/login">Login</Link>
                  </Button>
                )}
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
