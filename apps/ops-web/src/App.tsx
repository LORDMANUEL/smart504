import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Activity, Bell, BookOpenCheck, Boxes, Building2, CalendarDays, Columns3, FileCog, Gauge, HardHat, HeartPulse, Landmark, LayoutGrid, LogOut, Menu,
  CarFront, Megaphone, PackageOpen, PackageSearch, RefreshCw, Route, Search, Settings, ShoppingCart, Store, UserCog, UserRoundSearch, UsersRound, Warehouse, X,
} from 'lucide-react';
import { BaysView } from './components/BaysView';
import { BookingsView } from './components/BookingsView';
import { Brand } from './components/Brand';
import { CatalogManager } from './components/CatalogManager';
import { CashierModule, QuotesView } from './components/FinanceViews';
import { KanbanBoard } from './components/KanbanBoard';
import { Login } from './components/Login';
import { SettingsView } from './components/SettingsView';
import { AdminOverview, FlowAnalytics, MarketingDisplay, MarketingView, WarehouseView } from './components/RoleViews';
import { EnterpriseWorkspace } from './components/EnterpriseWorkspace';
import { StoreOrdersView } from './components/StoreOrdersView';
import { LeadsKanbanView, ManagementView, ProcessControlView } from './components/OperationsControlViews';
import { SystemStatus } from './components/SystemStatus';
import { WorkOrderDetail } from './components/WorkOrderDetail';
import { DocumentTemplateCenter } from './components/DocumentTemplateCenter';
import { StaffManagement } from './components/StaffManagement';
import { CounterSalesView } from './components/CounterSalesView';
import { GuidedTutorials } from './components/GuidedTutorials';
import { GuidedOnboarding } from './components/GuidedOnboarding';
import { BookingComposer, type BookingDraft } from './components/BookingComposer';
import { AccountingWorkspace } from './components/AccountingWorkspace';
import { TechnicianWorkspace } from './components/TechnicianWorkspace';
import { useActionPrompt } from './components/ActionPrompt';
import { useBranding } from './lib/branding';
import { COOKIE_SESSION, capturePayment, closeCashSession, convertQuoteToWorkOrder, createBooking, createCounterSale, createQuote, createQuoteFromWorkOrder, getApprovalRequests, getBoard, getBookings, getCashSummary, getCounterSales, getCounterSalesContext, getFlowHeatmap, getHaNodes, getManagementSummary, getOperationsOverview, getProducts, getQuotes, getStaffMe, getStoreOrders, getWorkshopView, openCashSession, recordFlowEvent, requestCounterApproval, requestWorkOrderPart, returnCounterSale, staffLogin, staffLogout, syncCounterSale, transitionWorkOrder, updateBookingStatus, updateQuoteStatus, updateStoreOrderStatus, updateWorkOrderPartStatus } from './lib/api';
import type { ApprovalRequest, Booking, BookingStatus, BoardResponse, CashSummary, CounterSale, CounterSalesContext, FlowHeatmapCell, HaNode, ManagementSummary, OperationsOverview, Product, Quote, QuoteLine, StaffUser, StoreOrder, StoreOrderStatus, WorkshopViewSetting, WorkOrderCard, WorkOrderStatus } from './types';
import './styles.css';
import './styles-commerce.css';
import './styles-enterprise.css';
import './styles-procurement-hr.css';

