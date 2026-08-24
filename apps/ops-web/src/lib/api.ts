import type { ApprovalRequest, AttendanceEntry, Booking, BookingStatus, BoardResponse, BrandingProfile, CashSession, CashSummary, CatalogImportPreview, CounterFitment, CounterSale, CounterSalesContext, DocumentRender, DocumentTemplate, DocumentTemplateVersion, EmployeeContract, EnterpriseOverview, FlowEvent, FlowHeatmapCell, HaNode, ImportCase, LeaveRequest, ManagementDocument, ManagementSummary, MarketingCampaign, OperationsOverview, Payment, PayrollRun, Product, ProductPage, PurchaseOrder, Quote, QuoteLine, SalesLead, SocialChannel, SocialConversation, StaffAccessEvent, StaffCompensationProfile, StaffRole, StaffTechnician, StaffUser, StoreOrder, StoreOrderStatus, Supplier, UsedVehicle, WorkshopViewSetting, WorkOrderCard, WorkOrderLaborEntry, WorkOrderStatus } from '../types';
import type { CounterItemRequest } from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
export const COOKIE_SESSION = '__cookie_session__';
// Actor fields remain in the compatibility contract, but the API discards
// this marker and resolves the authoritative employee from the signed session.
const SESSION_ACTOR = 'authenticated-session';

type ApiOptions = RequestInit & { token: string };

async function api<T>(path: string, { token, ...options }: ApiOptions): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  const recoveryToken = token === COOKIE_SESSION ? sessionStorage.getItem('smartdiag-admin-token') : null;
  const effectiveToken = recoveryToken || token;
  if (effectiveToken && effectiveToken !== COOKIE_SESSION) headers.set('X-Admin-Token', effectiveToken);
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { detail?: string | { message?: string } };
    const detail = typeof payload.detail === 'string' ? payload.detail : payload.detail?.message;
    throw new Error(detail ?? `Error HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function staffLogin(email: string, password: string, mfaCode = ''): Promise<StaffUser> {
  const body = new URLSearchParams({ username: email, password });
  if (mfaCode.trim()) body.set('client_secret', mfaCode.trim());
  const response = await fetch(`${API_BASE}/api/v1/staff/auth/login`, {
    method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body,
  });
  if (!response.ok) throw new Error('Correo, contrasena o codigo MFA incorrectos, o cuenta bloqueada.');
  return getStaffMe();
}

export async function staffLogout(): Promise<void> {
  await fetch(`${API_BASE}/api/v1/staff/auth/logout`, { method: 'POST', credentials: 'include' });
}

export async function requestStaffPasswordReset(email: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/staff/auth/forgot-password`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }),
  });
  if (!response.ok && response.status !== 202) throw new Error('No se pudo registrar la solicitud.');
}

