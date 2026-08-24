export type ProductImage = {
  id: string;
  source: 'UPLOAD' | 'EXTERNAL' | 'GOOGLE' | string;
  url: string;
  alt_text: string;
  attribution: string | null;
  source_page_url: string | null;
  sort_order: number;
  is_primary: boolean;
  mime_type: string | null;
};

export type Product = {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  brand: string | null;
  category_id: string | null;
  display_price: string;
  currency: string;
  stock_status: 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK' | 'ON_REQUEST';
  compatibility_note: string | null;
  erpnext_item_code: string | null;
  published: boolean;
  active: boolean;
  images: ProductImage[];
};

export type ProductPage = {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
};

export type VehicleFitment = {
  status: 'MATCHED' | 'NOT_FOUND' | 'AUTH_REQUIRED';
  vehicle: { make: string; model: string; model_year: number | null; label: string } | null;
  products: Product[];
};

export type ChatMessage = {
  id: string;
  role: 'assistant' | 'user' | 'system';
  content: string;
  created_at: string;
  audit_id?: string | null;
  mode?: string | null;
  suggested_actions?: string[];
};

export type ChatSession = {
  session_id: string;
  session_token: string;
  expires_at: string;
  welcome_message: string;
  quick_prompts?: string[];
  privacy_notice?: string;
};

export type ChatReply = {
  session_id: string;
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  audit_id: string | null;
  mode: string;
  suggested_actions: string[];
};

export type ChatHistory = {
  session_id: string;
  messages: ChatMessage[];
};


export type StoreOrderItemInput = {
  product_id: string;
  quantity: number;
};

export type StoreOrderInput = {
  customer_name: string;
  phone: string;
  email?: string;
  vehicle_vin?: string;
  notes?: string;
  promo_code?: string;
  idempotency_key: string;
  items: StoreOrderItemInput[];
};

export type StoreOrderItem = {
  id: string;
  product_id: string;
  sku: string;
  name: string;
  quantity: number;
  unit_price: string;
  line_total: string;
};

export type StoreOrder = {
  id: string;
  order_number: string;
  status: string;
  currency: string;
  subtotal: string;
  discount?: string;
  total?: string;
  promo_code?: string | null;
  items: StoreOrderItem[];
};

export type StorePromotion = {
  id: string; title: string; description: string; audience: string; call_to_action: string;
  media_url: string | null; media_type: string | null; public_path: string;
  promo_code?: string | null; discount_percent?: number; store_banner?: boolean;
  valid_from?: string | null; valid_until?: string | null;
};

export type AppointmentSlot = { starts_at: string; available: boolean };
export type ClientAppointment = {
  id: string;
  vehicle_id: string;
  vehicle_summary: string;
  service_requested: string;
  scheduled_at: string;
  duration_minutes: number;
  concern: string;
  status: string;
  source: string;
  created_at: string;
};

export type ClientVehicle = {
  id: string; label: string; make: string; model: string; model_year: number | null; engine: string | null;
  plate: string | null; vin: string | null; mileage_km: number; photo_url: string | null;
  maintenance: { status: string; next_service_km: number; oil_last_km: number; oil_next_km: number };
  history: Array<{ id: string; type: string; reference: string; summary: string; mileage_km: number | null; date: string }>;
  advice: string[];
};
export type ClientQuote = {
  id: string; number: string; work_order_id: string; status: string; notes: string | null; subtotal: string;
  discount: string; tax: string; total: string; created_at: string;
  lines: Array<{ id: string; code: string; description: string; quantity: string; unit_price: string; line_total: string; approval_status: string }>;
};
export type ClientDashboard = {
  profile: { full_name: string; email: string; notification_email?: string; managed_email?: string | null; mailbox_status?: string; username: string; mfa_enabled: boolean; loyalty_enabled: boolean; loyalty_points: number; credit_requested: boolean; credit_amount?: string | null; credit_status: string };
  vehicles: ClientVehicle[];
  alerts: Array<{ id: string; kind: string; title: string; detail: string; status: string; quote_id?: string }>;
  notifications: Array<{ id: string; event: string; reference: string; title: string; message: string; channel: string; delivery_status: string; created_at: string }>;
  quotes: ClientQuote[];
  invoices: Array<{ number: string; work_order_id: string; total: string; created_at: string }>;
};
export type MaintenancePackage = { id: string; name: string; description: string; points: number; service: string; available: boolean };
export type BrandingProfile = {
  organization_id: string; display_name: string; legal_name: string; tax_id: string; address: string;
  phone: string; email: string | null; website: string; primary_color: string; accent_color: string;
  surface_color: string; text_color: string; logo_url: string; logo_dark_url: string; favicon_url: string;
  document_footer: string; asset_history: { asset_type: string; url: string; actor: string; created_at: string }[];
  seasonal_theme_enabled: boolean; seasonal_theme_code: import('./lib/seasonalThemes').SeasonalThemeCode;
  seasonal_theme_title: string; seasonal_theme_message: string;
  updated_at: string | null;
};