type View = 'KANBAN' | 'BAYS' | 'TECHNICIAN' | 'BOOKINGS' | 'ORDERS' | 'CATALOG' | 'QUOTES' | 'COUNTER' | 'CASHIER' | 'WAREHOUSE' | 'PROCUREMENT' | 'HR' | 'USED' | 'PROCESSES' | 'LEADS' | 'MANAGEMENT' | 'ACCOUNTING' | 'MARKETING' | 'SOCIAL' | 'ADMIN' | 'STAFF' | 'DOCUMENTS' | 'FLOWS' | 'GUIDES' | 'SETTINGS' | 'SYSTEM';
const emptyBoard: BoardResponse = { columns: [] };
const emptyOperations: OperationsOverview = { branches: [], warehouses: [], reservations: [], transfers: [], shipments: [], quality_cases: [], leads: [], management_documents: [] };
const emptyCounterContext: CounterSalesContext = { owner_approval_email: 'admin@smartdiag504.com', branches: [], warehouses: [], products: [] };
const ROLE_VIEWS: Partial<Record<StaffUser['role'], View[]>> = {
  MANAGER: ['KANBAN', 'BAYS', 'TECHNICIAN', 'BOOKINGS', 'ORDERS', 'CATALOG', 'QUOTES', 'COUNTER', 'CASHIER', 'WAREHOUSE', 'PROCUREMENT', 'HR', 'USED', 'PROCESSES', 'FLOWS', 'LEADS', 'MANAGEMENT', 'ACCOUNTING', 'MARKETING', 'SOCIAL', 'DOCUMENTS', 'GUIDES', 'SETTINGS', 'SYSTEM'],
  ACCOUNTANT: ['ACCOUNTING', 'MANAGEMENT', 'PROCUREMENT', 'HR', 'QUOTES', 'CASHIER', 'DOCUMENTS', 'GUIDES'],
  TECHNICIAN: ['TECHNICIAN', 'KANBAN', 'BAYS', 'CATALOG', 'DOCUMENTS', 'GUIDES'],
  CASHIER: ['KANBAN', 'QUOTES', 'COUNTER', 'CASHIER', 'DOCUMENTS', 'GUIDES'],
  WAREHOUSE: ['KANBAN', 'CATALOG', 'WAREHOUSE', 'DOCUMENTS', 'GUIDES'],
  RECEPTION: ['KANBAN', 'BOOKINGS', 'ORDERS', 'QUOTES', 'LEADS', 'GUIDES'],
  MARKETING: ['LEADS', 'MARKETING', 'SOCIAL', 'GUIDES'],
  AUDITOR: ['KANBAN', 'QUOTES', 'CASHIER', 'WAREHOUSE', 'PROCESSES', 'FLOWS', 'MANAGEMENT', 'GUIDES'],
};

function routeView(path: string): View {
  if (path.includes('/bahias')) return 'BAYS';
  if (path.includes('/tecnico')) return 'TECHNICIAN';
  if (path.includes('/contador')) return 'ACCOUNTING';
  if (path.includes('/catalogo')) return 'CATALOG';
  if (path.includes('/citas')) return 'BOOKINGS';
  if (path.includes('/pedidos')) return 'ORDERS';
  if (path.includes('/cotizaciones')) return 'QUOTES';
  if (path.includes('/mostrador')) return 'COUNTER';
  if (path.includes('/caja')) return 'CASHIER';
  if (path.includes('/bodega')) return 'WAREHOUSE';
  if (path.includes('/compras') || path.includes('/importaciones')) return 'PROCUREMENT';
  if (path.includes('/rrhh')) return 'HR';
  if (path.includes('/usados')) return 'USED';
  if (path.includes('/procesos')) return 'PROCESSES';
  if (path.includes('/leads')) return 'LEADS';
  if (path.includes('/gerencia')) return 'MANAGEMENT';
  if (path.includes('/publicida')) return 'MARKETING';
  if (path.includes('/social')) return 'SOCIAL';
  if (path.includes('/3gj')) return 'ADMIN';
  if (path.includes('/personal')) return 'STAFF';
  if (path.includes('/documentos')) return 'DOCUMENTS';
  if (path.includes('/configuracion')) return 'SETTINGS';
  if (path.includes('/flujos')) return 'FLOWS';
  if (path.includes('/guias')) return 'GUIDES';
  if (path.includes('/sistema')) return 'SYSTEM';
  return 'KANBAN';
}

const VIEW_PATHS: Record<View, string> = {
  KANBAN: '/tallerv1/login', BAYS: '/tallerv1/bahias', TECHNICIAN: '/tallerv1/tecnico',
  BOOKINGS: '/tallerv1/citas', ORDERS: '/tallerv1/pedidos', CATALOG: '/tallerv1/catalogo',
  QUOTES: '/tallerv1/cotizaciones', COUNTER: '/tallerv1/mostrador', CASHIER: '/tallerv1/caja',
  WAREHOUSE: '/tallerv1/bodega', PROCUREMENT: '/tallerv1/compras', HR: '/tallerv1/rrhh',
  USED: '/tallerv1/usados', PROCESSES: '/tallerv1/procesos', FLOWS: '/tallerv1/flujos',
  LEADS: '/tallerv1/leads', MANAGEMENT: '/tallerv1/gerencia', ACCOUNTING: '/tallerv1/contador',
  MARKETING: '/tallerv1/publicida', SOCIAL: '/tallerv1/social', ADMIN: '/tallerv1/3gj',
  STAFF: '/tallerv1/personal', DOCUMENTS: '/tallerv1/documentos', GUIDES: '/tallerv1/guias',
  SETTINGS: '/tallerv1/configuracion', SYSTEM: '/tallerv1/sistema',
};