export async function resetStaffPassword(token: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/staff/auth/reset-password`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token, password }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(payload.detail ?? 'El enlace expiró o ya no es válido.');
  }
}

export async function getStaffMe(): Promise<StaffUser> {
  const response = await fetch(`${API_BASE}/api/v1/staff/session`, { credentials: 'include' });
  if (!response.ok) throw new Error('No hay una sesion activa.');
  if (response.status === 204) throw new Error('No hay una sesion activa.');
  return response.json() as Promise<StaffUser>;
}

export const enrollStaffMfa = () => api<{ secret: string; provisioning_uri: string }>('/api/v1/staff/me/mfa/enroll', { token: COOKIE_SESSION, method: 'POST' });
export const confirmStaffMfa = (code: string) => api<void>('/api/v1/staff/me/mfa/confirm', { token: COOKIE_SESSION, method: 'POST', body: JSON.stringify({ code }) });
export const disableStaffMfa = (code: string) => api<void>('/api/v1/staff/me/mfa', { token: COOKIE_SESSION, method: 'DELETE', body: JSON.stringify({ code }) });
export const revokeStaffSessions = () => api<void>('/api/v1/staff/me/sessions/revoke', { token: COOKIE_SESSION, method: 'POST' });

export const getStaffUsers = (token: string) => api<StaffUser[]>('/api/v1/staff/users', { token });
export const getStaffAccessEvents = (token: string) => api<StaffAccessEvent[]>('/api/v1/staff/access-events', { token });
export const createStaffUser = (token: string, data: { email: string; password: string; employee_code?: string; full_name: string; job_title?: string; role: StaffRole; phone?: string }) => api<StaffUser>('/api/v1/staff/users', { token, method: 'POST', body: JSON.stringify({ ...data, permissions_json: [], is_active: true, is_verified: true, is_superuser: data.role === 'OWNER' }) });
export const updateStaffUser = (token: string, id: string, data: Partial<Pick<StaffUser, 'role' | 'is_active' | 'full_name' | 'job_title' | 'phone' | 'permissions_json'>>) => api<StaffUser>(`/api/v1/staff/users/${id}`, { token, method: 'PATCH', body: JSON.stringify(data) });
export const getStaffTechnicians = (token: string) => api<StaffTechnician[]>('/api/v1/staff/technicians', { token });
export const getStaffCompensationProfiles = (token: string) => api<StaffCompensationProfile[]>('/api/v1/staff/compensation-profiles', { token });
export const updateStaffCompensation = (token: string, id: string, data: Omit<StaffCompensationProfile, 'id' | 'staff_user_id' | 'organization_id' | 'fixed_hourly_allocation' | 'standard_hourly_cost' | 'specialized_hourly_cost' | 'created_at' | 'updated_at'>) => api<StaffCompensationProfile>(`/api/v1/staff/users/${id}/compensation`, { token, method: 'PUT', body: JSON.stringify(data) });

type ApiWorkOrder = WorkOrderCard & {
  number?: string;
  assigned_technicians?: string[];
};
type ApiBoardColumn = { status: WorkOrderStatus; label: string; work_orders: ApiWorkOrder[] };

function mapWorkOrder(item: ApiWorkOrder): WorkOrderCard {
  return {
    ...item,
    external_reference: item.external_reference || item.number || item.id,
    technician_name: item.technician_name ?? item.assigned_technicians?.[0] ?? null,
    customer_name: item.customer_name || item.customer_id,
    vehicle_label: item.vehicle_label || item.vehicle_id,
    quote_total: item.quote_total ?? null,
    version: item.version ?? 1,
  };
}

export async function getBoard(token: string): Promise<BoardResponse> {
  const columns = await api<ApiBoardColumn[]>('/api/v1/operations/work-orders/board', { token });
  return {
    columns: columns.map((column) => ({
      status: column.status,
      label: column.label,
      cards: column.work_orders.map(mapWorkOrder),
    })),
  };
}

export const getWorkshopView = (token: string) => api<WorkshopViewSetting>('/api/v1/operations/settings/workshop', { token });
export const saveWorkshopView = (token: string, setting: WorkshopViewSetting) => api<WorkshopViewSetting>('/api/v1/operations/settings/workshop', {
  token,
  method: 'PUT',
  body: JSON.stringify({ ...setting, bay_codes: setting.bay_codes ?? ['B-01', 'B-02', 'B-03', 'B-04', 'B-05', 'B-06', 'B-07', 'B-08'] }),
});

export const getBranding = () => fetch(`${API_BASE}/api/v1/branding`, { credentials: 'include' }).then(async (response) => {
  if (!response.ok) throw new Error('No se pudo cargar la marca de la empresa.');
  return response.json() as Promise<BrandingProfile>;
});
export const getAdminBranding = (token: string) => api<BrandingProfile>('/api/v1/operations/settings/branding', { token });
export const updateBranding = (token: string, profile: Omit<BrandingProfile, 'organization_id' | 'logo_url' | 'logo_dark_url' | 'favicon_url' | 'asset_history' | 'updated_at'>) =>
  api<BrandingProfile>('/api/v1/operations/settings/branding', { token, method: 'PUT', body: JSON.stringify(profile) });
export async function uploadBrandAsset(token: string, assetType: 'LOGO' | 'LOGO_DARK' | 'FAVICON', file: File): Promise<BrandingProfile> {
  const form = new FormData(); form.set('asset_type', assetType); form.set('file', file);
  return api<BrandingProfile>('/api/v1/operations/settings/branding/assets', { token, method: 'POST', body: form });
}

export async function downloadCatalogTemplate(token: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/operations/catalog-import/template?demo=true`, {
    credentials: 'include', headers: token && token !== COOKIE_SESSION ? { 'X-Admin-Token': token } : {},
  });
  if (!response.ok) throw new Error('No se pudo descargar la plantilla.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = 'smartdiag504_catalogo_ejemplo.xlsx';
  link.click();
  URL.revokeObjectURL(url);
}

function catalogFileRequest(token: string, path: 'preview' | 'apply', file: File) {
  const body = new FormData();
  body.set('file', file);
  return api<CatalogImportPreview>(`/api/v1/operations/catalog-import/${path}`, { token, method: 'POST', body });
}

export const previewCatalogImport = (token: string, file: File) => catalogFileRequest(token, 'preview', file);
export const applyCatalogImport = (token: string, file: File) => catalogFileRequest(token, 'apply', file);

export type ProductionReadiness = {
  environment: string; organization_id: string; production_ready: boolean;
  summary: { ready: number; total: number };
  gates: Array<{ code: string; label: string; ready: boolean; owner: string }>;
};
export const getProductionReadiness = (token: string) =>
  api<ProductionReadiness>('/api/v1/operations/settings/production-readiness', { token });

export type DocumentTemplateDraft = {
  code: string; name: string; document_type: string; branch_id?: string | null;
  paper_size: string; print_profile: import('../types').PrintProfile; html_template: string; css_text: string; change_note: string; created_by: string;
};

export const getDocumentTemplates = (token: string) =>
  api<DocumentTemplate[]>('/api/v1/operations/documents/templates', { token });
export const createDocumentTemplate = (token: string, draft: DocumentTemplateDraft) =>
  api<DocumentTemplate>('/api/v1/operations/documents/templates', { token, method: 'POST', body: JSON.stringify(draft) });
export const createDocumentTemplateVersion = (token: string, templateId: string, draft: Omit<DocumentTemplateDraft, 'code' | 'name' | 'document_type' | 'branch_id'>) =>
  api<DocumentTemplateVersion>(`/api/v1/operations/documents/templates/${templateId}/versions`, { token, method: 'POST', body: JSON.stringify(draft) });
export const publishDocumentTemplate = (token: string, templateId: string, version: number) =>
  api<DocumentTemplate>(`/api/v1/operations/documents/templates/${templateId}/publish`, { token, method: 'POST', body: JSON.stringify({ version, actor: 'administrador' }) });
