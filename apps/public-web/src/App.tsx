import { useDeferredValue, useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, BadgeCheck, CarFront, CheckCircle2, ChevronRight, ClipboardCheck, Gauge,
  Menu, PackageSearch, Search, ShieldCheck, ShoppingBag, Sparkles, Wrench, X,
} from 'lucide-react';
import { Brand } from './components/Brand';
import { BookingForm } from './components/BookingForm';
import { ChatWidget } from './components/ChatWidget';
import { CheckoutDrawer } from './components/CheckoutDrawer';
import { AccessHub, CustomerAccess, CustomerPortal } from './components/CustomerExperience';
import { ProductCard } from './components/ProductCard';
import { getProducts, getStorePromotions, getVehicleFitment } from './lib/api';
import { useBranding } from './lib/branding';
import { seasonalThemes } from './lib/seasonalThemes';
import type { Product, StorePromotion, VehicleFitment } from './types';
import './styles.css';


const stockPhotos = {
  hero: {
    local: '/images/stock/workshop-hero.jpg',
    fallback: 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Auto_workshop01.jpg?width=1600',
  },
  diagnostic: {
    local: '/images/stock/diagnostic-service.jpg',
    fallback: 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Mechanic_repairing_car_engine.jpg?width=1400',
  },
  technician: {
    local: '/images/stock/technician-work.jpg',
    fallback: 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Mechanic_repairing_car_engine_1.jpg?width=1400',
  },
  engine: {
    local: '/images/stock/engine-service.jpg',
    fallback: 'https://commons.wikimedia.org/wiki/Special:Redirect/file/Auto_workshop02.jpg?width=1400',
  },
} as const;

type StockPhoto = (typeof stockPhotos)[keyof typeof stockPhotos];

function ExistingPhoto({ photo, alt, loading }: { photo: StockPhoto; alt: string; loading?: 'lazy' | 'eager' }) {
  return (
    <img
      src={photo.local}
      alt={alt}
      loading={loading}
      onError={(event) => {
        event.currentTarget.onerror = null;
        event.currentTarget.src = photo.fallback;
      }}
    />
  );
}

const services = [
  { title: 'Diagnóstico electrónico', text: 'Lectura, pruebas dirigidas y evidencia antes de reemplazar componentes.', icon: Gauge },
  { title: 'Programación y módulos', text: 'Configuración, adaptación y soporte especializado para sistemas electrónicos.', icon: Sparkles },
  { title: 'Transmisión y tren motriz', text: 'Diagnóstico, mantenimiento y reparación con trazabilidad de cada operación.', icon: Wrench },
  { title: 'Mantenimiento preventivo', text: 'Planes por kilometraje, historial por VIN y recordatorios de próxima atención.', icon: ClipboardCheck },
];

const process = [
  ['01', 'Recibimos', 'Documentamos síntomas, kilometraje y condición del vehículo.'],
  ['02', 'Diagnosticamos', 'El técnico registra pruebas, DTC, hallazgos y evidencia.'],
  ['03', 'Cotizamos', 'Se separan mano de obra, repuestos y trabajos opcionales.'],
  ['04', 'Usted aprueba', 'La cotización puede aprobarse de forma clara y trazable.'],
  ['05', 'Reparamos', 'Controlamos tiempos, repuestos, técnico y estado de la OT.'],
  ['06', 'Entregamos', 'Verificamos calidad, facturamos y conservamos el historial.'],
];

const businessPhone = (import.meta.env.VITE_BUSINESS_PHONE ?? '').trim() || 'Teléfono por confirmar';
const businessEmail = (import.meta.env.VITE_BUSINESS_EMAIL ?? '').trim() || 'info@smartdiag504.com';
const businessAddress = (import.meta.env.VITE_BUSINESS_ADDRESS ?? '').trim() || 'San Pedro Sula, Honduras';

