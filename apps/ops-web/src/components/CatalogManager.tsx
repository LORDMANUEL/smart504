import { FormEvent, useMemo, useState } from 'react';
import { CheckCircle2, CloudDownload, ImagePlus, LoaderCircle, PackagePlus, Search, Upload } from 'lucide-react';
import { addExternalImage, createProduct, searchGoogleImages, updateProduct, uploadProductImage } from '../lib/api';
import type { Product } from '../types';

export function CatalogManager({ token, products, onReload }: { token: string; products: Product[]; onReload: () => Promise<void> }) {
  const [selectedId, setSelectedId] = useState(products[0]?.id ?? '');
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [imageQuery, setImageQuery] = useState('');
  const [searchResult, setSearchResult] = useState<{ configured: boolean; items: { image_url: string; thumbnail_url?: string; source_page_url?: string; title: string; display_link?: string }[] } | null>(null);
  const selected = useMemo(() => products.find((item) => item.id === selectedId) ?? products[0], [products, selectedId]);

  async function submitProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setNotice('');
    const data = new FormData(event.currentTarget);
    try {
      const product = await createProduct(token, {
        sku: String(data.get('sku') ?? ''), name: String(data.get('name') ?? ''),
        description: String(data.get('description') ?? ''), brand: String(data.get('brand') ?? ''),
        display_price: String(data.get('display_price') ?? '0'), currency: 'HNL',
        purchase_cost: String(data.get('purchase_cost') ?? '0'), landed_cost_factor: String(data.get('landed_cost_factor') ?? '1'),
        target_markup_percent: String(data.get('target_markup_percent') ?? '30'), minimum_markup_percent: String(data.get('minimum_markup_percent') ?? '0'),
        abc_class: String(data.get('abc_class') ?? 'C'), xyz_class: String(data.get('xyz_class') ?? 'Z'),
        stock_status: String(data.get('stock_status') ?? 'ON_REQUEST'),
        compatibility_note: String(data.get('compatibility_note') ?? ''), published: data.get('published') === 'on',
      });
      setSelectedId(product.id); setCreating(false); setNotice('Producto creado correctamente.');
      await onReload();
    } catch (error) { setNotice(error instanceof Error ? error.message : 'No se pudo crear el producto'); }
    finally { setBusy(false); }
  }

  async function submitUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    const data = new FormData(event.currentTarget); const file = data.get('image');
    if (!(file instanceof File) || !file.size) { setNotice('Seleccione una imagen.'); return; }
    setBusy(true); setNotice('');
    try {
      await uploadProductImage(token, selected.id, file, String(data.get('alt_text') ?? selected.name), String(data.get('attribution') ?? ''));
      event.currentTarget.reset(); setNotice('Imagen cargada y asociada al producto.'); await onReload();
    } catch (error) { setNotice(error instanceof Error ? error.message : 'No se pudo cargar la imagen'); }
    finally { setBusy(false); }
  }

  async function savePricing(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    const data = new FormData(event.currentTarget); setBusy(true); setNotice('');
    try {
      await updateProduct(token, selected.id, {
        purchase_cost: String(data.get('purchase_cost') ?? '0'),
        landed_cost_factor: String(data.get('landed_cost_factor') ?? '1'),
        target_markup_percent: String(data.get('target_markup_percent') ?? '30'),
        minimum_markup_percent: String(data.get('minimum_markup_percent') ?? '0'),
        abc_class: String(data.get('abc_class') ?? 'C') as Product['abc_class'],
        xyz_class: String(data.get('xyz_class') ?? 'Z') as Product['xyz_class'],
      });
      setNotice('Regla de costo y reposicion actualizada.'); await onReload();
    } catch (error) { setNotice(error instanceof Error ? error.message : 'No se pudo guardar la regla'); }
    finally { setBusy(false); }
  }

  async function submitExternal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    const data = new FormData(event.currentTarget); setBusy(true); setNotice('');
    try {
      await addExternalImage(token, selected.id, {
        url: String(data.get('url') ?? ''), alt_text: String(data.get('alt_text') ?? selected.name),
        attribution: String(data.get('attribution') ?? ''), source_page_url: String(data.get('source_page_url') ?? '') || undefined,
      });
      event.currentTarget.reset(); setNotice('Imagen importada y copiada al almacenamiento administrado.'); await onReload();
    } catch (error) { setNotice(error instanceof Error ? error.message : 'No se pudo registrar la imagen'); }
    finally { setBusy(false); }
  }

  async function searchImages(event: FormEvent) {
    event.preventDefault(); if (!imageQuery.trim()) return;
    setBusy(true); setNotice('');
    try { setSearchResult(await searchGoogleImages(token, imageQuery)); }
    catch (error) { setNotice(error instanceof Error ? error.message : 'No se pudo ejecutar la búsqueda'); }
    finally { setBusy(false); }
  }

  async function useSearchImage(item: { image_url: string; source_page_url?: string; title: string; display_link?: string }) {
    if (!selected) return; setBusy(true);
    try {
      await addExternalImage(token, selected.id, {
        url: item.image_url, alt_text: item.title || selected.name, attribution: item.display_link,
        source_page_url: item.source_page_url, source: 'GOOGLE_SEARCH',
      });
      setNotice('Imagen seleccionada y registrada con su fuente.'); await onReload();
    } catch (error) { setNotice(error instanceof Error ? error.message : 'No se pudo registrar la imagen'); }
    finally { setBusy(false); }
  }

  return <div className="catalog-admin">
    <header className="content-header"><div><span>Catálogo y medios</span><h1>Repuestos publicados</h1><p>ERPNext conserva inventario y precio oficial; esta vista administra la presentación pública.</p></div><button className="primary-action" onClick={() => setCreating(!creating)}><PackagePlus size={17} /> Crear producto</button></header>
    {notice && <div className="notice" role="status"><CheckCircle2 size={17} />{notice}</div>}
    {creating && <form className="admin-form admin-form--product" onSubmit={submitProduct}>
      <div className="admin-form__heading"><h2>Nuevo producto</h2><p>Después de crearlo podrá cargar una o varias fotografías.</p></div>
      <label>SKU o número de parte<input required name="sku" /></label><label>Nombre<input required name="name" /></label>
      <label>Marca<input name="brand" /></label><label>Precio de exhibición<input required name="display_price" type="number" min="0" step="0.01" /></label>
      <label>Costo de compra<input required name="purchase_cost" type="number" min="0" step="0.01" /></label><label>Factor de importación<input required name="landed_cost_factor" type="number" min="1" step="0.0001" defaultValue="1" /></label>
      <label>Margen objetivo %<input required name="target_markup_percent" type="number" min="0" step="0.01" defaultValue="30" /></label><label>Margen mínimo %<input required name="minimum_markup_percent" type="number" min="0" step="0.01" defaultValue="0" /></label>
      <label>Clase ABC<select name="abc_class" defaultValue="C"><option>A</option><option>B</option><option>C</option></select></label><label>Variabilidad XYZ<select name="xyz_class" defaultValue="Z"><option>X</option><option>Y</option><option>Z</option></select></label>
      <label>Disponibilidad<select name="stock_status" defaultValue="ON_REQUEST"><option value="IN_STOCK">Disponible</option><option value="LOW_STOCK">Pocas unidades</option><option value="OUT_OF_STOCK">Agotado</option><option value="ON_REQUEST">Bajo pedido</option></select></label>
      <label className="admin-form__wide">Descripción<textarea name="description" rows={3} /></label>
      <label className="admin-form__wide">Nota de compatibilidad<textarea name="compatibility_note" rows={2} defaultValue="Validar por VIN antes de instalar." /></label>
      <label className="checkbox"><input type="checkbox" name="published" /> Publicar inmediatamente</label>
      <div className="admin-form__actions"><button type="button" onClick={() => setCreating(false)}>Cancelar</button><button className="primary-action" disabled={busy}>{busy ? <LoaderCircle className="spin" /> : <PackagePlus />} Guardar producto</button></div>
    </form>}

    <div className="catalog-admin__layout">
      <aside className="product-list"><div className="product-list__header"><strong>{products.length} productos</strong><Search size={16} /></div>{products.length === 0 && <p className="empty-copy">No hay productos creados.</p>}{products.map((product) => <button className={selected?.id === product.id ? 'product-list__item product-list__item--active' : 'product-list__item'} key={product.id} onClick={() => setSelectedId(product.id)}><span>{product.images[0] ? <img src={product.images.find((image) => image.is_primary)?.url ?? product.images[0].url} alt="" /> : <ImagePlus />}</span><div><strong>{product.name}</strong><small>{product.sku} · {product.brand ?? 'Sin marca'}</small></div><b>{product.published ? 'Publicado' : 'Borrador'}</b></button>)}</aside>
      <section className="media-manager">
        {!selected ? <div className="disabled-feature"><ImagePlus size={34} /><h2>Seleccione o cree un producto</h2></div> : <>
          <div className="media-manager__product"><div><small>{selected.sku}</small><h2>{selected.name}</h2><p>{selected.images.length} imagen(es) asociadas</p></div><strong>L {Number(selected.display_price).toLocaleString('es-HN', { minimumFractionDigits: 2 })}</strong></div>
          <form className="media-form catalog-pricing-policy" onSubmit={savePricing}><h3>Costo, importación y reposición</h3><p>El costo sincronizado desde ERPNext es la base. El factor incorpora flete, aduana y gastos; ningún descuento puede dejar la venta debajo del piso resultante.</p><div><label>Costo compra<input name="purchase_cost" type="number" min="0" step="0.01" defaultValue={selected.purchase_cost} /></label><label>Factor importación<input name="landed_cost_factor" type="number" min="1" step="0.0001" defaultValue={selected.landed_cost_factor} /></label><label>Margen objetivo %<input name="target_markup_percent" type="number" min="0" step="0.01" defaultValue={selected.target_markup_percent} /></label><label>Margen mínimo %<input name="minimum_markup_percent" type="number" min="0" step="0.01" defaultValue={selected.minimum_markup_percent} /></label><label>ABC<select name="abc_class" defaultValue={selected.abc_class}><option>A</option><option>B</option><option>C</option></select></label><label>XYZ<select name="xyz_class" defaultValue={selected.xyz_class}><option>X</option><option>Y</option><option>Z</option></select></label></div><button className="primary-action" disabled={busy}>Guardar regla comercial</button></form>
          <div className="image-gallery">{selected.images.length === 0 && <div className="image-gallery__empty"><ImagePlus /><span>Sin fotografías</span></div>}{selected.images.map((image) => <figure key={image.id}><img src={image.url} alt={image.alt_text} /><figcaption>{image.is_primary ? 'Principal · ' : ''}{image.source}</figcaption></figure>)}</div>
          <div className="media-tabs">
            <details open><summary><Upload size={17} /> Cargar desde la computadora</summary><form className="media-form" onSubmit={submitUpload}><p>Cargar JPEG, PNG o WEBP. Máximo configurado: 8 MB.</p><input aria-label="Seleccionar imagen del producto" required type="file" name="image" accept="image/jpeg,image/png,image/webp" /><input required name="alt_text" placeholder="Descripción accesible de la imagen" /><input name="attribution" placeholder="Autor o fuente, cuando corresponda" /><button className="primary-action" disabled={busy}>Subir imagen</button></form></details>
            <details><summary><CloudDownload size={17} /> URL externa</summary><form className="media-form" onSubmit={submitExternal}><input required type="url" name="url" placeholder="https://.../imagen.jpg" /><input required name="alt_text" placeholder="Descripción de la imagen" /><input name="attribution" placeholder="Autor o fuente" /><input type="url" name="source_page_url" placeholder="Página de origen" /><button className="primary-action" disabled={busy}>Registrar URL</button></form></details>
            <details><summary><Search size={17} /> Buscar con Google (opcional)</summary><form className="media-form media-form--search" onSubmit={searchImages}><p>Requiere Google Programmable Search configurado. La imagen elegida conserva su página de origen.</p><input value={imageQuery} onChange={(event) => setImageQuery(event.target.value)} placeholder={`${selected.name} ${selected.sku}`} /><button className="primary-action" disabled={busy}>Buscar</button></form>{searchResult && !searchResult.configured && <p className="configuration-note">Google Image Search no está configurado. Defina GOOGLE_CSE_API_KEY y GOOGLE_CSE_ID o utilice carga directa.</p>}<div className="search-image-grid">{searchResult?.items.map((item) => <button key={item.image_url} onClick={() => useSearchImage(item)}><img src={item.thumbnail_url ?? item.image_url} alt={item.title} /><span>Usar imagen</span></button>)}</div></details>
          </div>
        </>}
      </section>
    </div>
  </div>;
}