export function importDocumentTemplateFiles(token: string, draft: Pick<DocumentTemplateDraft, 'code' | 'name' | 'document_type' | 'branch_id' | 'paper_size' | 'print_profile' | 'change_note'>, htmlFile: File, cssFile?: File, templateId?: string) {
  const body = new FormData();
  Object.entries(draft).forEach(([key, value]) => { if (value != null) body.set(key === 'print_profile' ? 'print_profile_json' : key, typeof value === 'object' ? JSON.stringify(value) : String(value)); });
  if (templateId) body.set('template_id', templateId);
  body.set('html_file', htmlFile);
  if (cssFile) body.set('css_file', cssFile);
  return api<DocumentTemplate>('/api/v1/operations/documents/templates/import', { token, method: 'POST', body });
}
export async function exportDocumentTemplate(token: string, templateId: string, code: string): Promise<void> {
  const recoveryToken = token === COOKIE_SESSION ? sessionStorage.getItem('smartdiag-admin-token') : null;
  const effectiveToken = recoveryToken || token;
  const response = await fetch(`${API_BASE}/api/v1/operations/documents/templates/${templateId}/export`, {
    credentials: 'include', headers: effectiveToken && effectiveToken !== COOKIE_SESSION ? { 'X-Admin-Token': effectiveToken } : {},
  });
  if (!response.ok) throw new Error('No se pudo exportar el formato.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a'); link.href = url; link.download = `${code}.smartdiag.json`; link.click(); URL.revokeObjectURL(url);
}
export const getDocumentRenders = (token: string) =>
  api<DocumentRender[]>('/api/v1/operations/documents/renders', { token });
