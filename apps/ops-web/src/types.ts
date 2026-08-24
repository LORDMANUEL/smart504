export type WorkOrderStatus =
  | 'CREATED'
  | 'QUOTED_BY_TECHNICIAN'
  | 'PENDING_CUSTOMER_APPROVAL'
  | 'PENDING_PARTS'
  | 'READY_TO_INVOICE'
  | 'INVOICED';

export type WorkOrderCard = {
  id: string;
  external_reference: string;
  customer_id: string;
  vehicle_id: string;
  title: string;
  technician_name: string | null;
  bay_code: string | null;
  status: WorkOrderStatus;
  quote_total: string | null;
  invoice_reference: string | null;
  promised_at: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  vehicle_label: string;
  customer_name: string;
  concern?: string;
  diagnosis?: string | null;
  parts_required?: WorkOrderPartRequest[] | null;
  events?: WorkOrderEvent[];
};

export type WorkOrderPartRequest = {
  request_id?: string;
  product_id: string;
  sku: string;
  name: string;
  quantity: number;
  qty?: number;
  note: string;
  status: string;
  actor: string;
  requested_at: string;
  stock_status: string;
  location: string;
  delivered_by?: string;
  delivered_at?: string;
};

export type WorkOrderEvent = {
  id: string;
  event_type: string;
  actor: string;
  reason: string;
  created_at: string;
  payload?: Record<string, unknown>;
};

export type BoardColumn = { status: WorkOrderStatus; label: string; cards: WorkOrderCard[] };
export type BoardResponse = { columns: BoardColumn[] };
export type WorkshopViewSetting = { default_view: 'KANBAN' | 'BAYS'; bays_enabled: boolean; bay_codes?: string[] };
export type CatalogImportError = { sheet: string; row: number; column: string; message: string };
export type CatalogImportPreview = {
  summary: { labor: number; parts: number; errors: number };
  labor: unknown[];
  parts: unknown[];
  errors: CatalogImportError[];
};

export type ProductImage = {
  id: string;
  source: string;
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
  purchase_cost: string;
  landed_cost_factor: string;
  target_markup_percent: string;
  minimum_markup_percent: string;
  abc_class: 'A' | 'B' | 'C';
  xyz_class: 'X' | 'Y' | 'Z';
  currency: string;
  stock_status: string;
  stock_qty: string;
  compatibility_note: string | null;
  erpnext_item_code: string | null;
  published: boolean;
  active: boolean;
  images: ProductImage[];
};

export type BookingStatus = 'NEW' | 'CONTACTED' | 'CONFIRMED' | 'CANCELLED';
export type Booking = {
  id: string;
  customer_id?: string | null;
  vehicle_id?: string | null;
  full_name: string;
  phone: string;
  email: string | null;
  vehicle_summary: string;
  service_requested: string;
  preferred_date: string | null;
  scheduled_at?: string | null;
  duration_minutes?: number | null;
  concern: string;
  status: BookingStatus;
  source: string;
  created_at: string;
  updated_at: string;
};
export type LaborCatalogItem = { code: string; description: string; hours: string; price: string };
export type ProductPage = { items: Product[]; total: number; limit: number; offset: number };
export type HaNode = {
  node_id: string;
  role: string;
  healthy: boolean;
  stale: boolean;
  details: Record<string, unknown>;
  last_seen_at: string;
};

export type StoreOrderStatus =
  | 'PENDING_CONFIRMATION'
  | 'CONTACTED'
  | 'CONFIRMED'
  | 'PAID'
  | 'RESERVED'
  | 'PREPARING'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'RETURN_REQUESTED'
  | 'RETURNED'
  | 'SYNCED'
  | 'NO_RESPONSE'
  | 'LOST'
  | 'CANCELLED';

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
  customer_name: string;
  phone: string;
  email: string | null;
  vehicle_vin: string | null;
  notes: string | null;
  status: StoreOrderStatus;
  currency: string;
  subtotal: string;
  erpnext_sales_order_id: string | null;
  source?: string;
  branch_id?: string | null;
  assigned_cashier?: string | null;
  fulfillment_status?: string;
  reservation_expires_at?: string | null;
  whatsapp_status?: string;
  customer_id?: string | null;
  created_at: string;
  updated_at: string;
  items: StoreOrderItem[];
};

