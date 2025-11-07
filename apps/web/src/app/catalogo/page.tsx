'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { productos as productosApi, categorias as categoriasApi, marcas as marcasApi, Producto } from '@ecommerce/sdk';
import { ProductCard, Button, Card } from '@ecommerce/ui';
import Link from 'next/link';

export default function CatalogoPage() {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [categories, setCategories] = useState<{ categoria: string }[]>([]);
  const [marcas, setMarcas] = useState<{ marca: string }[]>([]);

  const searchParams = useSearchParams();
  const categoria = searchParams.get('categoria');
  const marca = searchParams.get('marca');
  const search = searchParams.get('search');
  const page = searchParams.get('page') || '1';

  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const [categoryData, marcaData] = await Promise.all([
          categoriasApi.getAll(),
          marcasApi.getAll(),
        ]);
        setCategories(categoryData);
        setMarcas(marcaData);
      } catch (error) {
        console.error('Failed to fetch filters', error);
      }
    };

    const fetchProductos = async () => {
      try {
        const productData = await productosApi.getAll({
          categoria: categoria || undefined,
          marca: marca || undefined,
          search: search || undefined,
          page,
        });
        setProductos(productData.data);
        setTotalPages(productData.totalPages);
        setCurrentPage(productData.page);
      } catch (error) {
        console.error('Failed to fetch products', error);
      }
    };

    fetchFilters();
    fetchProductos();
  }, [categoria, marca, search, page]);

  return (
    <div className="flex">
      {/* Filters Sidebar */}
      <aside className="w-1/4 pr-8">
        <Card className="p-4">
          <h3 className="font-bold mb-4">Categorías</h3>
          <ul>
            {categories.map(({ categoria }) => (
              <li key={categoria}><Link href={`/catalogo?categoria=${categoria}`}>{categoria}</Link></li>
            ))}
          </ul>
          <h3 className="font-bold my-4">Marcas</h3>
          <ul>
            {marcas.map(({ marca }) => (
              <li key={marca}><Link href={`/catalogo?marca=${marca}`}>{marca}</Link></li>
            ))}
          </ul>
        </Card>
      </aside>

      {/* Products Grid */}
      <div className="w-3/4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {productos.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>

        {/* Pagination Controls */}
        <div className="flex justify-center mt-8">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
            <Button key={page} variant={currentPage === page ? 'default' : 'ghost'}>
              <Link href={`/catalogo?page=${page}`}>{page}</Link>
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
