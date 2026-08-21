frappe.pages["smartdiag-workshop"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({ parent: wrapper, title: __("SmartDiag504"), single_column: true });
  new SmartDiag504ERPPage(page, wrapper);
};

class SmartDiag504ERPPage {
  constructor(page, wrapper) {
    this.page = page;
    this.wrapper = $(wrapper).find(".layout-main-section");
    this.readableDoctypes = new Set(frappe.boot?.user?.can_read || []);
    this.roles = new Set(frappe.user_roles || []);
    this.render();
    this.loadMetrics();
    this.loadActivity();
    this.loadSystemStatus();
  }

  internalLink(label, doctype, routeType = "List") {
    if (routeType === "List" && !this.readableDoctypes.has(doctype)) return "";
    if (routeType === "query-report" && !this.canOpenReports()) return "";
    return `<a class="smartdiag-erp__link" href="#" data-doctype="${doctype}" data-route-type="${routeType}">${__(label)}</a>`;
  }

  canOpenReports() {
    return ["Administrator", "System Manager", "Accounts Manager", "Accounts User", "Stock Manager", "Stock User"]
      .some((role) => this.roles.has(role));
  }

  section(title, description, links) {
    const visibleLinks = links.filter(Boolean);
    if (!visibleLinks.length) return "";
    return `<article class="smartdiag-erp__section"><h2>${__(title)}</h2><p>${__(description)}</p><div class="smartdiag-erp__links">${visibleLinks.join("")}</div></article>`;
  }

