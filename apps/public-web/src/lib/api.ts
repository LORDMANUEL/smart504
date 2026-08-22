import type { AppointmentSlot, BrandingProfile, ChatHistory, ChatReply, ChatSession, ClientAppointment, ClientDashboard, ClientVehicle, Product, ProductPage, StoreOrder, StoreOrderInput, VehicleFitment } from '../types';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export async function getBranding(): Promise<BrandingProfile> {
  const response = await fetch(`${API_BASE}/api/v1/branding`);
  if (!response.ok) throw new Error('No se pudo cargar la marca del taller');
  return response.json();
}

type ApiProductImage = {
  id: string;
  public_url: string;
  alt_text: string;
  source_type: string;
  source_page_url: string | null;
  attribution_text: string | null;
  mime_type: string;
  is_primary: boolean;
  sort_order: number;
};

type ApiProduct = {
  id: string;
  sku: string;
  name: string;
  short_description: string | null;
  description: string | null;
  category_id: string | null;
  brand: string | null;
  price: string | number;
  currency: string;
  stock_status: Product['stock_status'];
  active: boolean;
  compatibility_notes: string | null;
  source_system: string;
  source_reference: string | null;
  images: ApiProductImage[];
};

function mapProduct(product: ApiProduct): Product {
  return {
    id: product.id,
    sku: product.sku,
    name: product.name,
    description: product.short_description ?? product.description,
    brand: product.brand,
    category_id: product.category_id,
    display_price: String(product.price),
    currency: product.currency,
    stock_status: product.stock_status,
    compatibility_note: product.compatibility_notes,
    erpnext_item_code: product.source_system === 'ERPNEXT' ? product.source_reference : null,
    published: product.active,
    active: product.active,
    images: product.images.map((image) => ({
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

async function parseError(response: Response, fallback: string): Promise<Error> {
  const payload = await response.json().catch(() => null) as { detail?: string } | null;
  return new Error(typeof payload?.detail === 'string' ? payload.detail : fallback);
}

export async function loginClient(email: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/client-auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json' },
    credentials: 'include',
    body: new URLSearchParams({ username: email, password }),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible iniciar sesión');
}

export type ClientRegistrationOptions = {
  self_registration: boolean;
  managed_mail_domain: string;
  managed_mailbox_enabled: boolean;
  social_login: { enabled: boolean; configuration_source: string; login_url: string | null };
};

export async function getClientRegistrationOptions(): Promise<ClientRegistrationOptions> {
  const response = await fetch(`${API_BASE}/api/v1/client-auth/registration-options`, { headers: { Accept: 'application/json' } });
  if (!response.ok) throw await parseError(response, 'No se pudo consultar las opciones de acceso');
  return response.json() as Promise<ClientRegistrationOptions>;
}

export async function registerClient(payload: {
  full_name: string; phone: string; email: string; password: string; username?: string;
}): Promise<{ username: string; notification_email: string; managed_email: string; mailbox_status: string; message: string }> {
  const response = await fetch(`${API_BASE}/api/v1/client-auth/register`, {
    method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ ...payload, website: '' }),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible crear la cuenta');
  return response.json();
}

export async function getClientSession(): Promise<boolean> {
  const response = await fetch(`${API_BASE}/api/v1/client-auth/session`, { credentials: 'include' });
  return response.ok;
}

export async function logoutClient(): Promise<void> {
  await fetch(`${API_BASE}/api/v1/client-auth/logout`, { method: 'POST', credentials: 'include' });
}

export async function getAppointmentSlots(date: string): Promise<AppointmentSlot[]> {
  const response = await fetch(`${API_BASE}/api/v1/client-appointments/availability?date=${encodeURIComponent(date)}`, {
    credentials: 'include', headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw await parseError(response, 'No se pudo consultar el calendario');
  return (await response.json() as { slots: AppointmentSlot[] }).slots;
}

export async function getClientAppointments(): Promise<ClientAppointment[]> {
  const response = await fetch(`${API_BASE}/api/v1/client-appointments`, {
    credentials: 'include', headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw await parseError(response, 'No se pudieron consultar las citas');
  return response.json() as Promise<ClientAppointment[]>;
}

export async function createClientAppointment(payload: {
  vehicle_id: string; vehicle_summary: string; service_requested: string;
  scheduled_at: string; concern: string;
}): Promise<ClientAppointment> {
  const response = await fetch(`${API_BASE}/api/v1/client-appointments`, {
    method: 'POST',
    credentials: 'include', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw await parseError(response, 'No se pudo reservar el horario');
  return response.json() as Promise<ClientAppointment>;
}

export async function getClientDashboard(): Promise<ClientDashboard> {
  const response = await fetch(`${API_BASE}/api/v1/client-portal/dashboard`, { credentials: 'include', headers: { Accept: 'application/json' } });
  if (!response.ok) throw await parseError(response, 'No se pudo cargar el portal del cliente');
  return response.json() as Promise<ClientDashboard>;
}

export async function addClientVehicle(payload: { vin: string; plate?: string; make: string; model: string; model_year: number; engine?: string; mileage_km: number }): Promise<ClientVehicle> {
  const response = await fetch(`${API_BASE}/api/v1/client-portal/vehicles`, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!response.ok) throw await parseError(response, 'No se pudo registrar el vehículo');
  return response.json() as Promise<ClientVehicle>;
}

export async function getClientCompatibleParts(vehicleId: string): Promise<Product[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/client-portal/vehicles/${encodeURIComponent(vehicleId)}/compatible-parts`,
    { credentials: 'include', headers: { Accept: 'application/json' } },
  );
  if (!response.ok) throw await parseError(response, 'No se pudieron consultar los repuestos compatibles');
  return (await response.json() as ApiProduct[]).map(mapProduct);
}

export async function updateClientProfile(payload: { full_name: string; email: string; username: string; credit_requested: boolean; credit_amount?: number; new_password?: string }): Promise<ClientDashboard['profile']> {
  const response = await fetch(`${API_BASE}/api/v1/client-portal/profile`, { method: 'PUT', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!response.ok) throw await parseError(response, 'No se pudo guardar la configuración');
  return response.json() as Promise<ClientDashboard['profile']>;
}

export async function decideClientQuoteLine(quoteId: string, lineId: string, decision: 'APPROVED' | 'REJECTED'): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/client-portal/quotes/${quoteId}/lines/${lineId}?decision=${decision}`, { method: 'PATCH', credentials: 'include' });
  if (!response.ok) throw await parseError(response, 'No se pudo guardar la decisión');
}

export async function clientDocument(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`, { credentials: 'include' });
  if (!response.ok) throw await parseError(response, 'No se pudo generar el documento');
  return response.blob();
}

export async function getProducts(query: string, signal?: AbortSignal): Promise<ProductPage> {
  const params = new URLSearchParams({ limit: '24', offset: '0' });
  if (query.trim()) params.set('q', query.trim());
  const response = await fetch(`${API_BASE}/api/v1/catalog/products?${params.toString()}`, {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw await parseError(response, 'No se pudo consultar el catálogo');
  const payload = await response.json() as ApiProduct[] | ProductPage;
  if (!Array.isArray(payload)) {
    const items = payload.items.map((item) => 'display_price' in item ? item : mapProduct(item as unknown as ApiProduct));
    return { ...payload, items };
  }
  return { items: payload.map(mapProduct), total: payload.length, limit: 24, offset: 0 };
}

export async function getVehicleFitment(vin: string, signal?: AbortSignal): Promise<VehicleFitment> {
  const response = await fetch(`${API_BASE}/api/v1/catalog/fitment?vin=${encodeURIComponent(vin)}`, {
    signal,
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) throw await parseError(response, 'No se pudo validar el VIN');
  const payload = await response.json() as { status: VehicleFitment['status']; vehicle: VehicleFitment['vehicle']; products: ApiProduct[] };
  return { ...payload, products: payload.products.map(mapProduct) };
}

export type BookingInput = {
  customer_name: string;
  phone: string;
  email?: string;
  vehicle_summary: string;
  requested_service: string;
  preferred_date?: string;
  notes?: string;
  idempotency_key: string;
};

export async function createBooking(payload: BookingInput): Promise<{ id: string; status: string }> {
  const response = await fetch(`${API_BASE}/api/v1/bookings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      full_name: payload.customer_name,
      phone: payload.phone,
      email: payload.email || null,
      vehicle_summary: payload.vehicle_summary,
      service_requested: payload.requested_service,
      preferred_date: payload.preferred_date || null,
      concern: payload.notes?.trim() || `Solicitud de ${payload.requested_service} para ${payload.vehicle_summary}.`,
    }),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible registrar la reserva');
  return response.json() as Promise<{ id: string; status: string }>;
}

export async function createChatSession(): Promise<ChatSession> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      locale: navigator.language || 'es-HN',
      page_url: window.location.href,
      referrer: document.referrer || null,
      accepted_privacy: true,
    }),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible iniciar el asistente');
  return response.json() as Promise<ChatSession>;
}

export async function getChatHistory(session: ChatSession): Promise<ChatHistory> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions/${session.session_id}/messages`, {
    headers: {
      Accept: 'application/json',
      'X-Chat-Session-Token': session.session_token,
    },
  });
  if (!response.ok) throw await parseError(response, 'No fue posible recuperar la conversación');
  return response.json() as Promise<ChatHistory>;
}

export async function sendChatMessage(
  session: ChatSession,
  message: string,
  clientMessageId: string,
): Promise<ChatReply> {
  const response = await fetch(`${API_BASE}/api/v1/chat/sessions/${session.session_id}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Chat-Session-Token': session.session_token,
    },
    body: JSON.stringify({ message, client_message_id: clientMessageId }),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible enviar el mensaje');
  return response.json() as Promise<ChatReply>;
}


export async function createStoreOrder(payload: StoreOrderInput): Promise<StoreOrder> {
  const response = await fetch(`${API_BASE}/api/v1/store/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible registrar la solicitud de pedido');
  return response.json() as Promise<StoreOrder>;
}

export async function createLead(payload: {
  full_name: string; phone: string; email?: string; interest: string; vehicle_summary?: string;
  chat_session_id?: string;
}): Promise<{ number: string; status: string }> {
  const response = await fetch(`${API_BASE}/api/v1/leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ ...payload, email: payload.email || null, source: 'AI_CHAT' }),
  });
  if (!response.ok) throw await parseError(response, 'No fue posible solicitar un asesor');
  return response.json() as Promise<{ number: string; status: string }>;
}
