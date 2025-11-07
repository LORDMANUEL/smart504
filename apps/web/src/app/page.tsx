'use client';

import { useEffect, useState } from 'react';
import { categorias as categoriasApi, productos as productosApi, Producto } from '@ecommerce/sdk';
import { ProductCard, Button, Card } from '@ecommerce/ui';
import Link from 'next/link';

export default function HomePage() {
  const [categories, setCategories] = useState<{ categoria: string }[]>([]);
  const [featuredProducts, setFeaturedProducts] = useState<Producto[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [categoryData, productData] = await Promise.all([
          categoriasApi.getAll(),
          productosApi.getAll({ limit: '4' }), // Fetch 4 featured products
        ]);
        setCategories(categoryData);
        setFeaturedProducts(productData.data);
      } catch (error) {
        console.error('Failed to fetch home page data', error);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <Card className="text-center p-12">
        <h1 className="text-4xl font-bold mb-4">Encuentra el Repuesto Perfecto</h1>
        <p className="text-lg text-gray-600 mb-8">Calidad y confianza para tu vehículo.</p>
        <Button size="lg" asChild>
          <Link href="/catalogo">Ver Catálogo</Link>
        </Button>
      </Card>

      {/* Categories Section */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Categorías Populares</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {categories.map(({ categoria }) => (
            <Link key={categoria} href={`/catalogo?categoria=${categoria}`}>
              <Card className="p-4 text-center hover:shadow-lg transition-shadow">
                <span className="font-semibold">{categoria}</span>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Featured Products Section */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Productos Destacados</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredProducts.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </div>
    </div>
  );
}
