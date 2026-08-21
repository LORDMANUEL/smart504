import { PackageCheck, PackageSearch, ShoppingBag } from 'lucide-react';
import type { Product } from '../types';

const availability = {
  IN_STOCK: { label: 'Disponible', icon: PackageCheck },
  LOW_STOCK: { label: 'Pocas unidades', icon: PackageSearch },
  OUT_OF_STOCK: { label: 'Agotado', icon: PackageSearch },
  ON_REQUEST: { label: 'Bajo pedido', icon: PackageSearch },
} as const;

function formatMoney(value: string, currency: string) {
  return new Intl.NumberFormat('es-HN', { style: 'currency', currency }).format(Number(value));
}

function catalogImage(sku: string): string {
  if (sku.includes('AIR')) return '/images/products/air-filter.png';
  if (sku.includes('BRK') || sku.includes('PAD')) return '/images/products/brake-pads.png';
  if (sku.includes('SPK') || sku.includes('SPARK')) return '/images/products/spark-plugs.png';
  return '/images/products/oil-filter.png';
}

export function ProductCard({ product, onAdd }: { product: Product; onAdd: (product: Product) => void }) {
  const primary = product.images.find((image) => image.is_primary) ?? product.images[0];
  const isGenericPlaceholder = primary?.alt_text.toLocaleLowerCase('es').includes('imagen generica de referencia');
  const productImage = primary && !isGenericPlaceholder ? primary.url : catalogImage(product.sku);
  const productImageAlt = primary && !isGenericPlaceholder
    ? primary.alt_text
    : `Imagen de referencia de ${product.name}`;
  const state = availability[product.stock_status];
  const AvailabilityIcon = state.icon;

  return (
    <article className="product-card">
      <div className="product-card__media">
        <img src={productImage} alt={productImageAlt} loading="lazy" />
        <span className={`availability availability--${product.stock_status.toLowerCase()}`}>
          <AvailabilityIcon size={14} aria-hidden="true" /> {state.label}
        </span>
      </div>
      <div className="product-card__body">
        <div className="product-card__meta"><span>{product.brand ?? 'Repuesto'}</span><code>{product.sku}</code></div>
        <h3>{product.name}</h3>
        <p>{product.description ?? 'Consulte disponibilidad y compatibilidad con nuestro equipo.'}</p>
        <div className="product-card__compatibility">{product.compatibility_note ?? 'Compatibilidad sujeta a validación por VIN.'}</div>
        <div className="product-card__footer">
          <strong>{formatMoney(product.display_price, product.currency)}</strong>
          <button type="button" onClick={() => onAdd(product)} disabled={product.stock_status === 'OUT_OF_STOCK'}>
            <ShoppingBag size={17} aria-hidden="true" /> Agregar
          </button>
        </div>
      </div>
    </article>
  );
}