export type FlowEvent = {
  id: string;
  module: string;
  action: string;
  item_reference: string;
  actor: string;
  result: 'SUCCESS' | 'FAILED' | 'CANCELLED';
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type FlowHeatmapCell = {
  module: string;
  action: string;
  count: number;
  last_seen_at: string;
};

export type QuoteLine = {
  id?: string;
  line_type: 'LABOR' | 'PART' | 'OTHER';
  code: string;
  description: string;
  quantity: string;
  unit_price: string;
  unit_cost: string;
  line_total?: string;
  approval_status?: 'PENDING' | 'APPROVED' | 'REJECTED';
  source_reference?: string | null;
};
export type Quote = {
  id: string;
  number: string;
  work_order_id: string | null;
  customer_id?: string | null;
  vehicle_id?: string | null;
  converted_work_order_id?: string | null;
  status: 'DRAFT' | 'SENT' | 'APPROVED' | 'REJECTED';
  notes: string | null;
  discount: string;
  tax: string;
  subtotal: string;
  total: string;
  created_by: string;
  approved_by: string | null;
  approved_at: string | null;
  erpnext_quotation_id?: string | null;
  erp_sync_status?: 'PENDING' | 'SYNCED' | 'FAILED' | 'BLOCKED';
  erp_sync_error?: string | null;
  erp_last_synced_at?: string | null;
  created_at: string;
  updated_at: string;
  lines: QuoteLine[];
};
export type CashSession = {
  id: string;
  opened_by: string;
  closed_by: string | null;
  status: 'OPEN' | 'CLOSED';
  opening_balance: string;
  counted_cash: string | null;
  expected_cash: string | null;
  difference: string | null;
  opened_at: string;
  closed_at: string | null;
};
export type Payment = {
  id: string;
  receipt_number: string;
  cash_session_id: string;
  work_order_id: string | null;
  quote_id: string | null;
  retail_sale_id: string | null;
  method: 'CASH' | 'CARD' | 'TRANSFER';
  amount: string;
  reference: string | null;
  status: string;
  received_by: string;
  created_at: string;
};
export type CashSummary = {
  session: CashSession | null;
  payments: Payment[];
  totals_by_method: Record<string, string>;
  total_collected: string;
};

export type CounterSaleItem = {
  id: string; product_id: string; sku: string; name: string; quantity: string;
  returned_quantity: string; unit_price: string; unit_cost: string; line_total: string;
};
export type CounterSale = {
  id: string; organization_id: string; branch_id: string; warehouse_id: string;
  cash_session_id: string; sale_number: string; invoice_number: string;
  customer_id: string | null; customer_name: string; phone: string | null;
  tax_id: string | null; vehicle_vin: string | null; status: 'COMPLETED' | 'PARTIAL_RETURN' | 'RETURNED';
  currency: string; subtotal: string; discount: string; tax: string; total: string;
  payment_method: 'CASH' | 'CARD' | 'TRANSFER'; payment_reference: string | null;
  erpnext_invoice_id: string | null; erpnext_payment_id: string | null;
  sync_status: 'PENDING' | 'SYNCING' | 'SYNCED' | 'FAILED' | 'BLOCKED';
  sync_error: string | null; sync_attempts: number; last_sync_at: string | null; created_by: string;
  completed_at: string; created_at: string; updated_at: string; items: CounterSaleItem[];
  payment: Payment | null;
};
export type CounterSalesContext = {
  owner_approval_email: string;
  branches: { id: string; code: string; name: string }[];
  warehouses: { id: string; branch_id: string; code: string; name: string }[];
  products: { id: string; sku: string; name: string; price: string; purchase_cost: string; landed_cost_factor: string; target_markup_percent: string; minimum_sale_price: string; suggested_sale_price: string; abc_class: 'A' | 'B' | 'C'; xyz_class: 'X' | 'Y' | 'Z'; stock_qty: string; stock_status: string; compatibility_note?: string | null; image_url?: string | null; warehouse_stock?: Record<string, string>; sellable: boolean; blocking_reasons: ('SIN_ITEM' | 'SIN_PRECIO' | 'SIN_EXISTENCIA')[] }[];
};
export type CounterItemRequest = {
  id: string; organization_id: string; number: string; branch_id: string; warehouse_id: string | null;
  product_id: string | null; search_query: string; customer_name: string; phone: string | null;
  vehicle_vin: string | null; quantity: string; notes: string | null; status: string;
  requested_by: string; created_at: string; updated_at: string;
};
export type ApprovalRequest = { id: string; sale_id: string; request_type: 'RETURN' | 'WARRANTY'; status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CONSUMED' | 'EXPIRED'; requested_by: string; owner_email: string; reason: string; payload_json: Record<string, unknown>; expires_at: string; delivery_status: string; delivery_error: string | null; approval_url?: string | null; token?: string | null; created_at: string };
export type ManagementSummary = { currency: string; gross_sales: string; refunds: string; net_sales: string; net_cost: string; gross_profit: string; gross_margin_percent: string; erp_pending: number; quotes_by_status: Record<string, number>; approvals_by_status: Record<string, number>; inventory_policy: { product_id: string; sku: string; name: string; abc_class: string; xyz_class: string; stock_qty: string; sold_180_days: string; stock_value: string; minimum_sale_price: string; suggested_sale_price: string; recommendation: string }[]; accounting_source: string; operational_projection: string };
export type CounterFitment = {
  status: 'MATCHED' | 'NOT_FOUND';
  vehicle: { id: string; customer_id: string; label: string; make: string; model: string; model_year: number | null; vin: string; plate: string | null; owner: string | null } | null;
  products: CounterSalesContext['products'];
};

export type Branch = { id: string; code: string; name: string; address: string | null; phone: string | null; email_domain: string | null; timezone: string; active: boolean };
export type WarehouseLocation = { id: string; branch_id: string; code: string; name: string; warehouse_type: 'STOCK' | 'PROCESS' | 'TRANSIT' | 'RETURNS'; active: boolean };
export type InventoryReservation = { id: string; reference: string; product_id: string; warehouse_id: string; store_order_id: string | null; work_order_id: string | null; quantity: string; status: string; expires_at: string | null; actor: string; created_at: string };
export type InventoryTransfer = { id: string; number: string; from_warehouse_id: string; to_warehouse_id: string; status: string; items_json: Record<string, unknown>[]; carrier: string | null; tracking_number: string | null; guide_image_url: string | null; actor: string; created_at: string };
export type Shipment = { id: string; number: string; store_order_id: string; from_warehouse_id: string; status: string; carrier: string; tracking_number: string | null; guide_image_url: string | null; recipient_name: string; recipient_phone: string; delivery_notes: string | null; actor: string; created_at: string };
export type QualityCase = { id: string; number: string; case_type: string; customer_id: string | null; vehicle_id: string | null; work_order_id: string | null; store_order_id: string | null; status: string; description: string; resolution: string | null; evidence_url: string | null; actor: string; created_at: string; updated_at: string };
export type SalesLead = { id: string; number: string; source: string; full_name: string; phone: string; email: string | null; interest: string; vehicle_summary: string | null; status: 'NEW' | 'QUALIFYING' | 'ADVISOR' | 'QUOTED' | 'WON' | 'LOST'; assigned_to: string | null; chat_session_id: string | null; next_action_at: string | null; notes: string | null; created_at: string; updated_at: string };
export type ManagementDocument = { id: string; branch_id: string; document_type: string; number: string; valid_from: string | null; valid_until: string | null; file_url: string | null; status: string; metadata_json: Record<string, unknown>; created_at: string };
export type OperationsOverview = { branches: Branch[]; warehouses: WarehouseLocation[]; reservations: InventoryReservation[]; transfers: InventoryTransfer[]; shipments: Shipment[]; quality_cases: QualityCase[]; leads: SalesLead[]; management_documents: ManagementDocument[] };
export type MarketingCampaign = { id: string; title: string; description: string; audience: string; valid_from: string | null; valid_until: string | null; price_from: number | null; call_to_action: string; tv_enabled: boolean; display_seconds: number; promo_code?: string | null; discount_percent?: number; store_banner?: boolean; slug: string; status: 'DRAFT' | 'PUBLISHED'; media_url: string | null; media_type: 'IMAGE' | 'VIDEO' | null; clicks: number; public_path: string; created_at: string };
export type MaintenancePackage = { id: string; name: string; description: string; points: number; service: string; active: boolean; created_at: string };
export type PrintProfile = { printer_type: 'LASER_INKJET' | 'THERMAL' | 'PREPRINTED' | 'BROWSER_PDF'; orientation: 'PORTRAIT' | 'LANDSCAPE'; margins_mm: { top: number; right: number; bottom: number; left: number }; copies: number; show_logo: boolean; preprinted_background: boolean };
export type DocumentTemplateVersion = { id: string; template_id: string; version: number; status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'; paper_size: 'LETTER' | 'A4' | 'THERMAL_80' | 'THERMAL_58'; print_profile_json: PrintProfile; html_template: string; css_text: string; variables_json: string[]; change_note: string | null; created_by: string; created_at: string; published_at: string | null };
export type DocumentTemplate = { id: string; organization_id: string; branch_id: string | null; code: string; name: string; document_type: string; status: string; current_version: number; published_version: number | null; active: boolean; created_at: string; updated_at: string; versions: DocumentTemplateVersion[] };
export type DocumentRender = { id: string; template_id: string | null; template_version_id: string | null; document_type: string; business_reference: string; content_sha256: string; created_by: string; created_at: string };
export type StaffRole = 'OWNER' | 'ADMIN' | 'MANAGER' | 'ACCOUNTANT' | 'TECHNICIAN' | 'CASHIER' | 'WAREHOUSE' | 'RECEPTION' | 'MARKETING' | 'AUDITOR';
export type StaffUser = { id: string; email: string; organization_id: string; branch_id: string | null; employee_code: string; full_name: string; job_title: string | null; role: StaffRole; permissions_json: string[]; phone: string | null; is_active: boolean; is_superuser: boolean; is_verified: boolean; last_login_at: string | null; failed_login_attempts: number; locked_until: string | null; mfa_enabled: boolean; created_at: string; updated_at: string };
export type StaffTechnician = Pick<StaffUser, 'id' | 'employee_code' | 'full_name' | 'job_title'>;
export type StaffCompensationProfile = {
  id: string; staff_user_id: string; organization_id: string;
  fixed_monthly_salary: string; productive_hours_monthly: string;
  base_hourly_wage: string; specialized_hourly_wage: string;
  employer_burden_percent: string; standard_sale_rate: string;
  specialized_sale_rate: string; currency: string; effective_from: string;
  source_system: string; source_reference: string | null;
  fixed_hourly_allocation: string; standard_hourly_cost: string;
  specialized_hourly_cost: string; created_at: string; updated_at: string;
};
export type WorkOrderLaborEntry = {
  id: string; work_order_id: string; technician_user_id: string; technician_name: string;
  service_code: string; description: string; rate_kind: 'STANDARD' | 'SPECIALIZED';
  hours: string; hourly_sale_rate: string; sale_total: string; actor: string; created_at: string;
};
export type StaffAccessEvent = { id: string; user_id: string | null; action: string; result: string; detail: string | null; created_at: string };
export type Supplier = { id: string; code: string; name: string; tax_id: string | null; email: string | null; phone: string | null; payment_terms_days: number; currency: string; active: boolean; erpnext_supplier_id: string | null; erp_sync_status: string; erp_sync_error: string | null; created_at: string };
export type PurchaseOrder = { id: string; number: string; branch_id: string | null; supplier_id: string; status: string; currency: string; exchange_rate: string; subtotal: string; tax: string; total: string; expected_at: string | null; notes: string | null; items_json: { sku?: string; description?: string; quantity?: string; received_quantity?: string; unit_cost?: string }[]; created_by: string; erpnext_purchase_order_id: string | null; erp_sync_status: string; erp_sync_error: string | null; created_at: string };
export type ImportCase = { id: string; number: string; purchase_order_id: string; status: string; incoterm: string; origin_country: string; destination_port: string; eta: string | null; costs_json: { kind?: string; description?: string; amount?: string; currency?: string }[]; documents_json: Record<string, unknown>[]; additional_cost_total: string; allocation_method: string; landed_cost_status: string; erpnext_landed_cost_id: string | null; created_at: string };
export type EmployeeContract = { id: string; branch_id: string | null; staff_user_id: string | null; employee_code: string; employee_name: string; date_of_birth: string | null; national_id: string | null; address: string | null; phone: string | null; email: string | null; social_security_number: string | null; insurance_provider: string | null; insurance_member_number: string | null; job_title: string; contract_type: string; status: string; start_date: string; end_date: string | null; monthly_salary: string; payment_type: string; base_pay_amount: string; standard_hours_weekly: string; currency: string; benefits_json: Record<string, unknown>[]; schedule_json: Record<string, unknown>; erpnext_employee_id: string | null; erp_sync_status: string; created_at: string };
export type AttendanceEntry = { id: string; contract_id: string; work_date: string; regular_hours: string; overtime_hours: string; overtime_status: string; overtime_approved_by: string | null; overtime_approval_note: string | null; status: string; check_in_at: string | null; check_out_at: string | null; note: string | null; recorded_by: string };
export type LeaveRequest = { id: string; contract_id: string; leave_type: string; start_date: string; end_date: string; reason: string | null; status: string; requested_by: string; approved_by: string | null };
export type PayrollRun = { id: string; number: string; period_start: string; period_end: string; status: string; lines_json: Record<string, unknown>[]; gross_total: string; deduction_total: string; net_total: string; created_by: string; erpnext_payroll_entry_id: string | null; erp_sync_status: string; created_at: string };
export type PayrollRule = { code: string; label: string; side: 'EMPLOYEE_DEDUCTION' | 'EMPLOYER_CONTRIBUTION'; calculation: 'PERCENT' | 'FIXED'; rate: string; ceiling?: string | null; enabled: boolean };
export type PayrollPolicy = { id: string; code: string; name: string; effective_from: string; effective_until: string | null; rules_json: PayrollRule[]; source_reference: string; approved_by: string; active: boolean; created_at: string };
export type PayrollVoucher = { id: string; number: string; payroll_run_id: string; contract_id: string; period_start: string; period_end: string; gross: string; deductions: string; employer_contributions: string; net: string; details_json: Record<string, unknown>; status: string; issued_at: string | null };
export type EmployeeSelfService = { linked: boolean; contract: EmployeeContract | null; today_attendance: AttendanceEntry | null; leave_requests: LeaveRequest[]; vouchers: PayrollVoucher[] };
export type PrestationsPreview = { employee_code: string; service_days: number; daily_average: string; notice_days: string; severance_days: string; vacation_days: string; notice_amount: string; severance_amount: string; vacation_amount: string; thirteenth_accrual: string; fourteenth_accrual: string; estimated_total: string; legal_notice: string };
export type UsedVehicle = { id: string; branch_id: string | null; vin: string; make: string; model: string; model_year: number; mileage_km: number | null; acquisition_type: string; acquisition_cost: string; reconditioning_cost: string; target_sale_price: string; status: string; owner_name: string | null; inspection_json: Record<string, unknown>; media_json: Record<string, unknown>[]; published_at: string | null; sold_at: string | null; erpnext_item_id: string | null; created_at: string };
export type SocialChannel = { id: string; channel_type: string; name: string; external_account_id: string; credential_reference: string; webhook_status: string; active: boolean; created_at: string };
export type SocialConversation = { id: string; channel_id: string; contact_name: string; contact_handle: string; subject: string | null; status: string; consent_status: string; assigned_to: string | null; lead_id: string | null; last_message_at: string; created_at: string };
export type EnterpriseOverview = { counts: Record<string, number>; suppliers: Supplier[]; purchase_orders: PurchaseOrder[]; import_cases: ImportCase[]; contracts: EmployeeContract[]; attendance: AttendanceEntry[]; leave_requests: LeaveRequest[]; payroll_runs: PayrollRun[]; used_vehicles: UsedVehicle[]; social_channels: SocialChannel[]; social_conversations: SocialConversation[] };
export type BrandingProfile = {
  organization_id: string; display_name: string; legal_name: string; tax_id: string; address: string;
  phone: string; email: string | null; website: string; primary_color: string; accent_color: string;
  surface_color: string; text_color: string; logo_url: string; logo_dark_url: string; favicon_url: string;
  document_footer: string; asset_history: { asset_type: string; url: string; actor: string; created_at: string }[];
  seasonal_theme_enabled: boolean; seasonal_theme_code: 'NONE' | 'JANUARY_NEW_YEAR' | 'FEBRUARY_FRIENDSHIP' | 'MARCH_MAINTENANCE' | 'APRIL_ROAD_SAFETY' | 'MAY_FAMILY' | 'JUNE_ENVIRONMENT' | 'JULY_TRAVEL' | 'AUGUST_WORKSHOP' | 'PATRIA_SEPTEMBER' | 'OCTOBER_PREVENTION' | 'NOVEMBER_SAVINGS' | 'DECEMBER_HOLIDAYS';
  seasonal_theme_title: string; seasonal_theme_message: string;
  updated_at: string | null;
};