export default function App({ initialToken }: { initialToken?: string }) {
  const [token, setToken] = useState(() => initialToken ?? sessionStorage.getItem('smartdiag-admin-token') ?? '');
  const [staffUser, setStaffUser] = useState<StaffUser | null>(null);
  const [authChecked, setAuthChecked] = useState(Boolean(initialToken ?? sessionStorage.getItem('smartdiag-admin-token')));
  const [view, setView] = useState<View>(() => routeView(window.location.pathname));
  const [board, setBoard] = useState<BoardResponse>(emptyBoard);
  const [setting, setSetting] = useState<WorkshopViewSetting>({ default_view: 'KANBAN', bays_enabled: false });
  const [products, setProducts] = useState<Product[]>([]);
  const [storeOrders, setStoreOrders] = useState<StoreOrder[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [cashSummary, setCashSummary] = useState<CashSummary>({ session: null, payments: [], totals_by_method: {}, total_collected: '0' });
  const [counterSales, setCounterSales] = useState<CounterSale[]>([]);
  const [counterContext, setCounterContext] = useState<CounterSalesContext>(emptyCounterContext);
  const [approvalRequests, setApprovalRequests] = useState<ApprovalRequest[]>([]);
  const [managementSummary, setManagementSummary] = useState<ManagementSummary | null>(null);
  const [nodes, setNodes] = useState<HaNode[]>([]);
  const [flowCells, setFlowCells] = useState<FlowHeatmapCell[]>([]);
  const [operations, setOperations] = useState<OperationsOverview>(emptyOperations);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState<WorkOrderCard | null>(null);
  const [tourOpen, setTourOpen] = useState(false);
  const { ask, dialog: actionPrompt } = useActionPrompt();
  const branding = useBranding();

  function navigateTo(nextView: View) {
    setView(nextView);
    const path = VIEW_PATHS[nextView];
    if (window.location.pathname !== path) window.history.pushState({}, '', path);
  }

  useEffect(() => {
    const onPopState = () => setView(routeView(window.location.pathname));
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const reloadProducts = useCallback(async () => {
    if (!token) return;
    const page = await getProducts(token);
    setProducts(page.items);
  }, [token]);

  const reload = useCallback(async () => {
    if (!token) return;
    setLoading(true); setError('');
    try {
      const role = staffUser?.role;
      const allowed = (roles: StaffUser['role'][]) => !role || roles.includes(role);
      const settingsAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER']);
      const catalogAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER', 'TECHNICIAN', 'WAREHOUSE']);
      const ordersAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER', 'RECEPTION']);
      const bookingsAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER', 'RECEPTION']);
      const quotesAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER', 'CASHIER', 'RECEPTION', 'AUDITOR']);
      const cashierAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER', 'CASHIER', 'AUDITOR']);
      const managementAllowed = allowed(['OWNER', 'ADMIN', 'ACCOUNTANT']);
      const systemAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER']);
      const processesAllowed = allowed(['OWNER', 'ADMIN', 'MANAGER', 'AUDITOR']);
      const [nextBoard, nextSetting, productPage, nextOrders, nextBookings, nextQuotes, nextCashSummary, nextCounterSales, nextCounterContext, nextApprovals, nextManagement, nextNodes, nextFlowCells, nextOperations] = await Promise.all([
        getBoard(token).catch(() => emptyBoard),
        settingsAllowed ? getWorkshopView(token).catch(() => setting) : Promise.resolve(setting),
        catalogAllowed ? getProducts(token).catch(() => ({ items: [], total: 0, limit: 100, offset: 0 })) : Promise.resolve({ items: [], total: 0, limit: 100, offset: 0 }),
        ordersAllowed ? getStoreOrders(token).catch(() => []) : Promise.resolve([]),
        bookingsAllowed ? getBookings(token).catch(() => []) : Promise.resolve([]),
        quotesAllowed ? getQuotes(token).catch(() => []) : Promise.resolve([]),
        cashierAllowed ? getCashSummary(token).catch(() => ({ session: null, payments: [], totals_by_method: {}, total_collected: '0' })) : Promise.resolve({ session: null, payments: [], totals_by_method: {}, total_collected: '0' }),
        cashierAllowed ? getCounterSales(token).catch(() => []) : Promise.resolve([]),
        cashierAllowed ? getCounterSalesContext(token).catch(() => emptyCounterContext) : Promise.resolve(emptyCounterContext),
        cashierAllowed ? getApprovalRequests(token).catch(() => []) : Promise.resolve([]),
        managementAllowed ? getManagementSummary(token).catch(() => null) : Promise.resolve(null),
        systemAllowed ? getHaNodes(token).catch(() => []) : Promise.resolve([]),
        processesAllowed ? getFlowHeatmap(token).catch(() => []) : Promise.resolve([]),
        getOperationsOverview(token).catch(() => emptyOperations),
      ]);
      setBoard(nextBoard); setSetting(nextSetting); setProducts(productPage.items); setStoreOrders(nextOrders); setBookings(nextBookings); setQuotes(nextQuotes); setCashSummary(nextCashSummary); setCounterSales(nextCounterSales); setCounterContext(nextCounterContext); setApprovalRequests(nextApprovals); setManagementSummary(nextManagement); setNodes(nextNodes); setFlowCells(nextFlowCells); setOperations(nextOperations);
      setView((current) => window.location.pathname === '/tallerv1/login' && (current === 'KANBAN' || current === 'BAYS') ? nextSetting.default_view : current);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo cargar la operación.');
    } finally { setLoading(false); }
  }, [token, staffUser?.role]);

  useEffect(() => { void reload(); }, [reload]);

  useEffect(() => {
    if (token) { setAuthChecked(true); return; }
    void getStaffMe().then(activateStaffProfile).catch(() => undefined).finally(() => setAuthChecked(true));
  }, []);

  useEffect(() => {
    if (!staffUser || ['OWNER', 'ADMIN'].includes(staffUser.role)) return;
    const allowed = ROLE_VIEWS[staffUser.role] ?? [];
    if (!allowed.includes(view) && allowed[0]) setView(allowed[0]);
  }, [staffUser, view]);

  function activateStaffProfile(profile: StaffUser) {
    setStaffUser(profile);
    setToken(COOKIE_SESSION);
    const initialView: View = profile.role === 'TECHNICIAN' ? 'TECHNICIAN' : profile.role === 'ACCOUNTANT' ? 'ACCOUNTING' : (ROLE_VIEWS[profile.role]?.[0] ?? 'KANBAN');
    if (window.location.pathname === '/tallerv1/login') navigateTo(initialView);
    const tourKey = `smartdiag-tour-v1:${profile.id}`;
    if (!localStorage.getItem(tourKey)) {
      setTourOpen(true);
      localStorage.setItem(tourKey, 'shown');
    }
  }
  async function loginStaff(email: string, password: string, mfaCode: string) {
    activateStaffProfile(await staffLogin(email, password, mfaCode));
  }
  function loginRecovery(nextToken: string) { sessionStorage.setItem('smartdiag-admin-token', nextToken); setStaffUser(null); setToken(nextToken); }
  async function logout() { if (token === COOKIE_SESSION) await staffLogout(); sessionStorage.removeItem('smartdiag-admin-token'); setStaffUser(null); setToken(''); }

  async function changeStoreOrderStatus(order: StoreOrder, status: StoreOrderStatus, erpnextReference?: string) {
    try {
      const updated = await updateStoreOrderStatus(token, order.id, status, erpnextReference);
      setStoreOrders((current) => current.map((item) => item.id === updated.id ? updated : item));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo actualizar el pedido.');
      throw requestError;
    }
  }

  async function advance(card: WorkOrderCard, target: WorkOrderStatus) {
    const reason = await ask(`Motivo para mover ${card.external_reference} a ${target}`, { label: 'Motivo', initialValue: 'Actualización operativa' });
    if (!reason) return;
    const invoiceReference = target === 'INVOICED' ? await ask('Referencia de factura ERPNext', { label: 'Referencia ERPNext' }) ?? '' : undefined;
    if (target === 'INVOICED' && !invoiceReference) return;
    try { await transitionWorkOrder(token, card.id, target, reason, invoiceReference); await reload(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo actualizar la OT.'); }
  }

  async function changeBookingStatus(booking: Booking, status: BookingStatus) {
    try {
      const updated = await updateBookingStatus(token, booking.id, status);
      setBookings((current) => current.map((item) => item.id === updated.id ? updated : item));
      setFlowCells(await getFlowHeatmap(token));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo actualizar la cita.');
      throw requestError;
    }
  }

  async function addBooking(draft: BookingDraft) {
    try {
      const created = await createBooking(token, draft);
      setBookings((current) => [created, ...current]);
      setFlowCells(await getFlowHeatmap(token));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo crear la cita.');
      throw requestError;
    }
  }

  async function addPartToSelectedWorkOrder(product: Product, quantity: number, note: string) {
    if (!selectedWorkOrder) return;
    try {
      const updated = await requestWorkOrderPart(token, selectedWorkOrder.id, product.id, quantity, note);
      setSelectedWorkOrder(updated);
      setBoard((current) => ({ columns: current.columns.map((column) => ({ ...column, cards: column.cards.map((card) => card.id === updated.id ? updated : card) })) }));
      setFlowCells(await getFlowHeatmap(token));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo solicitar el repuesto.');
      throw requestError;
    }
  }

  async function changePartStatus(workOrder: WorkOrderCard, requestId: string, status: string, location: string, note = '') {
    try {
      const updated = await updateWorkOrderPartStatus(token, workOrder.id, requestId, status, location, note);
      setBoard((current) => ({ columns: current.columns.map((column) => ({ ...column, cards: column.cards.map((card) => card.id === updated.id ? updated : card) })) }));
      setSelectedWorkOrder((current) => current?.id === updated.id ? updated : current);
      setFlowCells(await getFlowHeatmap(token));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo registrar la entrega.');
      throw requestError;
    }
  }

  async function recordFlow(module: string, action: string, itemReference: string, metadata?: Record<string, unknown>) {
    try {
      await recordFlowEvent(token, { module, action, item_reference: itemReference, metadata });
      setFlowCells(await getFlowHeatmap(token));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'No se pudo registrar el flujo.');
      throw requestError;
    }
  }

  async function addQuote(payload: { work_order_id?: string; customer_id?: string; vehicle_id?: string; notes: string; discount: string; tax: string; created_by: string; lines: QuoteLine[] }) {
    try { const created = await createQuote(token, payload); setQuotes((items) => [created, ...items]); setFlowCells(await getFlowHeatmap(token)); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo crear la cotización.'); throw requestError; }
  }

  async function changeQuoteStatus(quote: Quote, status: 'SENT' | 'APPROVED' | 'REJECTED') {
    try { const updated = await updateQuoteStatus(token, quote.id, status); setQuotes((items) => items.map((item) => item.id === updated.id ? updated : item)); setFlowCells(await getFlowHeatmap(token)); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo actualizar la cotización.'); throw requestError; }
  }

  async function assembleQuote(workOrderId: string) {
    try { const created = await createQuoteFromWorkOrder(token, workOrderId); setQuotes((items) => [created, ...items]); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo armar la cotización desde la OT.'); throw requestError; }
  }

  async function convertQuote(quoteId: string) {
    try { const updated = await convertQuoteToWorkOrder(token, quoteId); setQuotes((items) => items.map((item) => item.id === updated.id ? updated : item)); await reload(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo convertir la cotizacion en OT.'); throw requestError; }
  }

  async function openCash(openingBalance: string) { const accessCode = await ask('Autorizar apertura de caja', { label: 'Código privado de cajera', inputType: 'password' }) || ''; if (!accessCode) return; try { await openCashSession(token, openingBalance, accessCode); setCashSummary(await getCashSummary(token)); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo abrir caja.'); throw requestError; } }
  async function pay(payload: { work_order_id: string; quote_id: string; method: string; amount: string; reference: string }) { if (!cashSummary.session) return; const accessCode = await ask('Autorizar cobro', { label: 'Código privado de cajera', inputType: 'password' }) || ''; if (!accessCode) return; try { await capturePayment(token, cashSummary.session.id, { ...payload, access_code: accessCode }); setCashSummary(await getCashSummary(token)); setFlowCells(await getFlowHeatmap(token)); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo registrar el pago.'); throw requestError; } }
  async function closeCash(countedCash: string) { if (!cashSummary.session) return; const accessCode = await ask('Autorizar cierre y arqueo', { label: 'Código privado de cajera', inputType: 'password' }) || ''; if (!accessCode) return; try { await closeCashSession(token, cashSummary.session.id, countedCash, accessCode); setCashSummary(await getCashSummary(token)); setFlowCells(await getFlowHeatmap(token)); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo cerrar el turno.'); throw requestError; } }
  async function sellAtCounter(payload: Parameters<typeof createCounterSale>[1]) { try { const created = await createCounterSale(token, payload); setCounterSales((items) => [created, ...items]); const [nextCash, nextContext] = await Promise.all([getCashSummary(token), getCounterSalesContext(token)]); setCashSummary(nextCash); setCounterContext(nextContext); setFlowCells(await getFlowHeatmap(token)); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo completar la venta de mostrador.'); throw requestError; } }
  async function requestApprovalAtCounter(sale: CounterSale, requestType: 'RETURN' | 'WARRANTY', saleItemId: string, quantity: string, reason: string, method: string, reference: string, ownerEmail: string) { try { const created = await requestCounterApproval(token, sale.id, { request_type: requestType, reason, method, reference: reference || undefined, requested_by: 'cajera-mostrador', owner_email: ownerEmail, items: [{ sale_item_id: saleItemId, quantity }] }); setApprovalRequests((items) => [created, ...items]); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo solicitar autorización.'); throw requestError; } }
  async function returnAtCounter(sale: CounterSale, approvalId: string, saleItemId: string, quantity: string, reason: string, method: string, reference: string, accessCode: string) { try { await returnCounterSale(token, sale.id, { approval_id: approvalId, reason, method, reference: reference || undefined, actor: 'cajera-mostrador', access_code: accessCode, items: [{ sale_item_id: saleItemId, quantity }] }); const [nextSales, nextCash, nextContext, nextApprovals] = await Promise.all([getCounterSales(token), getCashSummary(token), getCounterSalesContext(token), getApprovalRequests(token)]); setCounterSales(nextSales); setCashSummary(nextCash); setCounterContext(nextContext); setApprovalRequests(nextApprovals); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo registrar la devolución.'); throw requestError; } }
  async function syncSaleAtCounter(sale: CounterSale) { try { const updated = await syncCounterSale(token, sale.id); setCounterSales((items) => items.map((item) => item.id === updated.id ? updated : item)); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'No se pudo sincronizar la venta con ERPNext.'); throw requestError; } }

  const counts = useMemo(() => Object.fromEntries(board.columns.map((column) => [column.status, column.cards.length])), [board]);
  if (window.location.pathname.startsWith('/tallerv1/publicida/tv')) return <MarketingDisplay />;
  if (!authChecked) return <main className="login-screen login-loading"><Brand /><p>Validando sesion segura...</p></main>;
  if (!token) return <Login onLogin={loginStaff} onRecoveryLogin={loginRecovery} />;

  const nav = [
    { id: 'KANBAN' as View, label: 'Kanban', icon: Columns3 },
    { id: 'BAYS' as View, label: 'Bahías', icon: LayoutGrid },
    { id: 'TECHNICIAN' as View, label: 'Mi trabajo técnico', icon: HardHat },
    { id: 'BOOKINGS' as View, label: 'Citas', icon: CalendarDays },
    { id: 'ORDERS' as View, label: 'Pedidos web', icon: ShoppingCart },
    { id: 'CATALOG' as View, label: 'Catálogo', icon: PackageSearch },
    { id: 'QUOTES' as View, label: 'Cotizaciones', icon: ShoppingCart },
    { id: 'COUNTER' as View, label: 'Mostrador', icon: Store },
    { id: 'CASHIER' as View, label: 'Caja', icon: ShoppingCart },
    { id: 'WAREHOUSE' as View, label: 'Bodega', icon: Warehouse },
    { id: 'PROCUREMENT' as View, label: 'Compras e importación', icon: PackageOpen },
    { id: 'HR' as View, label: 'RR. HH. y nómina', icon: UsersRound },
    { id: 'USED' as View, label: 'Vehículos usados', icon: CarFront },
    { id: 'PROCESSES' as View, label: 'Procesos y calidad', icon: Route },
    { id: 'LEADS' as View, label: 'Leads CRM', icon: UserRoundSearch },
    { id: 'MANAGEMENT' as View, label: 'Gerencia', icon: Building2 },
    { id: 'ACCOUNTING' as View, label: 'Contador', icon: Landmark },
    { id: 'MARKETING' as View, label: 'Publicidad', icon: Megaphone },
    { id: 'SOCIAL' as View, label: 'Hub Social', icon: Bell },
    { id: 'ADMIN' as View, label: 'Administración', icon: Gauge },
    { id: 'STAFF' as View, label: 'Personal y accesos', icon: UserCog },
    { id: 'DOCUMENTS' as View, label: 'Documentos', icon: FileCog },
    { id: 'GUIDES' as View, label: 'Guía interactiva', icon: BookOpenCheck },
    { id: 'SETTINGS' as View, label: 'Configuración', icon: Settings },
    { id: 'SYSTEM' as View, label: 'Sistema', icon: HeartPulse },
  ].filter((item) => !staffUser || ['OWNER', 'ADMIN'].includes(staffUser.role) || (ROLE_VIEWS[staffUser.role] ?? []).includes(item.id));

  return <div className="ops-shell">
    <a className="skip-link" href="#contenido-principal">Saltar al contenido principal</a>
    <aside className={menuOpen ? 'ops-sidebar ops-sidebar--open' : 'ops-sidebar'}>
      <div className="ops-sidebar__brand"><Brand /><button aria-label="Cerrar menú" onClick={() => setMenuOpen(false)}><X /></button></div>
      <nav aria-label="Módulos de operación" data-tour="navigation">{nav.map(({ id, label, icon: Icon }) => <button key={id} data-tour={id} className={view === id || (id === 'PROCESSES' && view === 'FLOWS') ? 'nav-item nav-item--active' : 'nav-item'} onClick={() => { navigateTo(id); setMenuOpen(false); }}><Icon size={19} /><span>{label}</span>{id === 'KANBAN' && <b>{Object.values(counts).reduce((a, b) => a + Number(b || 0), 0)}</b>}</button>)}</nav>
      <div className="ops-sidebar__footer"><div><span className="online-dot" /><p><strong>API conectada</strong><small>{branding.display_name} v0.4</small></p></div><button onClick={() => void logout()}><LogOut size={18} /> Salir</button></div>
    </aside>

    <div className="ops-main">
      <header className="ops-topbar"><button className="mobile-menu" onClick={() => setMenuOpen(true)} aria-label="Abrir menú"><Menu /></button><div className="ops-search" data-tour="global-search"><Search size={17} /><input placeholder="Buscar OT, VIN, placa o cliente" aria-label="Buscar en operaciones" /></div><div className="ops-topbar__actions"><button data-tour="tour-button" aria-label="Abrir recorrido guiado" onClick={() => setTourOpen(true)}><BookOpenCheck /></button><button aria-label="Actualizar" onClick={() => void reload()} className={loading ? 'rotating' : ''}><RefreshCw /></button><button aria-label="Notificaciones"><Bell /><span /></button><div className="user-chip"><strong>{staffUser?.full_name || 'Administrador'}</strong><small>{staffUser?.role || 'Acceso de recuperacion'}</small></div></div></header>
      {error && <div className="global-error" role="alert" aria-live="assertive">{error}<button onClick={() => setError('')}>Cerrar</button></div>}
      <main className="ops-content" id="contenido-principal" tabIndex={-1}>
        {(view === 'KANBAN' || view === 'BAYS') && <>
          <header className="content-header operation-heading"><div><span>Operación del taller</span><h1>{view === 'KANBAN' ? 'Órdenes de trabajo' : 'Bahías y vehículos'}</h1><p>Una sola OT desde recepción hasta factura, sin duplicar estados.</p></div><div className="view-switch">{view === 'KANBAN' && <BookingComposer busy={loading} onCreate={addBooking} />}<button aria-label="Kanban" className={view === 'KANBAN' ? 'active' : ''} onClick={() => navigateTo('KANBAN')}><Columns3 /> Kanban</button><button aria-label="Bahías" className={view === 'BAYS' ? 'active' : ''} onClick={() => navigateTo('BAYS')}><LayoutGrid /> Bahías</button></div></header>
          <div className="status-summary"><div><span className="summary-icon summary-icon--blue"><Gauge /></span><p><small>En diagnóstico/cotización</small><strong>{(counts.CREATED || 0) + (counts.QUOTED_BY_TECHNICIAN || 0)}</strong></p></div><div><span className="summary-icon summary-icon--gold"><Bell /></span><p><small>Esperando cliente/repuestos</small><strong>{(counts.PENDING_CUSTOMER_APPROVAL || 0) + (counts.PENDING_PARTS || 0)}</strong></p></div><div><span className="summary-icon summary-icon--green"><Warehouse /></span><p><small>Listas para facturar</small><strong>{counts.READY_TO_INVOICE || 0}</strong></p></div><div><span className="summary-icon summary-icon--navy"><Boxes /></span><p><small>Facturadas</small><strong>{counts.INVOICED || 0}</strong></p></div></div>
          {view === 'KANBAN' ? <KanbanBoard board={board} onAdvance={advance} onOpen={setSelectedWorkOrder} /> : <BaysView board={board} enabled={setting.bays_enabled} />}
        </>}
        {view === 'TECHNICIAN' && <TechnicianWorkspace board={board} user={staffUser} onOpen={setSelectedWorkOrder} />}
        {view === 'BOOKINGS' && <BookingsView bookings={bookings} busy={loading} onStatusChange={changeBookingStatus} />}
        {view === 'ORDERS' && <StoreOrdersView token={token} orders={storeOrders} busy={loading} onStatusChange={changeStoreOrderStatus} onReload={reload} />}
        {view === 'CATALOG' && <CatalogManager token={token} products={products} onReload={reloadProducts} />}
        {view === 'QUOTES' && <QuotesView token={token} workOrders={board.columns.flatMap((column) => column.cards)} quotes={quotes} busy={loading} onCreate={addQuote} onAssemble={assembleQuote} onStatus={changeQuoteStatus} onConvert={convertQuote} />}
        {view === 'COUNTER' && <CounterSalesView token={token} summary={cashSummary} context={counterContext} sales={counterSales} quotes={quotes} approvals={approvalRequests} busy={loading} onCreate={sellAtCounter} onQuote={addQuote} onQuoteStatus={changeQuoteStatus} onRequestApproval={requestApprovalAtCounter} onReturn={returnAtCounter} onSync={syncSaleAtCounter} />}
        {view === 'CASHIER' && <CashierModule token={token} workOrders={board.columns.flatMap((column) => column.cards)} quotes={quotes} summary={cashSummary} busy={loading} onOpen={openCash} onPay={pay} onClose={closeCash} />}
        {view === 'WAREHOUSE' && <WarehouseView token={token} workOrders={board.columns.flatMap((column) => column.cards)} onStatus={changePartStatus} />}
        {view === 'PROCUREMENT' && <EnterpriseWorkspace token={token} mode="PROCUREMENT" />}
        {view === 'HR' && <EnterpriseWorkspace token={token} mode="HR" />}
        {view === 'USED' && <EnterpriseWorkspace token={token} mode="USED" />}
        {(view === 'PROCESSES' || view === 'FLOWS') && <>
          <nav className="process-workspace-tabs" aria-label="Secciones de procesos y calidad">
            <button className={view === 'PROCESSES' ? 'active' : ''} aria-current={view === 'PROCESSES' ? 'page' : undefined} onClick={() => navigateTo('PROCESSES')}><Route /> Procesos y calidad</button>
            <button className={view === 'FLOWS' ? 'active' : ''} aria-current={view === 'FLOWS' ? 'page' : undefined} onClick={() => navigateTo('FLOWS')}><Activity /> Mapa de flujos</button>
          </nav>
          {view === 'PROCESSES' ? <ProcessControlView overview={operations} token={token} onReload={reload} /> : <FlowAnalytics cells={flowCells} />}
        </>}
        {view === 'LEADS' && <LeadsKanbanView overview={operations} token={token} onReload={reload} />}
        {view === 'MANAGEMENT' && <ManagementView overview={operations} token={token} onReload={reload} />}
        {view === 'ACCOUNTING' && <AccountingWorkspace token={token} overview={operations} summary={managementSummary} onReload={reload} />}
        {view === 'MARKETING' && <MarketingView token={token} />}
        {view === 'SOCIAL' && <EnterpriseWorkspace token={token} mode="SOCIAL" />}
        {view === 'ADMIN' && <AdminOverview summary={managementSummary} operations={operations} staffUser={staffUser} />}
        {view === 'STAFF' && <StaffManagement token={token} />}
        {view === 'DOCUMENTS' && <DocumentTemplateCenter token={token} />}
        {view === 'GUIDES' && <GuidedTutorials />}
        {view === 'SETTINGS' && <SettingsView token={token} setting={setting} onChange={(next) => { setSetting(next); navigateTo(next.default_view); }} />}
        {view === 'SYSTEM' && <SystemStatus nodes={nodes} />}
      </main>
    </div>
    {selectedWorkOrder && <WorkOrderDetail token={token} workOrder={selectedWorkOrder} products={products} busy={loading} onClose={() => setSelectedWorkOrder(null)} onRequestPart={addPartToSelectedWorkOrder} />}
    {staffUser && <GuidedOnboarding role={staffUser.role} module={view === 'COUNTER' ? 'COUNTER' : undefined} open={tourOpen} onClose={() => setTourOpen(false)} />}
    {actionPrompt}
  </div>;
}
