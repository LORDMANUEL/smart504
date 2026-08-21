import { useEffect, useMemo, useState } from 'react';
import { Banknote, CarFront, CheckCircle2, ClipboardList, Copy, Minus, PackagePlus, Printer, RefreshCw, RotateCcw, Search, Send, ShieldCheck, ShoppingBasket } from 'lucide-react';
import { createCounterItemRequest, getAdminDocument, getCounterFitment, getCounterItemRequests } from '../lib/api';
import type { ApprovalRequest, CashSummary, CounterFitment, CounterItemRequest, CounterSale, CounterSalesContext, Quote, QuoteLine } from '../types';
import { useActionPrompt } from './ActionPrompt';

const money = (value: string | number) => new Intl.NumberFormat('es-HN', { style: 'currency', currency: 'HNL' }).format(Number(value));
type CartItem = CounterSalesContext['products'][number] & { quantity: number };

async function downloadReceipt(token: string, sale: CounterSale) {
  const blob = await getAdminDocument(token, `/api/v1/operations/finance/counter-sales/${sale.id}.pdf`);
  const url = URL.createObjectURL(blob); const link = document.createElement('a');
  link.href = url; link.download = `${sale.invoice_number}.pdf`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 15000);
}

export function CounterSalesView({ token, summary, context, sales, quotes, approvals, busy, onCreate, onQuote, onQuoteStatus, onRequestApproval, onReturn, onSync }: {
  token: string; summary: CashSummary; context: CounterSalesContext; sales: CounterSale[]; quotes: Quote[]; approvals: ApprovalRequest[]; busy: boolean;
  onCreate: (payload: {
    cash_session_id: string; branch_id: string; warehouse_id: string; customer_name: string;
    phone?: string; tax_id?: string; vehicle_vin?: string; discount: string; tax: string;
    method: string; reference?: string; actor: string; access_code: string;
    items: { product_id: string; quantity: string; unit_price: string }[];
  }) => Promise<void>;
  onQuote: (payload: { work_order_id?: string; customer_id?: string; vehicle_id?: string; notes: string; discount: string; tax: string; created_by: string; lines: QuoteLine[] }) => Promise<void>;
  onQuoteStatus: (quote: Quote, status: 'SENT' | 'APPROVED' | 'REJECTED') => Promise<void>;
  onRequestApproval: (sale: CounterSale, requestType: 'RETURN' | 'WARRANTY', saleItemId: string, quantity: string, reason: string, method: string, reference: string, ownerEmail: string) => Promise<void>;
  onReturn: (sale: CounterSale, approvalId: string, saleItemId: string, quantity: string, reason: string, method: string, reference: string, accessCode: string) => Promise<void>;
  onSync: (sale: CounterSale) => Promise<void>;
}) {
  const session = summary.session?.status === 'OPEN' ? summary.session : null;
  const [query, setQuery] = useState(''); const [cart, setCart] = useState<CartItem[]>([]);
  const [branchId, setBranchId] = useState(context.branches[0]?.id ?? '');
  const [warehouseId, setWarehouseId] = useState(context.warehouses.find((item) => item.branch_id === branchId)?.id ?? '');
  const [customerName, setCustomerName] = useState('Consumidor final'); const [phone, setPhone] = useState('');
  const [taxId, setTaxId] = useState(''); const [vin, setVin] = useState('');
  const [fitment, setFitment] = useState<CounterFitment | null>(null);
  const [fitmentBusy, setFitmentBusy] = useState(false);
  const [fitmentError, setFitmentError] = useState('');
  const [discount, setDiscount] = useState('0'); const [tax, setTax] = useState('0');
  const [method, setMethod] = useState('CASH'); const [reference, setReference] = useState('');
  const [requests, setRequests] = useState<CounterItemRequest[]>([]);
  const [requestQuantity, setRequestQuantity] = useState('1');
  const [requestNotes, setRequestNotes] = useState('');
  const [requestStatus, setRequestStatus] = useState('');
  const { ask, dialog: actionPrompt } = useActionPrompt();
  const products = useMemo(() => {
    const term = query.trim().toLowerCase();
    const allowed = fitment?.status === 'MATCHED' ? new Set(fitment.products.map((item) => item.id)) : null;
    return context.products.filter((item) => (!allowed || allowed.has(item.id)) && (!term || `${item.sku} ${item.name} ${item.compatibility_note ?? ''}`.toLowerCase().includes(term))).slice(0, 40);
  }, [context.products, fitment, query]);
  const subtotal = useMemo(() => cart.reduce((sum, item) => sum + item.quantity * Number(item.price), 0), [cart]);
  const total = subtotal - Number(discount || 0) + Number(tax || 0);
  const warehouses = useMemo(
    () => context.warehouses.filter((item) => item.branch_id === branchId),
    [context.warehouses, branchId],
  );
  const counterQuotes = useMemo(() => quotes.filter((quote) => quote.created_by === 'mostrador'), [quotes]);

  useEffect(() => {
    if (!branchId && context.branches.length) setBranchId(context.branches[0].id);
  }, [branchId, context.branches]);

  useEffect(() => {
    if (!warehouses.some((item) => item.id === warehouseId)) setWarehouseId(warehouses[0]?.id ?? '');
  }, [warehouseId, warehouses]);
  useEffect(() => { void getCounterItemRequests(token).then(setRequests).catch(() => setRequests([])); }, [token]);
  const stockFor = (product: CounterSalesContext['products'][number]) => Number(product.warehouse_stock?.[warehouseId] ?? (warehouseId ? 0 : product.stock_qty));
  const blockReasons = (product: CounterSalesContext['products'][number]) => {
    const reasons: CounterSalesContext['products'][number]['blocking_reasons'] = [...(product.blocking_reasons || [])].filter((reason) => reason !== 'SIN_EXISTENCIA');
    if (stockFor(product) <= 0) reasons.push('SIN_EXISTENCIA');
    return reasons;
  };
  const canSell = (product: CounterSalesContext['products'][number]) => blockReasons(product).length === 0;
  const reasonLabel = (product: CounterSalesContext['products'][number]) => blockReasons(product).map((reason) => ({ SIN_ITEM: 'sin código', SIN_PRECIO: 'sin precio', SIN_EXISTENCIA: 'sin existencia' }[reason])).join(', ');

  function catalogImage(product: CounterSalesContext['products'][number]) {
    if (product.image_url) return product.image_url;
    if (product.sku.includes('AIR')) return '/images/products/air-filter.png';
    if (product.sku.includes('BRK') || product.sku.includes('PAD')) return '/images/products/brake-pads.png';
    if (product.sku.includes('SPK') || product.sku.includes('SPARK')) return '/images/products/spark-plugs.png';
    return '/images/products/oil-filter.png';
  }

  async function findVin(event: React.FormEvent) {
    event.preventDefault();
    if (vin.trim().length < 11) return;
    setFitmentBusy(true); setFitmentError('');
    try {
      const result = await getCounterFitment(token, vin.trim().toUpperCase());
      setFitment(result);
      if (result.vehicle?.owner) setCustomerName(result.vehicle.owner);
      setQuery('');
    } catch (error) { setFitmentError(error instanceof Error ? error.message : 'No se pudo consultar el VIN.'); }
    finally { setFitmentBusy(false); }
  }

  function clearFitment() { setFitment(null); setFitmentError(''); setVin(''); setCustomerName('Consumidor final'); }

  function add(product: CounterSalesContext['products'][number]) {
    if (!canSell(product)) return;
    setCart((items) => {
      const current = items.find((item) => item.id === product.id);
      if (current) return items.map((item) => item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, stockFor(product)) } : item);
      return [...items, { ...product, quantity: 1 }];
    });
  }
  async function requestMissingItem(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim() || !branchId || !customerName.trim()) return;
    setRequestStatus('Enviando solicitud…');
    try {
      const created = await createCounterItemRequest(token, {
        search_query: query.trim(), customer_name: customerName.trim(), phone: phone || undefined,
        vehicle_vin: vin || undefined, quantity: requestQuantity, branch_id: branchId,
        warehouse_id: warehouseId || undefined, notes: requestNotes || undefined,
      });
      setRequests((items) => [created, ...items]); setRequestStatus(`Solicitud ${created.number} enviada a Compras.`);
      setRequestNotes(''); setRequestQuantity('1');
    } catch (error) { setRequestStatus(error instanceof Error ? error.message : 'No se pudo registrar la solicitud.'); }
  }
  function changeQuantity(id: string, quantity: number) {
    setCart((items) => items.map((item) => item.id === id ? { ...item, quantity: Math.max(1, Math.min(quantity, stockFor(item))) } : item));
  }
  async function checkout(event: React.FormEvent) {
    event.preventDefault(); if (!session || !cart.length || !branchId || !warehouseId) return;
    const accessCode = await ask('Autorizar venta de mostrador', { label: 'Código privado de cajera', inputType: 'password' }) || '';
    if (!accessCode) return;
    await onCreate({
      cash_session_id: session.id, branch_id: branchId, warehouse_id: warehouseId,
      customer_name: customerName, phone: phone || undefined, tax_id: taxId || undefined,
      vehicle_vin: vin || undefined, discount, tax, method, reference: reference || undefined,
      actor: 'cajera-mostrador', access_code: accessCode,
      items: cart.map((item) => ({ product_id: item.id, quantity: String(item.quantity), unit_price: item.price })),
    });
    setCart([]); setDiscount('0'); setTax('0'); setReference('');
  }
  async function saveQuote() {
    if (!cart.length || fitment?.status !== 'MATCHED' || !fitment.vehicle) return;
    await onQuote({
      customer_id: fitment.vehicle.customer_id, vehicle_id: fitment.vehicle.id,
      notes: 'Cotización creada desde venta por mostrador para seguimiento comercial.',
      discount, tax, created_by: 'mostrador',
      lines: cart.map((item) => ({ line_type: 'PART', code: item.sku, description: item.name, quantity: String(item.quantity), unit_price: item.price, unit_cost: item.purchase_cost, source_reference: item.id })),
    });
    setCart([]); setDiscount('0'); setTax('0');
  }
  async function requestApproval(sale: CounterSale, requestType: 'RETURN' | 'WARRANTY') {
    const item = sale.items.find((candidate) => Number(candidate.quantity) > Number(candidate.returned_quantity));
    if (!item) return;
    const quantity = await ask(`Cantidad para ${requestType === 'RETURN' ? 'devolver' : 'garantía'} de ${item.sku}`, { label: 'Cantidad', inputType: 'number', initialValue: '1' }) || '';
    if (!quantity) return;
    const reason = await ask(`Motivo documentado de la ${requestType === 'RETURN' ? 'devolución' : 'garantía'}`, { label: 'Motivo' }) || '';
    if (!reason) return;
    const ownerEmail = await ask('Correo del propietario que autoriza', { label: 'Correo', inputType: 'email', initialValue: context.owner_approval_email }) || '';
    if (!ownerEmail) return;
    await onRequestApproval(sale, requestType, item.id, quantity, reason, sale.payment_method, '', ownerEmail);
  }
  async function processApprovedReturn(sale: CounterSale, approval: ApprovalRequest) {
    const item = (approval.payload_json.items as Array<{ sale_item_id: string; quantity: string }> | undefined)?.[0];
    if (!item) return;
    const accessCode = await ask('Ejecutar devolución autorizada', { label: 'Código privado de cajera', inputType: 'password' }) || '';
    if (!accessCode) return;
    await onReturn(sale, approval.id, item.sale_item_id, item.quantity, approval.reason, String(approval.payload_json.method || sale.payment_method), String(approval.payload_json.reference || ''), accessCode);
  }

  return <div className="role-view counter-sales-view"><header className="content-header"><div><span>Venta directa de repuestos</span><h1>Mostrador</h1><p>Venta sin OT: existencia, cliente, cobro, factura, devolución y movimiento de caja en un solo flujo.</p></div></header>
    {!session && <section className="role-panel counter-warning"><Banknote /><div><h2>Abra Caja antes de vender</h2><p>El turno y fondo inicial se administran en Caja. Mostrador registra cada cobro dentro de ese turno.</p></div></section>}
    <form className="role-panel counter-fitment" onSubmit={findVin}><header><div><CarFront /><span><small>1. Vehículo</small><h2>Buscar por VIN</h2></span></div><button disabled={fitmentBusy}>{fitmentBusy ? 'Consultando…' : 'Consultar VIN'}</button></header><label><span>VIN registrado</span><input minLength={11} maxLength={40} value={vin} onChange={(event) => setVin(event.target.value.toUpperCase())} placeholder="Ej. 1FMCU0G6XLUA12545" /></label>
      {fitment?.status === 'MATCHED' && <div className="counter-fitment-result counter-fitment-result--matched"><CheckCircle2 /><span><strong>{fitment.vehicle?.label}</strong><small>{fitment.vehicle?.owner} · Placa {fitment.vehicle?.plate || 'sin placa'} · {fitment.products.length} piezas compatibles</small></span><button type="button" onClick={clearFitment}>Cambiar</button></div>}
      {fitment?.status === 'NOT_FOUND' && <div className="counter-fitment-result counter-fitment-result--unknown"><CarFront /><span><strong>VIN no registrado</strong><small>No se infiere compatibilidad. Puede buscar una pieza por nombre o SKU.</small></span><button type="button" onClick={clearFitment}>Limpiar</button></div>}
      {fitmentError && <p role="alert">{fitmentError}</p>}
    </form>
    <div className="counter-grid"><section className="role-panel counter-catalog"><header><div><small>2. Producto existente</small><h2>{fitment?.status === 'MATCHED' ? `Piezas para ${fitment.vehicle?.label}` : 'Inventario de la bodega'}</h2></div><label><Search /><input aria-label="Buscar repuesto" placeholder="Nombre, SKU u OEM" value={query} onChange={(event) => setQuery(event.target.value)} /></label></header><p className="counter-catalog-rule">Mostrador sólo selecciona artículos creados en Catálogo/ERP. No puede crear ni alterar el precio.</p><div className="counter-product-list">{products.map((product) => <article key={product.id} className={!canSell(product) ? 'counter-product--blocked' : ''}><img src={catalogImage(product)} alt={`Imagen de referencia de ${product.name}`} /><div><strong>{product.name}</strong><small>{product.sku} · {product.compatibility_note || 'Validar aplicación'} · Bodega: {stockFor(product)}</small><small>{canSell(product) ? `Disponible para vender · Piso ${money(product.minimum_sale_price)}` : `No vendible: ${reasonLabel(product)}`}</small></div><b>{money(product.price)}</b><button type="button" disabled={!canSell(product)} onClick={() => add(product)} aria-label={`Agregar ${product.name}`}><PackagePlus /></button></article>)}{!products.length && <p>No hay coincidencias en los artículos existentes.</p>}</div>
      <form className="counter-demand-form" onSubmit={requestMissingItem}><header><PackagePlus /><div><h3>¿No está disponible?</h3><p>Registre lo que pidió el cliente; Compras verá la demanda sin crear un artículo desde caja.</p></div></header><div><label>Búsqueda solicitada<input required minLength={2} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ej. sensor ABS Escape 2020" /></label><label>Cantidad<input required type="number" min="1" step="1" value={requestQuantity} onChange={(event) => setRequestQuantity(event.target.value)} /></label><label className="counter-demand-notes">Detalle<textarea value={requestNotes} onChange={(event) => setRequestNotes(event.target.value)} placeholder="Marca, lado, urgencia o cuándo llamar" /></label></div><button disabled={!query.trim() || !branchId}>Solicitar a Compras</button>{requestStatus && <p role="status">{requestStatus}</p>}</form>
      {requests.length > 0 && <div className="counter-demand-history"><strong>Últimas solicitudes</strong>{requests.slice(0, 4).map((item) => <span key={item.id}><b>{item.number}</b><small>{item.search_query} · {item.quantity} · {item.status}</small></span>)}</div>}
    </section>
      <form className="role-panel counter-cart" onSubmit={checkout}><header><ShoppingBasket /><div><h2>Carrito de mostrador</h2><p>{cart.length} productos diferentes</p></div></header><div className="counter-scope"><label>Sucursal<select value={branchId} onChange={(event) => { const next = event.target.value; setBranchId(next); setWarehouseId(context.warehouses.find((item) => item.branch_id === next)?.id ?? ''); }}>{context.branches.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><label>Bodega<select value={warehouseId} onChange={(event) => setWarehouseId(event.target.value)}>{warehouses.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label></div><div className="counter-cart-lines">{cart.map((item) => <article key={item.id}><button type="button" aria-label={`Quitar ${item.name}`} onClick={() => setCart((items) => items.filter((candidate) => candidate.id !== item.id))}><Minus /></button><span><strong>{item.name}</strong><small>{item.sku} · {money(item.price)}</small></span><input aria-label={`Cantidad ${item.name}`} type="number" min="1" max={stockFor(item)} value={item.quantity} onChange={(event) => changeQuantity(item.id, Number(event.target.value))} /><b>{money(item.quantity * Number(item.price))}</b></article>)}{!cart.length && <p>Seleccione repuestos del catálogo.</p>}</div><div className="counter-customer"><label>Cliente<input required value={customerName} onChange={(event) => setCustomerName(event.target.value)} /></label><label>Teléfono<input value={phone} onChange={(event) => setPhone(event.target.value)} /></label><label>RTN<input value={taxId} onChange={(event) => setTaxId(event.target.value)} /></label><label>VIN opcional<input value={vin} onChange={(event) => setVin(event.target.value.toUpperCase())} /></label><label>Descuento<input type="number" min="0" step="0.01" value={discount} onChange={(event) => setDiscount(event.target.value)} /></label><label>Impuesto<input type="number" min="0" step="0.01" value={tax} onChange={(event) => setTax(event.target.value)} /></label><label>Método<select value={method} onChange={(event) => setMethod(event.target.value)}><option value="CASH">Efectivo</option><option value="CARD">Tarjeta / POS</option><option value="TRANSFER">Transferencia</option></select></label>{method !== 'CASH' && <label>Referencia<input required value={reference} onChange={(event) => setReference(event.target.value)} /></label>}</div><div className="counter-total"><span>Total a cobrar</span><strong>{money(total)}</strong></div><div className="counter-checkout-actions"><button type="button" disabled={busy || !cart.length || fitment?.status !== 'MATCHED'} onClick={() => void saveQuote()}><ClipboardList /> Guardar cotización y seguimiento</button><button className="role-primary" disabled={busy || !session || !cart.length || total <= 0}><Banknote /> Cobrar, descontar existencia y facturar</button></div>{fitment?.status !== 'MATCHED' && cart.length > 0 && <small>Para cotizar identifique primero el VIN y propietario. La venta inmediata puede continuar como consumidor final.</small>}</form></div>
    <section className="role-panel counter-quote-followup"><header><div><h2>Cotizaciones y pedidos de mostrador</h2><p>Seguimiento antes de cobrar: creada, enviada, aprobada o no concretada.</p></div></header><div className="counter-quote-kanban">{[{ status: 'DRAFT', label: 'Por contactar' }, { status: 'SENT', label: 'En seguimiento' }, { status: 'APPROVED', label: 'Venta aprobada' }, { status: 'REJECTED', label: 'No concretada' }].map((column) => <section key={column.status}><header><b>{column.label}</b><span>{counterQuotes.filter((quote) => quote.status === column.status).length}</span></header>{counterQuotes.filter((quote) => quote.status === column.status).map((quote) => <article key={quote.id}><small>{quote.number}</small><strong>{money(quote.total)}</strong><span>{quote.lines.length} repuestos</span>{quote.status === 'DRAFT' && <button onClick={() => void onQuoteStatus(quote, 'SENT')}><Send /> Contactar</button>}{quote.status === 'SENT' && <div><button onClick={() => void onQuoteStatus(quote, 'APPROVED')}><CheckCircle2 /> Aprobar</button><button onClick={() => void onQuoteStatus(quote, 'REJECTED')}>No se vendió</button></div>}</article>)}</section>)}</div></section>
    <section className="role-panel counter-approvals"><header><div><h2>Autorizaciones de devolución y garantía</h2><p>El enlace vence y sólo el propietario decide. Caja ejecuta el movimiento después de la aprobación.</p></div></header><div>{approvals.map((approval) => <article key={approval.id}><span><strong>{approval.request_type === 'RETURN' ? 'Devolución' : 'Garantía'} · {approval.status}</strong><small>{approval.reason}</small><small>Correo: {approval.owner_email} · {approval.delivery_status}</small>{approval.delivery_error && <small>{approval.delivery_error}</small>}</span>{approval.approval_url && <button onClick={() => void navigator.clipboard.writeText(approval.approval_url || '')}><Copy /> Copiar enlace</button>}{approval.status === 'APPROVED' && approval.request_type === 'RETURN' && <button className="role-primary" onClick={() => { const sale = sales.find((item) => item.id === approval.sale_id); if (sale) void processApprovedReturn(sale, approval); }}><RotateCcw /> Ejecutar devolución</button>}</article>)}{!approvals.length && <p>No hay autorizaciones solicitadas.</p>}</div></section>
    <section className="role-panel counter-history"><header><div><h2>Ventas y devoluciones</h2><p>Historial con factura descargable y estado contable verificable.</p></div></header><div>{sales.map((sale) => <article key={sale.id}><span><strong>{sale.invoice_number}</strong><small>{sale.customer_name} · {new Date(sale.completed_at).toLocaleString('es-HN')}</small>{sale.erpnext_invoice_id && <small>ERP: {sale.erpnext_invoice_id}</small>}{sale.sync_error && <small className="counter-sync-error">{sale.sync_error}</small>}</span><em>{sale.status}</em><em className={`counter-sync counter-sync--${sale.sync_status.toLowerCase()}`}>{sale.sync_status === 'SYNCED' ? 'Contabilizada' : sale.sync_status === 'FAILED' ? 'Error ERP' : sale.sync_status === 'SYNCING' ? 'Sincronizando' : 'Pendiente ERP'}</em><b>{money(sale.total)}</b>{sale.sync_status !== 'SYNCED' && <button disabled={busy || sale.sync_status === 'SYNCING'} onClick={() => void onSync(sale)}><RefreshCw /> Reintentar ERP</button>}<button onClick={() => void downloadReceipt(token, sale)}><Printer /> PDF</button><button disabled={sale.status === 'RETURNED'} onClick={() => void requestApproval(sale, 'RETURN')}><RotateCcw /> Solicitar devolución</button><button onClick={() => void requestApproval(sale, 'WARRANTY')}><ShieldCheck /> Solicitar garantía</button></article>)}{!sales.length && <p>No hay ventas de mostrador todavía.</p>}</div></section>
    {actionPrompt}
  </div>;
}