  render() {
    const sections = [
      this.section("Taller y servicio", "Órdenes, recepción, diagnóstico, bahías y control de calidad.", [
        this.internalLink("Órdenes de trabajo", "Service Order"), this.internalLink("Cotizaciones de servicio", "Service Quotation"),
        this.internalLink("Vehículos", "SmartDiag Vehicle"), this.internalLink("Recepción del vehículo", "Vehicle Check In"),
        this.internalLink("Bahías", "Workshop Bay"), this.internalLink("Control de calidad", "Workshop Quality Check"),
      ]),
      this.section("Ventas, caja y clientes", "Facturación, cobros, cuentas por cobrar y documentos comerciales.", [
        this.internalLink("Clientes", "Customer"), this.internalLink("Facturas de venta", "Sales Invoice"),
        this.internalLink("Pagos", "Payment Entry"), this.internalLink("Cotizaciones", "Quotation"),
        this.internalLink("Cuentas por cobrar", "Accounts Receivable", "query-report"), this.internalLink("Libro mayor", "General Ledger", "query-report"),
      ]),
      this.section("Repuestos, compras y bodega", "Catálogo, existencias, proveedores, compras y movimientos de almacén.", [
        this.internalLink("Artículos y repuestos", "Item"), this.internalLink("Bodegas", "Warehouse"),
        this.internalLink("Movimientos de inventario", "Stock Entry"), this.internalLink("Proveedores", "Supplier"),
        this.internalLink("Órdenes de compra", "Purchase Order"), this.internalLink("Balance de existencias", "Stock Balance", "query-report"),
      ]),
      this.section("Personal y nómina", "Empleados, asistencia, permisos, salarios y entradas de nómina.", [
        this.internalLink("Empleados", "Employee"), this.internalLink("Asistencia", "Attendance"),
        this.internalLink("Permisos", "Leave Application"), this.internalLink("Estructuras salariales", "Salary Structure"),
        this.internalLink("Entradas de nómina", "Payroll Entry"), this.internalLink("Comprobantes de salario", "Salary Slip"),
      ]),
      this.section("Reportes gerenciales", "Contabilidad, cartera, compras, ventas y rotación calculadas por ERPNext.", [
        this.internalLink("Pérdidas y ganancias", "Profit and Loss Statement", "query-report"),
        this.internalLink("Balance de comprobación", "Trial Balance", "query-report"),
        this.internalLink("Cuentas por pagar", "Accounts Payable", "query-report"),
      ]),
      this.section("Redes, correo y automatización", "Conectores autorizados para correo, redes sociales, webhooks y avisos del taller.", [
        this.internalLink("Cuentas de correo", "Email Account"), this.internalLink("Comunicaciones", "Communication"),
        this.internalLink("Notificaciones", "Notification"), this.internalLink("Webhooks", "Webhook"),
        this.internalLink("Acceso con redes sociales", "Social Login Key"), this.internalLink("Aplicaciones OAuth", "OAuth Client"),
      ]),
      this.section("Logs, flujos y contabilidad", "Trazabilidad de eventos, integraciones, errores y asientos contables del ERP.", [
        this.internalLink("Flujos SmartDiag", "SmartDiag Event Outbox"), this.internalLink("Solicitudes de integración", "Integration Request"),
        this.internalLink("Registro de errores", "Error Log"), this.internalLink("Actividad de usuarios", "Activity Log"),
        this.internalLink("Asientos contables", "GL Entry"), this.internalLink("Comprobantes de diario", "Journal Entry"),
      ]),
    ];
    this.wrapper.html(`<div class="smartdiag-erp">
      <section class="smartdiag-erp__hero"><div><span class="smartdiag-erp__eyebrow">Administración conectada al taller</span><h1>Centro administrativo SmartDiag504</h1><p>ERPNext conserva empleados, inventario, compras, facturas, pagos y contabilidad. Las pantallas SmartDiag504 simplifican el trabajo diario y sincronizan aquí los documentos autoritativos.</p><div class="smartdiag-erp__actions">
        <a class="smartdiag-erp__action smartdiag-erp__action--primary" href="https://taller.nexusmedi.org/tallerv1/login" target="_blank" rel="noopener">Abrir taller operativo</a>
        <a class="smartdiag-erp__action" href="https://taller.nexusmedi.org/tallerv1/tecnico" target="_blank" rel="noopener">Técnico móvil</a>
        <a class="smartdiag-erp__action" href="https://taller.nexusmedi.org/lading/cliente" target="_blank" rel="noopener">Portal del cliente</a>
        <a class="smartdiag-erp__action" href="https://taller.nexusmedi.org/lading" target="_blank" rel="noopener">Landing y tienda</a>
      </div></div><img class="smartdiag-erp__logo" src="/assets/smartdiag_workshop/smartdiag504-logo.png" alt="SmartDiag504"></section>
      <section class="smartdiag-erp__metrics"><article class="smartdiag-erp__metric"><small>OT abiertas</small><strong data-metric="orders">—</strong></article><article class="smartdiag-erp__metric"><small>Facturas pendientes</small><strong data-metric="invoices">—</strong></article><article class="smartdiag-erp__metric"><small>Compras abiertas</small><strong data-metric="purchases">—</strong></article><article class="smartdiag-erp__metric"><small>Empleados activos</small><strong data-metric="employees">—</strong></article></section>
      <section class="smartdiag-erp__system" aria-live="polite"><h2>Salud operativa y contable</h2><p>Lectura directa de eventos, integraciones y asientos guardados en ERPNext.</p><div class="smartdiag-erp__system-grid" data-system-grid><div class="smartdiag-erp__skeleton"></div><div class="smartdiag-erp__skeleton"></div><div class="smartdiag-erp__skeleton"></div><div class="smartdiag-erp__skeleton"></div></div></section>
      <section class="smartdiag-erp__activity" aria-live="polite"><div class="smartdiag-erp__activity-head"><div><h2>Actividad administrativa</h2><p>Documentos reales guardados en ERPNext.</p></div><span>Actualizado al abrir</span></div><div class="smartdiag-erp__activity-grid" data-activity-grid><div class="smartdiag-erp__skeleton"></div><div class="smartdiag-erp__skeleton"></div><div class="smartdiag-erp__skeleton"></div></div></section>
      <section class="smartdiag-erp__grid">${sections.join("")}</section>
      <p class="smartdiag-erp__note"><b>Regla de operación:</b> use SmartDiag504 para atender rápido; use este ERP para configurar maestros, revisar sincronización, contabilizar y cerrar periodos.</p>
    </div>`);
    this.wrapper.on("click", "[data-route-type]", (event) => {
      event.preventDefault();
      const target = $(event.currentTarget);
      const routeType = target.data("route-type");
      frappe.set_route(routeType === "query-report" ? ["query-report", target.data("doctype")] : [routeType, target.data("doctype")]);
    });
  }