export async function previewDocumentTemplate(token: string, draft: Pick<DocumentTemplateDraft, 'html_template' | 'css_text' | 'paper_size' | 'print_profile'>): Promise<string> {
  const response = await fetch(`${API_BASE}/api/v1/operations/documents/preview`, {
    method: 'POST', credentials: 'include', headers: { ...(token && token !== COOKIE_SESSION ? { 'X-Admin-Token': token } : {}), 'Content-Type': 'application/json' }, body: JSON.stringify(draft),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(payload.detail ?? `Error HTTP ${response.status}`);
  }
  return response.text();
}

type ApiProductImage = {
  id: string; public_url: string; alt_text: string; source_type: string; source_page_url: string | null;
  attribution_text: string | null; sort_order: number; is_primary: boolean; mime_type: string;
};
type ApiProduct = {
  id: string; sku: string; name: string; short_description: string | null; description: string | null;
  brand: string | null; category_id: string | null; price: string | number; currency: string;
  stock_qty: string | number; stock_status: string; compatibility_notes: string | null; source_system: string;
  source_reference: string | null; active: boolean; images: ApiProductImage[];
  purchase_cost: string | number; landed_cost_factor: string | number;
  target_markup_percent: string | number; minimum_markup_percent: string | number;
  abc_class: 'A' | 'B' | 'C'; xyz_class: 'X' | 'Y' | 'Z';
};

function mapProduct(item: ApiProduct): Product {
  return {
    id: item.id,
    sku: item.sku,
    name: item.name,
    description: item.short_description ?? item.description,
    brand: item.brand,
    category_id: item.category_id,
    display_price: String(item.price),
    purchase_cost: String(item.purchase_cost),
    landed_cost_factor: String(item.landed_cost_factor),
    target_markup_percent: String(item.target_markup_percent),
    minimum_markup_percent: String(item.minimum_markup_percent),
    abc_class: item.abc_class,
    xyz_class: item.xyz_class,
    currency: item.currency,
    stock_status: item.stock_status,
    stock_qty: String(item.stock_qty),
    compatibility_note: item.compatibility_notes,
    erpnext_item_code: item.source_system === 'ERPNEXT' ? item.source_reference : null,
    published: item.active,
    active: item.active,
    images: item.images.map((image) => ({
      id: image.id,
      source: image.source_type,
      url: image.public_url,
      alt_text: image.alt_text,
      attribution: image.attribution_text,
      source_page_url: image.source_page_url,
      sort_order: image.sort_order,
      is_primary: image.is_primary,
      mime_type: image.mime_type,
    })),
  };
}

export async function getProducts(token: string): Promise<ProductPage> {
  const items = await api<ApiProduct[]>('/api/v1/admin/catalog/products', { token });
  return { items: items.map(mapProduct), total: items.length, limit: items.length, offset: 0 };
}

export async function getHaNodes(token: string): Promise<HaNode[]> {
  const items = await api<Array<{ node_id: string; role: string; status: string; metadata_json: Record<string, unknown>; last_seen_at: string }>>('/api/v1/cluster/heartbeats', { token });
  const now = Date.now();
  return items.map((item) => {
    const stale = now - Date.parse(item.last_seen_at) > 90_000;
    return {
      node_id: item.node_id,
      role: item.role,
      healthy: item.status === 'HEALTHY',
      stale,
      details: item.metadata_json,
      last_seen_at: item.last_seen_at,
    };
  });
}

export const transitionWorkOrder = (
  token: string,
  workOrderId: string,
  target: WorkOrderStatus,
  reason: string,
  invoiceReference?: string,
) => api(`/api/v1/operations/work-orders/${workOrderId}/transitions`, {
  token,
  method: 'POST',
  body: JSON.stringify({
    to_status: target,
    actor: 'admin@smartdiag504.local',
    reason,
    invoice_reference: invoiceReference || null,
    idempotency_key: crypto.randomUUID(),
  }),
});

export type NewProduct = {
  sku: string; name: string; description?: string; brand?: string; display_price: string;
  currency: string; stock_status: string; compatibility_note?: string; published: boolean;
  purchase_cost?: string; landed_cost_factor?: string; target_markup_percent?: string; minimum_markup_percent?: string; abc_class?: string; xyz_class?: string;
};

export async function createProduct(token: string, product: NewProduct): Promise<Product> {
  const created = await api<ApiProduct>('/api/v1/admin/catalog/products', {
    token,
    method: 'POST',
    body: JSON.stringify({
      sku: product.sku,
      name: product.name,
      short_description: product.description || null,
      description: product.description || null,
      brand: product.brand || null,
      price: product.display_price,
      purchase_cost: product.purchase_cost || '0',
      landed_cost_factor: product.landed_cost_factor || '1',
      target_markup_percent: product.target_markup_percent || '30',
      minimum_markup_percent: product.minimum_markup_percent || '0',
      abc_class: product.abc_class || 'C', xyz_class: product.xyz_class || 'Z',
      currency: product.currency,
      stock_qty: 0,
      stock_status: product.stock_status,
      active: product.published,
      featured: false,
      compatibility_notes: product.compatibility_note || 'Validar por VIN antes de instalar.',
      source_system: 'LOCAL',
    }),
  });
  return mapProduct(created);
}

export async function updateProduct(token: string, productId: string, changes: Partial<Product>): Promise<Product> {
  const updated = await api<ApiProduct>(`/api/v1/admin/catalog/products/${productId}`, {
    token,
    method: 'PATCH',
    body: JSON.stringify({
      name: changes.name,
      short_description: changes.description,
      description: changes.description,
      brand: changes.brand,
      price: changes.display_price,
      purchase_cost: changes.purchase_cost,
      landed_cost_factor: changes.landed_cost_factor,
      target_markup_percent: changes.target_markup_percent,
      minimum_markup_percent: changes.minimum_markup_percent,
      abc_class: changes.abc_class,
      xyz_class: changes.xyz_class,
      currency: changes.currency,
      stock_status: changes.stock_status,
      active: changes.published,
      compatibility_notes: changes.compatibility_note,
    }),
  });
  return mapProduct(updated);
}

export const uploadProductImage = (token: string, productId: string, file: File, altText: string, attribution: string) => {
  const data = new FormData();
  data.set('image', file);
  data.set('alt_text', altText);
  data.set('attribution_text', attribution || altText);
  data.set('make_primary', 'true');
  return api(`/api/v1/admin/catalog/products/${productId}/images/upload`, { token, method: 'POST', body: data });
};

export const addExternalImage = (
  token: string,
  productId: string,
  payload: { url: string; alt_text: string; attribution?: string; source_page_url?: string; source?: string },
) => api(`/api/v1/admin/catalog/products/${productId}/images/import`, {
  token,
  method: 'POST',
  body: JSON.stringify({
    image_url: payload.url,
    alt_text: payload.alt_text,
    source_page_url: payload.source_page_url || null,
    attribution_text: payload.attribution || payload.alt_text,
    make_primary: true,
  }),
});

export async function searchGoogleImages(token: string, query: string) {
  const items = await api<Array<{ image_url: string; thumbnail_url?: string; source_page_url: string; title: string; display_link?: string }>>(`/api/v1/admin/catalog/images/google?q=${encodeURIComponent(query)}`, { token });
  return { configured: true, items };
}


export const getStoreOrders = (token: string) =>
  api<StoreOrder[]>('/api/v1/admin/store/orders', { token });

export const getBookings = (token: string) =>
  api<Booking[]>('/api/v1/operations/bookings', { token });

export const createBooking = (token: string, data: { full_name: string; phone: string; email?: string; vehicle_summary: string; service_requested: string; preferred_date?: string; concern: string }) =>
  api<Booking>('/api/v1/operations/bookings', { token, method: 'POST', body: JSON.stringify(data) });

export const updateBookingStatus = (token: string, bookingId: string, status: BookingStatus) =>
  api<Booking>(`/api/v1/operations/bookings/${bookingId}`, {
    token,
    method: 'PATCH',
    body: JSON.stringify({ status, actor: SESSION_ACTOR }),
  });

export const requestWorkOrderPart = (
  token: string,
  workOrderId: string,
  productId: string,
  quantity: number,
  note: string,
) => api<ApiWorkOrder>(`/api/v1/operations/work-orders/${workOrderId}/part-requests`, {
  token,
  method: 'POST',
  body: JSON.stringify({ product_id: productId, quantity, note, actor: SESSION_ACTOR }),
}).then(mapWorkOrder);

export const deliverWorkOrderPart = (
  token: string,
  workOrderId: string,
  requestId: string,
  location: string,
) => api<ApiWorkOrder>(`/api/v1/operations/work-orders/${workOrderId}/part-requests/${requestId}/delivery`, {
  token,
  method: 'PATCH',
  body: JSON.stringify({ actor: SESSION_ACTOR, location }),
}).then(mapWorkOrder);

export const updateWorkOrderPartStatus = (token: string, workOrderId: string, requestId: string, status: string, location: string, note = '') =>
  api<ApiWorkOrder>(`/api/v1/operations/work-orders/${workOrderId}/part-requests/${requestId}/status`, {
    token, method: 'PATCH', body: JSON.stringify({ status, location, note, actor: SESSION_ACTOR }),
  }).then(mapWorkOrder);

export type WorkOrderEvidence = { id: string; category: string; caption: string; actor: string; media_url: string; mime_type: string; created_at: string };

export const getWorkOrderEvidence = (token: string, workOrderId: string) =>
  api<WorkOrderEvidence[]>(`/api/v1/operations/work-orders/${workOrderId}/evidence`, { token });

export const getWorkOrderLabor = (token: string, workOrderId: string) =>
  api<WorkOrderLaborEntry[]>(`/api/v1/operations/work-orders/${workOrderId}/labor-entries`, { token });

export const getLaborCatalog = (token: string) =>
  api<import('../types').LaborCatalogItem[]>('/api/v1/operations/labor-catalog', { token });

export const recordWorkOrderLabor = (token: string, workOrderId: string, data: { technician_id: string; service_code: string; rate_kind: 'STANDARD' | 'SPECIALIZED'; actor: string }) =>
  api<WorkOrderLaborEntry>(`/api/v1/operations/work-orders/${workOrderId}/labor-entries`, { token, method: 'POST', body: JSON.stringify(data) });

export const registerWorkOrderCheckIn = (token: string, workOrderId: string, data: { mileage_km: number; fuel_percent: number; accessories: string[]; exterior_notes: string; customer_name: string; customer_accepted: boolean }) =>
  api<ApiWorkOrder>(`/api/v1/operations/work-orders/${workOrderId}/check-in`, { token, method: 'POST', body: JSON.stringify({ ...data, actor: SESSION_ACTOR }) }).then(mapWorkOrder);

export const updateWorkOrderTimer = (token: string, workOrderId: string, action: 'START' | 'PAUSE' | 'RESUME' | 'STOP', note = '') =>
  api<ApiWorkOrder>(`/api/v1/operations/work-orders/${workOrderId}/timer`, { token, method: 'POST', body: JSON.stringify({ action, note, actor: SESSION_ACTOR }) }).then(mapWorkOrder);

export const registerWorkOrderQuality = (token: string, workOrderId: string, data: { checklist: Record<string, boolean>; road_test_required: boolean; road_test_result: 'NOT_REQUIRED' | 'PASS' | 'FAIL'; notes: string; result: 'PASS' | 'FAIL' }) =>
  api<ApiWorkOrder>(`/api/v1/operations/work-orders/${workOrderId}/quality`, { token, method: 'POST', body: JSON.stringify({ ...data, actor: SESSION_ACTOR }) }).then(mapWorkOrder);

export async function uploadWorkOrderEvidence(token: string, workOrderId: string, file: File, caption: string, category = 'DIAGNOSIS') {
  const body = new FormData();
  body.set('file', file); body.set('caption', caption); body.set('category', category); body.set('actor', SESSION_ACTOR);
  const response = await fetch(`/api/v1/operations/work-orders/${workOrderId}/evidence`, { method: 'POST', credentials: 'include', headers: token && token !== COOKIE_SESSION ? { 'X-Admin-Token': token } : {}, body });
  if (!response.ok) throw new Error('No se pudo guardar la evidencia fotografica.');
  return response.json() as Promise<WorkOrderEvidence>;
}

export const updateStoreOrderStatus = (
  token: string,
  orderId: string,
  status: StoreOrderStatus,
  erpnextSalesOrderId?: string,
) => api<StoreOrder>(`/api/v1/admin/store/orders/${orderId}`, {
  token,
  method: 'PATCH',
  body: JSON.stringify({
    status,
    erpnext_sales_order_id: erpnextSalesOrderId?.trim() || null,
  }),
});

export async function uploadStorePaymentProof(token: string, orderId: string, file: File, reference: string, amount: string) {
  const body = new FormData();
  body.set('file', file); body.set('reference', reference); body.set('amount', amount);
  const headers: Record<string, string> = {};
  if (token && token !== COOKIE_SESSION) headers['X-Admin-Token'] = token;
  const response = await fetch(`/api/v1/admin/store/orders/${orderId}/payment-proofs`, { method: 'POST', credentials: 'include', headers, body });
  if (!response.ok) throw new Error('No se pudo guardar el comprobante de pago.');
  return response.json() as Promise<{ proof_id: string; reference: string; amount: string }>;
}

export const recordFlowEvent = (
  token: string,
  payload: { module: string; action: string; item_reference: string; metadata?: Record<string, unknown> },
) => api<FlowEvent>('/api/v1/operations/flow-events', {
  token,
  method: 'POST',
  body: JSON.stringify({ ...payload, actor: SESSION_ACTOR, result: 'SUCCESS' }),
});

export const getFlowHeatmap = (token: string) =>
  api<FlowHeatmapCell[]>('/api/v1/operations/flow-events/heatmap', { token });

export const getQuotes = (token: string) =>
  api<Quote[]>('/api/v1/operations/finance/quotes', { token });

export const createQuote = (token: string, payload: {
  work_order_id?: string; customer_id?: string; vehicle_id?: string; notes: string; discount: string; tax: string; created_by: string; lines: QuoteLine[];
}) => api<Quote>('/api/v1/operations/finance/quotes', {
  token, method: 'POST', body: JSON.stringify(payload),
});

export type QuoteContext = { vehicle_id: string; customer_id: string; vin: string | null; plate: string | null; vehicle: string; owner: string };
export const searchQuoteContext = (token: string, query: string) => api<QuoteContext[]>(`/api/v1/operations/finance/quote-context?query=${encodeURIComponent(query)}`, { token });
export const convertQuoteToWorkOrder = (token: string, quoteId: string) => api<Quote>(`/api/v1/operations/finance/quotes/${quoteId}/convert-to-work-order`, { token, method: 'POST', body: JSON.stringify({ actor: SESSION_ACTOR }) });

export const updateQuoteStatus = (token: string, quoteId: string, status: 'SENT' | 'APPROVED' | 'REJECTED') =>
  api<Quote>(`/api/v1/operations/finance/quotes/${quoteId}/status`, {
    token, method: 'PATCH', body: JSON.stringify({ status, actor: SESSION_ACTOR }),
  });

export const getCashSummary = (token: string) =>
  api<CashSummary>('/api/v1/operations/finance/cash-summary', { token });

export const getCounterSalesContext = (token: string, warehouseId?: string) =>
  api<CounterSalesContext>(`/api/v1/operations/finance/counter-sales/context${warehouseId ? `?warehouse_id=${encodeURIComponent(warehouseId)}` : ''}`, { token });

export const getCounterItemRequests = (token: string) =>
  api<CounterItemRequest[]>('/api/v1/operations/finance/counter-item-requests', { token });

export const createCounterItemRequest = (token: string, payload: {
  search_query: string; customer_name: string; phone?: string; vehicle_vin?: string;
  quantity: string; branch_id: string; warehouse_id?: string; product_id?: string; notes?: string;
}) => api<CounterItemRequest>('/api/v1/operations/finance/counter-item-requests', {
  token, method: 'POST', body: JSON.stringify(payload),
});

export const getCounterFitment = (token: string, vin: string) =>
  api<CounterFitment>(`/api/v1/operations/finance/counter-sales/fitment?vin=${encodeURIComponent(vin)}`, { token });

export const getCounterSales = (token: string) =>
  api<CounterSale[]>('/api/v1/operations/finance/counter-sales', { token });

export const createCounterSale = (token: string, payload: {
  cash_session_id: string; branch_id: string; warehouse_id: string; customer_name: string;
  phone?: string; tax_id?: string; vehicle_vin?: string; discount: string; tax: string;
  method: string; reference?: string; actor: string; access_code: string;
  items: { product_id: string; quantity: string; unit_price: string }[];
}) => api<CounterSale>('/api/v1/operations/finance/counter-sales', {
  token, method: 'POST', body: JSON.stringify(payload),
});

export const syncCounterSale = (token: string, saleId: string) =>
  api<CounterSale>(`/api/v1/operations/finance/counter-sales/${saleId}/sync`, {
    token, method: 'POST',
  });

export const returnCounterSale = (token: string, saleId: string, payload: {
  approval_id: string; reason: string; method: string; reference?: string; actor: string; access_code: string;
  items: { sale_item_id: string; quantity: string }[];
}) => api(`/api/v1/operations/finance/counter-sales/${saleId}/returns`, {
  token, method: 'POST', body: JSON.stringify(payload),
});

export const getApprovalRequests = (token: string) => api<ApprovalRequest[]>('/api/v1/operations/finance/approval-requests', { token });
export const requestCounterApproval = (token: string, saleId: string, payload: { request_type: 'RETURN' | 'WARRANTY'; reason: string; method: string; reference?: string; requested_by: string; owner_email: string; items: { sale_item_id: string; quantity: string }[] }) => api<ApprovalRequest>(`/api/v1/operations/finance/counter-sales/${saleId}/approval-requests`, { token, method: 'POST', body: JSON.stringify(payload) });
export const getManagementSummary = (token: string) => api<ManagementSummary>('/api/v1/operations/finance/reporting/summary', { token });

export const openCashSession = (token: string, openingBalance: string, accessCode: string) =>
  api<CashSession>('/api/v1/operations/finance/cash-sessions', {
    token, method: 'POST', body: JSON.stringify({ opening_balance: openingBalance, actor: SESSION_ACTOR, access_code: accessCode }),
  });

export const capturePayment = (token: string, sessionId: string, payload: {
  work_order_id: string; quote_id: string; method: string; amount: string; reference: string; access_code: string;
}) => api<Payment>(`/api/v1/operations/finance/cash-sessions/${sessionId}/payments`, {
  token, method: 'POST', body: JSON.stringify({ ...payload, actor: SESSION_ACTOR, reference: payload.reference || null }),
});

export const closeCashSession = (token: string, sessionId: string, countedCash: string, accessCode: string) =>
  api<CashSession>(`/api/v1/operations/finance/cash-sessions/${sessionId}/close`, {
    token, method: 'POST', body: JSON.stringify({ counted_cash: countedCash, actor: SESSION_ACTOR, access_code: accessCode }),
  });

export const getOperationsOverview = (token: string) =>
  api<OperationsOverview>('/api/v1/operations/control/overview', { token });

export const updateLead = (
  token: string,
  leadId: string,
  status: SalesLead['status'],
  assignedTo?: string,
) => api<SalesLead>(`/api/v1/operations/control/leads/${leadId}`, {
  token,
  method: 'PATCH',
  body: JSON.stringify({ status, assigned_to: assignedTo || null, actor: SESSION_ACTOR }),
});

export const createStaffLead = (token: string, payload: { full_name: string; phone: string; email?: string; interest: string; vehicle_summary?: string; source: string }) =>
  api<SalesLead>('/api/v1/operations/control/leads', { token, method: 'POST', body: JSON.stringify(payload) });
export const addLeadActivity = (token: string, leadId: string, payload: { activity_type: string; content: string; outcome?: string }) =>
  api(`/api/v1/operations/control/leads/${leadId}/activities`, { token, method: 'POST', body: JSON.stringify({ ...payload, actor: SESSION_ACTOR }) });
export const addLeadSurvey = (token: string, leadId: string, surveyName: string, answers: Record<string, unknown>) =>
  api(`/api/v1/operations/control/leads/${leadId}/surveys`, { token, method: 'POST', body: JSON.stringify({ survey_name: surveyName, answers, actor: SESSION_ACTOR }) });

export const createQualityCase = (token: string, payload: {
  case_type: 'RETURN' | 'WARRANTY' | 'COMPLAINT' | 'REWORK'; description: string;
  work_order_id?: string; store_order_id?: string; vehicle_id?: string;
}) => api('/api/v1/operations/control/quality-cases', {
  token,
  method: 'POST',
  body: JSON.stringify({ ...payload, actor: SESSION_ACTOR }),
});

export const updateQualityCase = (token: string, caseId: string, status: string, resolution?: string) =>
  api(`/api/v1/operations/control/quality-cases/${caseId}`, { token, method: 'PATCH', body: JSON.stringify({ status, resolution: resolution || null, actor: SESSION_ACTOR }) });

export const createBranch = (token: string, payload: { code: string; name: string; address?: string }) =>
  api('/api/v1/operations/control/branches', {
    token, method: 'POST', body: JSON.stringify(payload),
  });

export const createManagementDocument = (token: string, payload: {
  branch_id: string; document_type: string; number: string; status: string;
  valid_from?: string | null; valid_until?: string | null; file_url?: string | null;
  metadata_json?: Record<string, unknown>;
}) => api('/api/v1/operations/control/management-documents', {
  token, method: 'POST', body: JSON.stringify(payload),
});

export const updateManagementDocumentStatus = (
  token: string,
  documentId: string,
  payload: { status: 'DRAFT' | 'ACTIVE' | 'EXPIRED'; accountant_confirmed?: boolean; note?: string },
) => api<ManagementDocument>(`/api/v1/operations/control/management-documents/${documentId}/status`, {
  token, method: 'PATCH', body: JSON.stringify(payload),
});

export const createQuoteFromWorkOrder = (token: string, workOrderId: string) =>
  api<Quote>(`/api/v1/operations/finance/quotes/from-work-order/${workOrderId}`, {
    token, method: 'POST', body: JSON.stringify({ actor: SESSION_ACTOR }),
  });

export const updateQuoteLineStatus = (
  token: string,
  quoteId: string,
  lineId: string,
  approvalStatus: 'PENDING' | 'APPROVED' | 'REJECTED',
) => api<Quote>(`/api/v1/operations/finance/quotes/${quoteId}/lines/${lineId}`, {
  token,
  method: 'PATCH',
  body: JSON.stringify({ approval_status: approvalStatus, actor: SESSION_ACTOR }),
});

export async function getAdminDocument(token: string, path: string): Promise<Blob> {
  const response = await fetch(path, { credentials: 'include', headers: token && token !== COOKIE_SESSION ? { 'X-Admin-Token': token } : {} });
  if (!response.ok) throw new Error('No se pudo generar el documento.');
  return response.blob();
}

export const getCampaigns = (token: string) => api<MarketingCampaign[]>('/api/v1/operations/marketing/campaigns', { token });
export const createCampaign = (token: string, payload: { title: string; description: string; audience: string; valid_from?: string; valid_until?: string; price_from?: number; call_to_action?: string; tv_enabled?: boolean; display_seconds?: number; promo_code?: string; discount_percent?: number; store_banner?: boolean }) => api<MarketingCampaign>('/api/v1/operations/marketing/campaigns', { token, method: 'POST', body: JSON.stringify(payload) });
export const getMaintenancePackages = (token: string) => api<import('../types').MaintenancePackage[]>('/api/v1/operations/marketing/maintenance-packages', { token });
export const createMaintenancePackage = (token: string, payload: { name: string; description: string; points: number; service: string }) => api<import('../types').MaintenancePackage>('/api/v1/operations/marketing/maintenance-packages', { token, method: 'POST', body: JSON.stringify(payload) });
export const publishCampaign = (token: string, id: string) => api<MarketingCampaign>(`/api/v1/operations/marketing/campaigns/${id}/publish`, { token, method: 'POST' });
export const getPublicCampaigns = () => api<MarketingCampaign[]>('/api/v1/marketing/campaigns', { token: '' });
export async function uploadCampaignMedia(token: string, id: string, file: File): Promise<MarketingCampaign> {
  const body = new FormData(); body.append('file', file);
  const response = await fetch(`/api/v1/operations/marketing/campaigns/${id}/media`, { method: 'POST', credentials: 'include', headers: token && token !== COOKIE_SESSION ? { 'X-Admin-Token': token } : {}, body });
  if (!response.ok) throw new Error('No se pudo cargar el archivo de campaña.');
  return response.json() as Promise<MarketingCampaign>;
}

const enterprise = '/api/v1/operations/enterprise';
export const getEnterpriseOverview = (token: string) => api<EnterpriseOverview>(`${enterprise}/overview`, { token });
export const createSupplier = (token: string, payload: { code: string; name: string; tax_id?: string; email?: string; phone?: string; payment_terms_days: number; currency: string }) => api<Supplier>(`${enterprise}/suppliers`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updateSupplier = (token: string, id: string, payload: Partial<Pick<Supplier, 'name' | 'tax_id' | 'email' | 'phone' | 'payment_terms_days' | 'currency' | 'active'>>) => api<Supplier>(`${enterprise}/suppliers/${id}`, { token, method: 'PATCH', body: JSON.stringify(payload) });
export const createPurchaseOrder = (token: string, payload: { supplier_id: string; currency: string; exchange_rate?: string; expected_at?: string; notes?: string; items: { sku: string; description: string; quantity: string; unit_cost: string }[] }) => api<PurchaseOrder>(`${enterprise}/purchase-orders`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updatePurchaseOrderStatus = (token: string, id: string, status: string) => api<PurchaseOrder>(`${enterprise}/purchase-orders/${id}/status`, { token, method: 'PATCH', body: JSON.stringify({ status }) });
export const receivePurchaseOrder = (token: string, id: string, payload: { reference: string; note?: string; items: { sku: string; quantity: string }[] }) => api<PurchaseOrder>(`${enterprise}/purchase-orders/${id}/receipts`, { token, method: 'POST', body: JSON.stringify(payload) });
export const createImportCase = (token: string, payload: { purchase_order_id: string; incoterm: string; origin_country: string; destination_port: string; eta?: string; allocation_method: string; costs: { kind: string; description: string; amount: string; currency: string }[]; documents?: Record<string, unknown>[] }) => api<ImportCase>(`${enterprise}/import-cases`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updateImportCase = (token: string, id: string, payload: { eta?: string; allocation_method?: string; costs?: { kind: string; description: string; amount: string; currency: string }[]; documents?: Record<string, unknown>[] }) => api<ImportCase>(`${enterprise}/import-cases/${id}`, { token, method: 'PATCH', body: JSON.stringify(payload) });
export const updateImportCaseStatus = (token: string, id: string, status: string) => api<ImportCase>(`${enterprise}/import-cases/${id}/status`, { token, method: 'PATCH', body: JSON.stringify({ status }) });
export const createEmployeeContract = (token: string, payload: { employee_code?: string; employee_name: string; date_of_birth: string; national_id?: string; address?: string; phone?: string; email?: string; social_security_number?: string; insurance_provider?: string; insurance_member_number?: string; job_title: string; contract_type: string; start_date: string; monthly_salary: string; payment_type?: string; base_pay_amount?: string; standard_hours_weekly: string; currency: string; schedule?: Record<string, unknown> }) => api<EmployeeContract>(`${enterprise}/hr/contracts`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updateEmployeeContract = (token: string, id: string, payload: { employee_name?: string; national_id?: string; address?: string; phone?: string; email?: string; social_security_number?: string; insurance_provider?: string; insurance_member_number?: string; job_title?: string; monthly_salary?: string; payment_type?: string; base_pay_amount?: string; standard_hours_weekly?: string; schedule?: Record<string, unknown> }) => api<EmployeeContract>(`${enterprise}/hr/contracts/${id}`, { token, method: 'PATCH', body: JSON.stringify(payload) });
export const terminateEmployeeContract = (token: string, id: string) => api<EmployeeContract>(`${enterprise}/hr/contracts/${id}/terminate`, { token, method: 'POST', body: JSON.stringify({ status: 'TERMINATED' }) });
export const createAttendance = (token: string, payload: { contract_id: string; work_date: string; regular_hours: string; overtime_hours: string }) => api<AttendanceEntry>(`${enterprise}/hr/attendance`, { token, method: 'POST', body: JSON.stringify(payload) });
export const decideOvertime = (token: string, id: string, status: 'APPROVED' | 'REJECTED', note: string) => api<AttendanceEntry>(`${enterprise}/hr/attendance/${id}/overtime`, { token, method: 'PATCH', body: JSON.stringify({ status, note }) });
export const createLeaveRequest = (token: string, payload: { contract_id: string; leave_type: string; start_date: string; end_date: string; reason?: string }) => api<LeaveRequest>(`${enterprise}/hr/leave-requests`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updateLeaveRequestStatus = (token: string, id: string, status: string) => api<LeaveRequest>(`${enterprise}/hr/leave-requests/${id}/status`, { token, method: 'PATCH', body: JSON.stringify({ status }) });
export const createPayrollRun = (token: string, payload: { period_start: string; period_end: string; contract_ids: string[]; adjustments?: { contract_id: string; kind: string; description: string; amount: string }[] }) => api<PayrollRun>(`${enterprise}/hr/payroll-runs`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updatePayrollRunStatus = (token: string, id: string, status: string) => api<PayrollRun>(`${enterprise}/hr/payroll-runs/${id}/status`, { token, method: 'PATCH', body: JSON.stringify({ status }) });
export const getPayrollPolicies = (token: string) => api<import('../types').PayrollPolicy[]>(`${enterprise}/hr/payroll-policies`, { token });
export const createPayrollPolicy = (token: string, payload: { code: string; name: string; effective_from: string; effective_until?: string; rules: import('../types').PayrollRule[]; source_reference: string; active: boolean }) => api<import('../types').PayrollPolicy>(`${enterprise}/hr/payroll-policies`, { token, method: 'POST', body: JSON.stringify(payload) });
export const getPayrollVouchers = (token: string) => api<import('../types').PayrollVoucher[]>(`${enterprise}/hr/payroll-vouchers`, { token });
export const previewPrestations = (token: string, payload: { contract_id: string; termination_date: string; average_ordinary_monthly: string; include_notice: boolean; include_severance: boolean }) => api<import('../types').PrestationsPreview>(`${enterprise}/hr/prestations/preview`, { token, method: 'POST', body: JSON.stringify(payload) });
export const getEmployeeSelfService = (token: string) => api<import('../types').EmployeeSelfService>('/api/v1/staff/self-service/overview', { token });
export const employeePunch = (token: string, action: 'CHECK_IN' | 'CHECK_OUT', note?: string) => api<AttendanceEntry>('/api/v1/staff/self-service/punch', { token, method: 'POST', body: JSON.stringify({ action, note }) });
export const requestOwnLeave = (token: string, payload: { leave_type: string; start_date: string; end_date: string; reason?: string }) => api<LeaveRequest>('/api/v1/staff/self-service/leave-requests', { token, method: 'POST', body: JSON.stringify(payload) });
export const createUsedVehicle = (token: string, payload: { vin: string; make: string; model: string; model_year: number; mileage_km?: number; acquisition_type: string; acquisition_cost: string; reconditioning_cost: string; target_sale_price: string; owner_name?: string }) => api<UsedVehicle>(`${enterprise}/used-vehicles`, { token, method: 'POST', body: JSON.stringify(payload) });
export const updateUsedVehicleStatus = (token: string, id: string, status: string) => api<UsedVehicle>(`${enterprise}/used-vehicles/${id}/status`, { token, method: 'PATCH', body: JSON.stringify({ status }) });
export const createSocialChannel = (token: string, payload: { channel_type: string; name: string; external_account_id: string; credential_reference: string }) => api<SocialChannel>(`${enterprise}/social/channels`, { token, method: 'POST', body: JSON.stringify(payload) });
export const createSocialConversation = (token: string, payload: { channel_id: string; contact_name: string; contact_handle: string; consent_status: string; subject?: string }) => api<SocialConversation>(`${enterprise}/social/conversations`, { token, method: 'POST', body: JSON.stringify(payload) });
export const createSocialMessage = (token: string, conversationId: string, payload: { direction: 'INBOUND' | 'OUTBOUND'; body: string; human_approved: boolean }) => api(`${enterprise}/social/conversations/${conversationId}/messages`, { token, method: 'POST', body: JSON.stringify(payload) });