function PatrioticSplash({ active }: { active: boolean }) {
  const [visible, setVisible] = useState(() => active && sessionStorage.getItem('smartdiag-patria-welcome') !== 'seen');
  useEffect(() => {
    if (!visible) return undefined;
    sessionStorage.setItem('smartdiag-patria-welcome', 'seen');
    const timer = window.setTimeout(() => setVisible(false), 2600);
    return () => window.clearTimeout(timer);
  }, [visible]);
  if (!visible) return null;
  return <div className="patriotic-splash" role="status" aria-label="Bienvenida del mes de la patria" onClick={() => setVisible(false)}>
    <img src="/images/seasonal/patria-welcome.gif" alt="Fiestas patrias de Honduras" width="420" height="260" />
    <span>Toque para continuar</span>
  </div>;
}

function PublicLanding() {
  const [menuOpen, setMenuOpen] = useState(false);
  const branding = useBranding();
  const phone = branding.phone || businessPhone;
  const email = branding.email || businessEmail;
  const address = branding.address || businessAddress;
  const telephoneHref = /^\+?[0-9 ()-]{7,}$/.test(phone)
    ? `tel:${phone.replace(/[^0-9+]/g, '')}`
    : null;
  const seasonalTheme = branding.seasonal_theme_enabled && branding.seasonal_theme_code !== 'NONE' ? seasonalThemes[branding.seasonal_theme_code] : null;
  const isPatriaTheme = branding.seasonal_theme_enabled && branding.seasonal_theme_code === 'PATRIA_SEPTEMBER';

  useEffect(() => {
    if (!isPatriaTheme) return undefined;
    const preload = document.createElement('link');
    preload.rel = 'preload';
    preload.as = 'image';
    preload.type = 'image/webp';
    preload.href = '/images/seasonal/september-patria-hero.webp';
    preload.fetchPriority = 'high';
    document.head.appendChild(preload);
    return () => preload.remove();
  }, [isPatriaTheme]);

  return (
    <div className="site-shell">
      <PatrioticSplash active={isPatriaTheme} />
      {seasonalTheme ? (
        <aside className={`seasonal-banner seasonal-banner--${branding.seasonal_theme_code.toLowerCase()}`} aria-label={`Tema especial: ${seasonalTheme.shortLabel}`}>
          <div className="seasonal-banner__flag" aria-hidden="true"><i /><i /><i /><span className="seasonal-banner__stars"><b /><b /><b /><b /><b /></span></div>
          {isPatriaTheme
            ? <img className="seasonal-banner__image" src="/images/seasonal/honduras-flag.webp" alt="" width="48" height="48" decoding="async" />
            : <span className="seasonal-banner__symbol" aria-hidden="true">{seasonalTheme.symbol}</span>}
          <div className="seasonal-banner__copy">
            <strong>{branding.seasonal_theme_title || seasonalTheme.title}</strong>
            <small>{branding.seasonal_theme_message || seasonalTheme.message}</small>
          </div>
          <div className="seasonal-banner__decor" aria-hidden="true">
            {Array.from({ length: 9 }, (_, index) => <i key={index} />)}
          </div>
        </aside>
      ) : null}
      <header className="site-header">
        <div className="container site-header__inner">
          <a href="#inicio" className="brand-link"><Brand /></a>
          <nav className={menuOpen ? 'site-nav site-nav--open' : 'site-nav'} aria-label="Navegación principal">
            <a href="#servicios" onClick={() => setMenuOpen(false)}>Servicios</a>
            <a href="#proceso" onClick={() => setMenuOpen(false)}>Cómo trabajamos</a>
            <a href="/lading/repuestos" onClick={() => setMenuOpen(false)}>Repuestos</a>
            <a href="#reservar" onClick={() => setMenuOpen(false)}>Reservar</a>
            <a href="/lading/acceso" onClick={() => setMenuOpen(false)}>Comprar / Mi vehículo</a>
          </nav>
          <div className="site-header__actions">
            <a className="button button--nav" href="#reservar">Reservar cita</a>
            <a className="button button--client" href="/lading/acceso">Ingresar</a>
            <button className="menu-button" type="button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Abrir menú">
              {menuOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </header>

      <main>
        <section id="inicio" className={isPatriaTheme ? 'hero hero--patria' : 'hero'}>
          <div className="container hero__grid">
            <div className="hero__copy">
              <h1>Diagnóstico preciso.<br /><span>Decisiones claras.</span></h1>
              <p>{branding.display_name} combina experiencia técnica, evidencia y seguimiento digital para reparar lo necesario y conservar el historial completo de su vehículo.</p>
              <div className="hero__actions">
                <a className="button button--gold" href="#reservar">Reservar diagnóstico <ArrowRight size={18} /></a>
                <a className="text-link" href="/lading/repuestos">Comprar repuestos <ChevronRight size={17} /></a>
              </div>
              <div className="hero__trust" aria-label="Características del servicio">
                <span><BadgeCheck size={18} /> Cotización trazable</span>
                <span><ShieldCheck size={18} /> Historial por VIN</span>
                <span><CarFront size={18} /> Seguimiento de OT</span>
              </div>
            </div>
            <div className="hero__media" aria-hidden={isPatriaTheme || undefined}>
              <ExistingPhoto photo={stockPhotos.hero} alt="Vehículo dentro de un taller automotriz profesional" loading="eager" />
              <div className="hero__status">
                <span className="status-dot" />
                <div><small>Su vehículo, visible</small><strong>Seguimiento desde recepción hasta factura</strong></div>
              </div>
            </div>
          </div>
        </section>

        <section className="assurance-strip" aria-label="Compromisos de servicio">
          <div className="container assurance-strip__grid">
            <div>{isPatriaTheme ? <img className="assurance-strip__seasonal" src="/images/seasonal/honduras-flag.webp" alt="Bandera de Honduras con cinco estrellas" width="72" height="72" loading="lazy" decoding="async" /> : null}<span><strong>Diagnóstico antes de reemplazar</strong><span>Pruebas y hallazgos registrados</span></span></div>
            <div>{isPatriaTheme ? <img className="assurance-strip__seasonal" src="/images/seasonal/guacamaya.webp" alt="Guacamaya roja, ave nacional de Honduras" width="72" height="72" loading="lazy" decoding="async" /> : null}<span><strong>Aprobación antes de ejecutar</strong><span>Costos separados y comprensibles</span></span></div>
            <div>{isPatriaTheme ? <img className="assurance-strip__seasonal" src="/images/seasonal/orquidea.webp" alt="Orquídea nacional de Honduras" width="72" height="72" loading="lazy" decoding="async" /> : null}<span><strong>Historial que permanece</strong><span>Trabajo, repuestos y recomendaciones</span></span></div>
          </div>
        </section>

        <section id="servicios" className="section services-section">
          <div className="container">
            <div className="section-heading section-heading--split">
              <div><span className="section-number">01</span><h2>Especialistas en encontrar la causa, no en adivinar piezas.</h2></div>
              <p>La orden de trabajo conecta lo que usted reporta con las pruebas del técnico, la cotización, los repuestos y el resultado final.</p>
            </div>
            <div className="services-layout">
              <div className="services-image"><ExistingPhoto photo={stockPhotos.diagnostic} loading="lazy" alt="Técnico realizando diagnóstico automotriz" /></div>
              <div className="services-list">
                {services.map(({ title, text, icon: Icon }, index) => (
                  <article className="service-row" key={title}>
                    <span className="service-row__icon"><Icon size={23} /></span>
                    <div><h3>{title}</h3><p>{text}</p></div>
                    <span className="service-row__index">0{index + 1}</span>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="proceso" className="section process-section">
          <div className="container">
            <div className="section-heading section-heading--center">
              <span className="section-number">02</span>
              <h2>Un proceso que usted puede entender y nosotros podemos auditar.</h2>
            </div>
            <div className="process-grid">
              {process.map(([number, title, text]) => (
                <article className="process-step" key={number}><strong>{number}</strong><h3>{title}</h3><p>{text}</p></article>
              ))}
            </div>
          </div>
        </section>

        <section className="section digital-section">
          <div className="container digital-section__grid">
            <div className="digital-section__copy">
              <span className="section-number">03</span>
              <h2>La tecnología acompaña al taller, no sustituye al técnico.</h2>
              <p>Cada OT conserva el vehículo, el diagnóstico, el técnico, las aprobaciones, los repuestos y la factura en una sola línea de tiempo.</p>
              <ul>
                <li><BadgeCheck /> Evidencia organizada por OT y VIN</li>
                <li><BadgeCheck /> Estados operativos visibles</li>
                <li><BadgeCheck /> Repuestos vinculados a la reparación</li>
                <li><BadgeCheck /> Historial para la próxima visita</li>
              </ul>
            </div>
            <div className="digital-section__visual">
              <ExistingPhoto photo={stockPhotos.technician} loading="lazy" alt="Técnico trabajando en un vehículo" />
              <div className="workflow-card">
                <small>Estado actual</small><strong>OT pendiente aprobación cliente</strong>
                <div className="workflow-line"><span className="done" /><span className="done" /><span className="active" /><span /><span /><span /></div>
                <p>Cotización técnica enviada con repuestos y mano de obra separados.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="repuestos" className="section catalog-section">
          <div className="container">
            <div className="section-heading section-heading--catalog">
              <div><span className="section-number">04</span><h2>Repuestos con origen, precio y compatibilidad verificable.</h2></div>
              <p>La tienda en línea filtra el catálogo por su vehículo. Antes de instalar, nuestro equipo puede confirmar la aplicación mediante VIN.</p>
            </div>
            <div className="landing-store-teaser">
              <PackageSearch size={42} />
              <div><strong>Ford Escape 2020, Ford F-150 2020 y Honda Civic 2008</strong><p>Consulte piezas compatibles, precio al cliente y disponibilidad sin exponer información interna del taller.</p></div>
              <a className="button button--gold" href="/lading/repuestos">Ir a la tienda <ArrowRight size={17} /></a>
            </div>
          </div>
        </section>

        <section id="reservar" className="section booking-section">
          <div className="container booking-section__grid">
            <div className="booking-section__copy">
              <span className="section-number">05</span>
              <h2>Cuéntenos qué ocurre con su vehículo.</h2>
              <p>La reserva inicia una solicitud; nuestro equipo confirma fecha, alcance del diagnóstico y datos necesarios antes de recibir el vehículo.</p>
              <ExistingPhoto photo={stockPhotos.engine} loading="lazy" alt="Servicio técnico en el compartimiento del motor" />
            </div>
            <BookingForm />
          </div>
        </section>
      </main>

      <ChatWidget />

      <footer className="site-footer">
        <div className="container site-footer__grid">
          <div><Brand /><p>Diagnóstico automotriz, reparación especializada, mantenimiento y repuestos con trazabilidad.</p></div>
          <div><h3>Contacto</h3>{telephoneHref ? <a href={telephoneHref}>{phone}</a> : <span>{phone}</span>}<a href={`mailto:${email}`}>{email}</a><span>{address}</span></div>
          <div><h3>Accesos</h3><a href="#reservar">Reservar servicio</a><a href="/lading/repuestos">Comprar repuestos</a><a href="/lading/acceso">Ingresar / Mi vehículo</a><a href="/tallerv1/login">Acceso del taller</a></div>
        </div>
        <div className="container site-footer__bottom"><span>© 2026 {branding.display_name}</span><span>Fotografías con procedencia documentada; sustituibles desde la administración de marca.</span></div>
      </footer>
    </div>
  );
}

function PartsStorefront() {
  const branding = useBranding();
  const isPatriaTheme = branding.seasonal_theme_enabled && branding.seasonal_theme_code === 'PATRIA_SEPTEMBER';
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);
  const [vin, setVin] = useState('');
  const [fitment, setFitment] = useState<VehicleFitment | null>(null);
  const [fitmentState, setFitmentState] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [products, setProducts] = useState<Product[]>([]);
  const [catalogState, setCatalogState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [cart, setCart] = useState<Product[]>([]);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [promotions, setPromotions] = useState<StorePromotion[]>([]);
  const [promoCode, setPromoCode] = useState('');

  useEffect(() => { void getStorePromotions().then(setPromotions).catch(() => setPromotions([])); }, []);

  useEffect(() => {
    const controller = new AbortController();
    setCatalogState('loading');
    if (fitment?.status === 'MATCHED') {
      const term = deferredQuery.trim().toLowerCase();
      setProducts(fitment.products.filter((product) => !term || `${product.sku} ${product.name} ${product.brand ?? ''}`.toLowerCase().includes(term)));
      setCatalogState('ready');
      return () => controller.abort();
    }
    getProducts(deferredQuery, controller.signal)
      .then((page) => { setProducts(page.items); setCatalogState('ready'); })
      .catch((error) => { if ((error as Error).name !== 'AbortError') setCatalogState('error'); });
    return () => controller.abort();
  }, [deferredQuery, fitment]);

  async function validateVin(event: React.FormEvent) {
    event.preventDefault();
    if (vin.trim().length < 11) return;
    setFitmentState('loading');
    try {
      const result = await getVehicleFitment(vin.trim().toUpperCase());
      setFitment(result); setFitmentState('ready'); setQuery('');
    } catch { setFitmentState('error'); }
  }

  function clearFitment() { setFitment(null); setFitmentState('idle'); setVin(''); }
  const cartTotal = useMemo(() => cart.reduce((total, item) => total + Number(item.display_price), 0), [cart]);

  return <div className="site-shell store-page">
    <PatrioticSplash active={isPatriaTheme} />
    <a className="skip-link" href="#catalogo-principal">Saltar al catálogo</a>
    <header className="site-header"><div className="container site-header__inner">
      <a href="/lading" className="brand-link"><Brand /></a>
      <nav className="site-nav"><a href="/lading">Taller</a><a href="/lading/loginclie">Mi vehículo</a></nav>
      <div className="site-header__actions"><button className="cart-button" type="button" onClick={() => setCheckoutOpen(true)} aria-label={`Carrito con ${cart.length} artículos`}><ShoppingBag size={19} /><span>{cart.length}</span></button><a className="button button--client" href="/lading/loginclie">Ingresar</a></div>
    </div></header>
    {promotions.filter((item) => item.store_banner !== false).slice(0, 1).map((promotion) => <aside className="store-promotion-banner" key={promotion.id}>
      {promotion.media_url && promotion.media_type === 'IMAGE' ? <img src={promotion.media_url} alt="" loading="eager" decoding="async" /> : null}
      <div><small>{promotion.audience}</small><strong>{promotion.title}</strong><span>{promotion.description}</span></div>
      {promotion.discount_percent ? <b>{promotion.discount_percent}% menos</b> : null}
      {promotion.promo_code ? <button type="button" onClick={() => { setPromoCode(promotion.promo_code ?? ''); setCheckoutOpen(true); }}>Usar código {promotion.promo_code}</button> : <a href={promotion.public_path}>{promotion.call_to_action}</a>}
    </aside>)}
    <main className="section catalog-section" id="catalogo-principal" tabIndex={-1}><div className="container">
      <div className="store-heading"><h1>Encuentre el repuesto correcto.</h1><p>Valide un vehículo registrado o busque libremente por pieza. Nunca inferimos compatibilidad de un VIN desconocido.</p></div>
      <div className="fitment-search-grid">
        <form className="fitment-panel" onSubmit={validateVin}><div><CarFront /><span><strong>Buscar por vehículo (VIN)</strong><small>Mostramos sólo compatibilidad guardada.</small></span></div><label>VIN del vehículo<span><input minLength={11} maxLength={40} value={vin} onChange={(event) => setVin(event.target.value.toUpperCase())} placeholder="Ej. 1FMCU0G6XLUA12545" /><button disabled={fitmentState === 'loading'}>{fitmentState === 'loading' ? 'Consultando…' : 'Validar VIN'}</button></span></label></form>
        <div className="part-search-panel"><div><Search /><span><strong>Buscar por nombre o número de parte</strong><small>Nombre, marca, SKU u OEM.</small></span></div><label className="search-field"><Search size={20} /><input type="search" role="searchbox" aria-label="Buscar repuesto" placeholder="Filtro, pastillas, bujías o SKU" value={query} onChange={(event) => setQuery(event.target.value)} /></label></div>
      </div>
      {fitment?.status === 'MATCHED' && <section className="fitment-result fitment-result--matched"><CheckCircle2 /><div><strong>{fitment.vehicle?.label}</strong><span>{fitment.products.length} repuestos compatibles registrados</span></div><button type="button" onClick={clearFitment}>Cambiar vehículo</button></section>}
      {fitment?.status === 'NOT_FOUND' && <section className="fitment-result fitment-result--unknown"><CarFront /><div><strong>VIN no registrado</strong><span>No adivinamos el vehículo. Revise el VIN o utilice la búsqueda por nombre/SKU.</span></div><button type="button" onClick={clearFitment}>Limpiar VIN</button></section>}
      {fitment?.status === 'AUTH_REQUIRED' && <section className="fitment-result fitment-result--unknown" role="status"><CarFront /><div><strong>Protegemos los datos de su vehículo</strong><span>Ingrese al portal del cliente para consultar por VIN. También puede buscar aquí por nombre, marca, SKU u OEM.</span></div><a className="button button--client" href="/lading/loginclie">Ingresar para validar VIN</a></section>}
      {fitmentState === 'error' && <section className="fitment-result fitment-result--unknown"><CarFront /><div><strong>No fue posible validar el VIN</strong><span>Puede continuar usando la búsqueda libre.</span></div></section>}
      <div className="catalog-results-heading"><div><strong>{fitment?.status === 'MATCHED' ? `Piezas para ${fitment.vehicle?.label}` : 'Catálogo de repuestos'}</strong><span>{catalogState === 'ready' ? `${products.length} resultados` : 'Consultando catálogo'}</span></div></div>
      {catalogState === 'error' && <div className="catalog-message"><PackageSearch /><div><strong>Catálogo temporalmente no disponible</strong><p>Reserve una validación desde la página del taller.</p></div></div>}
      {catalogState === 'ready' && products.length === 0 && <div className="catalog-message"><PackageSearch /><div><strong>No encontramos coincidencias</strong><p>Revise el nombre, SKU o VIN registrado.</p></div></div>}
      <div className="product-grid">{products.map((product) => <ProductCard key={product.id} product={product} onAdd={(item) => setCart((current) => [...current, item])} />)}</div>
      {cart.length > 0 && <div className="cart-summary" role="status"><span>{cart.length} artículo(s)</span><strong>{new Intl.NumberFormat('es-HN', { style: 'currency', currency: 'HNL' }).format(cartTotal)}</strong><button type="button" onClick={() => setCheckoutOpen(true)}>Solicitar pedido <ArrowRight size={17} /></button></div>}
    </div></main>
    <CheckoutDrawer open={checkoutOpen} cart={cart} initialPromoCode={promoCode} onClose={() => setCheckoutOpen(false)} onRemove={(productId) => setCart((current) => current.filter((item) => item.id !== productId))} onCompleted={() => setCart([])} />
  </div>;
}

export default function App() {
  const [path, setPath] = useState(window.location.pathname.replace(/\/$/, '') || '/');
  useEffect(() => {
    const updatePath = () => setPath(window.location.pathname.replace(/\/$/, '') || '/');
    window.addEventListener('popstate', updatePath);
    return () => window.removeEventListener('popstate', updatePath);
  }, []);
  if (path === '/lading/loginclie') return <CustomerAccess />;
  if (path === '/lading/acceso') return <AccessHub />;
  if (path === '/lading/cliente') return <CustomerPortal />;
  if (path === '/lading/repuestos') return <PartsStorefront />;
  return <PublicLanding />;
}