  async loadMetrics() {
    const requests = [
      ["orders", "Service Order", { status: ["not in", ["Completed", "Cancelled"]] }],
      ["invoices", "Sales Invoice", { docstatus: 1, outstanding_amount: [">", 0] }],
      ["purchases", "Purchase Order", { docstatus: ["<", 2], status: ["not in", ["Completed", "Closed", "Cancelled"]] }],
      ["employees", "Employee", { status: "Active" }],
    ];
    const results = await Promise.all(requests.map(async ([key, doctype, filters]) => {
      if (!this.readableDoctypes.has(doctype)) return [key, "No disponible"];
      try {
        const rows = await frappe.db.get_list(doctype, { filters, fields: ["name"], limit: 1000 });
        return [key, rows.length];
      } catch (_) { return [key, "No disponible"]; }
    }));
    results.forEach(([key, value]) => this.wrapper.find(`[data-metric="${key}"]`).text(value));
  }

  async loadActivity() {
    const sources = [
      { title: "Facturas recientes", doctype: "Sales Invoice", fields: ["name", "customer_name", "grand_total", "status"], detail: (row) => `${row.customer_name || "Cliente"} · L ${Number(row.grand_total || 0).toLocaleString("es-HN", { minimumFractionDigits: 2 })}`, status: (row) => row.status || "Borrador" },
      { title: "Compras recientes", doctype: "Purchase Order", fields: ["name", "supplier_name", "grand_total", "status"], detail: (row) => `${row.supplier_name || "Proveedor"} · L ${Number(row.grand_total || 0).toLocaleString("es-HN", { minimumFractionDigits: 2 })}`, status: (row) => row.status || "Borrador" },
      { title: "Personal activo", doctype: "Employee", fields: ["name", "employee_name", "designation", "status"], filters: { status: "Active" }, detail: (row) => row.designation || "Cargo por configurar", status: () => "Activo" },
    ].filter((source) => this.readableDoctypes.has(source.doctype));
    const columns = await Promise.all(sources.map(async (source) => {
      try {
        const rows = await frappe.db.get_list(source.doctype, { fields: source.fields, filters: source.filters || {}, order_by: "modified desc", limit: 4 });
        const items = rows.length ? rows.map((row) => `<button type="button" class="smartdiag-erp__activity-row" data-doctype="${source.doctype}" data-name="${row.name}"><span><b>${frappe.utils.escape_html(row.name)}</b><small>${frappe.utils.escape_html(source.detail(row))}</small></span><em>${frappe.utils.escape_html(source.status(row))}</em></button>`).join("") : `<div class="smartdiag-erp__empty"><b>Sin registros todavía</b><span>Use “Nuevo” para crear el primer documento.</span></div>`;
        return `<article><h3>${source.title}</h3>${items}</article>`;
      } catch (_) {
        return `<article><h3>${source.title}</h3><div class="smartdiag-erp__empty"><b>No disponible</b><span>Revise el permiso del rol.</span></div></article>`;
      }
    }));
    this.wrapper.find("[data-activity-grid]").html(columns.join(""));
    this.wrapper.on("click", "[data-name]", (event) => {
      const target = $(event.currentTarget);
      frappe.set_route("Form", target.data("doctype"), target.data("name"));
    });
  }

  async loadSystemStatus() {
    const count = async (doctype, filters = {}) => {
      if (!this.readableDoctypes.has(doctype)) return null;
      try {
        const rows = await frappe.db.get_list(doctype, { filters, fields: ["name"], limit: 1000 });
        return rows.length;
      } catch (_) { return null; }
    };
    const [pendingEvents, failedEvents, integrationErrors, ledgerEntries] = await Promise.all([
      count("SmartDiag Event Outbox", { status: "PENDING" }),
      count("SmartDiag Event Outbox", { status: "FAILED" }),
      count("Integration Request", { status: ["in", ["Failed", "Error"]] }),
      count("GL Entry", { posting_date: frappe.datetime.get_today(), is_cancelled: 0 }),
    ]);
    const cards = [
      ["Flujos pendientes", pendingEvents, pendingEvents === 0 ? "ok" : "warn"],
      ["Flujos con error", failedEvents, failedEvents === 0 ? "ok" : "error"],
      ["Integraciones fallidas", integrationErrors, integrationErrors === 0 ? "ok" : "error"],
      ["Asientos de hoy", ledgerEntries, "ok"],
    ];
    this.wrapper.find("[data-system-grid]").html(cards.map(([label, value, state]) => `<article class="smartdiag-erp__system-item" data-state="${value === null ? "warn" : state}"><small>${__(label)}</small><strong>${value === null ? __("Sin acceso") : value}</strong></article>`).join(""));
  }
}
