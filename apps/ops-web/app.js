"use strict";
const orders = [
    { id: "OT-2026-0184", customer: "Carlos Mejía", vehicle: "Ford Escape 2018", plate: "HAD 4821", advisor: "Andrea P.", technician: "Miguel Santos", status: "APROBADO", promised: "Hoy · 3:30 p. m.", total: 18640, priority: "ALTA", reason: "Luz de motor y pérdida de potencia" },
    { id: "OT-2026-0181", customer: "Marta López", vehicle: "Ford Explorer 2020", plate: "HBF 9024", advisor: "Luis F.", technician: "Kevin Cruz", status: "EN TRABAJO", promised: "Hoy · 5:00 p. m.", total: 9280, priority: "NORMAL", reason: "Mantenimiento 60,000 km" },
    { id: "OT-2026-0187", customer: "Ricardo Paz", vehicle: "Ford Ranger 2019", plate: "PDE 1132", advisor: "Andrea P.", technician: "Sin asignar", status: "DIAGNOSTICO", promised: "Mañana · 11:00 a. m.", total: 1200, priority: "CRÍTICA", reason: "No arranca después de lluvia" },
    { id: "OT-2026-0179", customer: "Sofía Aguilar", vehicle: "Ford Focus 2016", plate: "HCC 7750", advisor: "José R.", technician: "David Flores", status: "ESPERANDO APROBACIÓN", promised: "Hoy · 1:00 p. m.", total: 7850, priority: "ALTA", reason: "A/C enfría de forma intermitente" },
    { id: "OT-2026-0176", customer: "Empresa Ruta Norte", vehicle: "Ford Transit 2021", plate: "HAP 3009", advisor: "Luis F.", technician: "Óscar Díaz", status: "CONTROL CALIDAD", promised: "Hoy · 4:00 p. m.", total: 22650, priority: "NORMAL", reason: "Frenos delanteros y servicio" },
    { id: "OT-2026-0189", customer: "Daniela Núñez", vehicle: "Ford EcoSport 2017", plate: "HDD 6318", advisor: "José R.", technician: "Sin asignar", status: "RECIBIDO", promised: "Mañana · 2:00 p. m.", total: 0, priority: "NORMAL", reason: "Ruido al girar a la izquierda" },
    { id: "OT-2026-0172", customer: "Mario Zelaya", vehicle: "Ford F-150 2018", plate: "HAW 9187", advisor: "Andrea P.", technician: "Samuel Pineda", status: "LISTO ENTREGA", promised: "Hoy · 11:30 a. m.", total: 31240, priority: "NORMAL", reason: "Servicio transmisión y fuga" },
];
const bays = [
    { id: "B-01", label: "Bahía 01", state: "En reparación", order: "OT-2026-0181", vehicle: "Explorer 2020", technician: "Kevin Cruz", progress: 62 },
    { id: "B-02", label: "Bahía 02", state: "Esperando repuesto", order: "OT-2026-0179", vehicle: "Focus 2016", technician: "David Flores", progress: 28 },
    { id: "B-03", label: "Bahía 03", state: "Diagnóstico", order: "OT-2026-0187", vehicle: "Ranger 2019", technician: "Miguel Santos", progress: 40 },
    { id: "B-04", label: "Bahía 04", state: "Control de calidad", order: "OT-2026-0176", vehicle: "Transit 2021", technician: "Óscar Díaz", progress: 92 },
    { id: "B-05", label: "Bahía 05", state: "Libre" },
    { id: "B-06", label: "Bahía 06", state: "En reparación", order: "OT-2026-0184", vehicle: "Escape 2018", technician: "Samuel Pineda", progress: 15 },
    { id: "B-07", label: "Bahía 07", state: "Libre" },
    { id: "B-08", label: "Bahía 08", state: "Fuera de servicio" },
];
const partRequests = [
    { id: "SR-0418", order: "OT-2026-0181", technician: "Kevin Cruz", items: "Filtro aceite · Aceite 5W-20 · Arandela", age: "hace 8 min", state: "Preparando" },
    { id: "SR-0417", order: "OT-2026-0179", technician: "David Flores", items: "Válvula servicio A/C · O-rings", age: "hace 34 min", state: "Faltante" },
    { id: "SR-0416", order: "OT-2026-0176", technician: "Óscar Díaz", items: "Pastillas delanteras · Limpiador frenos", age: "hace 52 min", state: "Entregada" },
    { id: "SR-0415", order: "OT-2026-0184", technician: "Miguel Santos", items: "Bujía SP-550 ×4 · Bobina", age: "hace 1 h 18 min", state: "Nueva" },
];
const alerts = [
    { id: "A-901", severity: "critical", title: "Promesa de entrega en riesgo", detail: "OT-2026-0179 continúa esperando aprobación y vence hoy a la 1:00 p. m.", age: "hace 4 min", entity: "OT-2026-0179" },
    { id: "A-902", severity: "warning", title: "Repuesto pendiente", detail: "La solicitud SR-0417 tiene una línea faltante y bloquea la bahía 02.", age: "hace 12 min", entity: "SR-0417" },
    { id: "A-903", severity: "warning", title: "Técnico sin trabajo asignado", detail: "Jorge Ramos está disponible desde hace 1 h 06 min.", age: "hace 18 min", entity: "EMP-0024" },
    { id: "A-904", severity: "info", title: "Control de calidad listo", detail: "OT-2026-0176 completó todos los puntos obligatorios.", age: "hace 22 min", entity: "OT-2026-0176" },
];
const state = { activeView: "dashboard" };
const currency = new Intl.NumberFormat("es-HN", { style: "currency", currency: "HNL", minimumFractionDigits: 0 });
function byId(id) {
    const element = document.getElementById(id);
    if (!element)
        throw new Error(`Missing element #${id}`);
    return element;
}
function escapeHtml(value) {
    return value.replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character] ?? character));
}
function statusClass(value) {
    return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-");
}
function renderPageHeader(title, subtitle, actions = "") {
    return `<div class="page-head"><div><p>${subtitle}</p><h1>${title}</h1></div><div class="page-actions">${actions}</div></div>`;
}
function metricCard(label, value, detail, tone, dataMetric) {
    return `<article class="metric metric--${tone}"><div class="metric-top"><span>${label}</span><i></i></div><strong${dataMetric ? ` data-metric="${dataMetric}"` : ""}>${value}</strong><small>${detail}</small></article>`;
}
function orderCard(order, compact = false) {
    return `<article class="order-card${compact ? " order-card--compact" : ""}" data-order-id="${order.id}">
    <div class="order-top"><code>${order.id}</code><span class="priority priority--${order.priority.toLowerCase()}">${order.priority}</span></div>
    <div class="order-vehicle"><strong>${escapeHtml(order.vehicle)}</strong><span>${escapeHtml(order.plate)} · ${escapeHtml(order.customer)}</span></div>
    <p>${escapeHtml(order.reason)}</p>
    <div class="order-tags"><span class="order-status status-${statusClass(order.status)}">${order.status}</span><span>${escapeHtml(order.promised)}</span></div>
    <div class="order-owner"><div class="avatar">${order.technician === "Sin asignar" ? "—" : order.technician.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div><span><small>Técnico</small><strong>${escapeHtml(order.technician)}</strong></span><b>${currency.format(order.total)}</b></div>
    ${compact ? "" : `<button class="order-advance" type="button" data-action="advance">Avanzar OT <svg viewBox="0 0 20 20"><path d="m7 4 6 6-6 6"/></svg></button>`}
  </article>`;
}
function renderDashboard() {
    const currentWork = orders.filter((order) => ["DIAGNOSTICO", "EN TRABAJO", "CONTROL CALIDAD"].includes(order.status));
    return `${renderPageHeader("Operación de hoy", "Miércoles · 12 de agosto de 2026", '<button class="sd-button sd-button--secondary" type="button" data-view-target="orders">Ver todas las OT</button><button class="sd-button sd-button--dark" type="button" data-action="new-order">Nueva orden</button>')}
    <section class="metric-grid" aria-label="Indicadores del día">
      ${metricCard("Órdenes abiertas", "18", "+3 desde ayer", "blue", "open-orders")}
      ${metricCard("En trabajo", "6", "4 bahías activas", "cyan")}
      ${metricCard("Esperando aprobación", "4", "L 31,480 por autorizar", "amber")}
      ${metricCard("Listas para entregar", "3", "2 con saldo pendiente", "green")}
    </section>
    <div class="dashboard-grid">
      <section class="dashboard-block active-work"><div class="block-head"><div><h2>Trabajo activo</h2><p>Órdenes en diagnóstico, reparación o calidad.</p></div><button type="button" data-view-target="orders">Abrir Kanban</button></div><div class="active-order-list">${currentWork.map((order) => orderCard(order, true)).join("")}</div></section>
      <aside class="dashboard-block alerts-preview"><div class="block-head"><div><h2>Requiere atención</h2><p>Prioridad calculada por reglas operativas.</p></div><button type="button" data-view-target="alerts">Ver todas</button></div><div class="alert-list">${alerts.slice(0, 3).map(alertRow).join("")}</div></aside>
    </div>
    <section class="dashboard-block bay-overview"><div class="block-head"><div><h2>Estado del taller</h2><p>Ocupación y avance por bahía.</p></div><button type="button" data-view-target="workshop">Vista completa</button></div><div class="mini-bay-grid">${bays.map((bay) => miniBay(bay)).join("")}</div></section>`;
}
function alertRow(alert) {
    return `<article class="alert-row alert-row--${alert.severity}" data-alert-id="${alert.id}"><i></i><div><strong>${escapeHtml(alert.title)}</strong><p>${escapeHtml(alert.detail)}</p><span>${alert.age} · ${alert.entity}</span></div><button type="button" aria-label="Abrir ${alert.entity}">→</button></article>`;
}
function miniBay(bay) {
    return `<article class="mini-bay mini-bay--${statusClass(bay.state)}"><div><span>${bay.id}</span><i></i></div><strong>${escapeHtml(bay.state)}</strong><small>${bay.vehicle ? `${escapeHtml(bay.vehicle)} · ${bay.order}` : "Disponible"}</small></article>`;
}
const boardColumns = ["RECIBIDO", "DIAGNOSTICO", "ESPERANDO APROBACIÓN", "APROBADO", "PROGRAMADO", "EN TRABAJO", "CONTROL CALIDAD", "LISTO ENTREGA"];
function renderOrders() {
    return `${renderPageHeader("Órdenes de trabajo", "Kanban operacional", '<label class="view-search"><span class="sd-visually-hidden">Buscar OT</span><input id="order-search" placeholder="Buscar OT, placa o cliente"></label><button class="sd-button sd-button--dark" type="button" data-action="new-order">Nueva orden</button>')}
    <div class="board-toolbar"><div><button class="is-active" type="button">Kanban</button><button type="button">Tabla</button></div><span>${orders.length} órdenes visibles</span></div>
    <section class="kanban-board" id="kanban-board" aria-label="Órdenes por estado">
      ${boardColumns.map((column) => {
        const columnOrders = orders.filter((order) => order.status === column);
        return `<div class="kanban-column" data-column="${column}"><header><span>${column}</span><b>${columnOrders.length}</b></header><div class="kanban-cards">${columnOrders.map((order) => orderCard(order)).join("") || '<div class="empty-column">Sin órdenes</div>'}</div></div>`;
    }).join("")}
    </section>`;
}
function bayCard(bay) {
    const occupied = Boolean(bay.order);
    return `<article class="bay-card bay-card--${statusClass(bay.state)}" data-bay-id="${bay.id}">
    <header><div><span>${bay.label}</span><strong>${escapeHtml(bay.state)}</strong></div><i></i></header>
    <div class="bay-visual"><svg viewBox="0 0 260 115" aria-hidden="true"><path d="M36 74c8-20 20-32 39-39 28-11 78-15 126-9 25 3 42 13 55 28l-4 35H23l1-6c1-5 5-9 12-9Z"/><path d="M80 35l28 39M174 27l-16 47M108 35c24-7 54-9 81-5 15 2 29 7 40 16l-59 3-62-14Z"/><circle cx="79" cy="84" r="20"/><circle cx="205" cy="84" r="20"/></svg>${occupied ? "" : '<span class="bay-free-label">Bahía disponible</span>'}</div>
    <div class="bay-info">${occupied ? `<div><code>${bay.order}</code><strong>${escapeHtml(bay.vehicle ?? "")}</strong></div><div><small>Técnico</small><span>${escapeHtml(bay.technician ?? "")}</span></div><div class="bay-progress"><span style="width:${bay.progress ?? 0}%"></span></div>` : '<p>Lista para asignar vehículo y técnico.</p>'}</div>
  </article>`;
}
function renderWorkshop() {
    const occupied = bays.filter((bay) => bay.order).length;
    return `${renderPageHeader("Vista de taller", "Bahías y capacidad", '<button class="sd-button sd-button--secondary" type="button">Configurar bahías</button><button class="sd-button sd-button--dark" type="button">Asignar vehículo</button>')}
    <div class="workshop-summary"><span><strong>${occupied}</strong> ocupadas</span><span><strong>${bays.filter((bay) => bay.state === "Libre").length}</strong> libres</span><span><strong>1</strong> fuera de servicio</span><span><strong>75%</strong> utilización</span></div>
    <section class="bay-grid" aria-label="Bahías del taller">${bays.map(bayCard).join("")}</section>`;
}
function partRequestRow(request) {
    return `<article class="part-request" data-part-request data-request-id="${request.id}"><div class="request-id"><code>${request.id}</code><span>${request.age}</span></div><div><strong>${request.order}</strong><span>${escapeHtml(request.technician)}</span></div><p>${escapeHtml(request.items)}</p><span class="request-state request-state--${statusClass(request.state)}">${request.state}</span><button type="button">Abrir</button></article>`;
}
function renderParts() {
    return `${renderPageHeader("Repuestos y bodega", "Solicitudes del taller", '<button class="sd-button sd-button--secondary" type="button">Inventario</button><button class="sd-button sd-button--dark" type="button">Nueva solicitud</button>')}
    <section class="parts-command"><div class="parts-stats"><article><span>Pendientes</span><strong>2</strong><small>1 bloquea una bahía</small></article><article><span>Preparando</span><strong>1</strong><small>Tiempo promedio 14 min</small></article><article><span>Entregadas hoy</span><strong>23</strong><small>98% confirmadas</small></article><article><span>Pedidos especiales</span><strong>4</strong><small>L 18,920 comprometidos</small></article></div>
    <div class="request-table"><div class="request-table-head"><span>Solicitud</span><span>OT / técnico</span><span>Artículos</span><span>Estado</span><span></span></div>${partRequests.map(partRequestRow).join("")}</div></section>`;
}
function renderAlerts() {
    return `${renderPageHeader("Centro de alertas", "Reglas y seguimiento", '<button class="sd-button sd-button--secondary" type="button">Silencios</button><button class="sd-button sd-button--dark" type="button">Configurar reglas</button>')}
    <div class="alert-layout"><section class="all-alerts"><div class="alert-filter"><button class="is-active" type="button">Abiertas <b>4</b></button><button type="button">Reconocidas</button><button type="button">Resueltas hoy</button></div>${alerts.map(alertRow).join("")}</section><aside class="alert-policy"><h2>Política activa</h2><dl><div><dt>OT con promesa en riesgo</dt><dd>30 min antes</dd></div><div><dt>Cotización sin respuesta</dt><dd>48 horas</dd></div><div><dt>Solicitud de repuesto</dt><dd>2 horas</dd></div><div><dt>Técnico disponible</dt><dd>60 min</dd></div></dl><p>Las alertas informan; no modifican documentos ERP ni cierran órdenes automáticamente.</p></aside></div>`;
}
function renderCash() {
    const rows = [
        ["Efectivo", "L 28,450", "L 28,450", "L 0"],
        ["Tarjeta", "L 64,780", "L 64,780", "L 0"],
        ["Transferencia", "L 41,200", "L 40,700", "L -500"],
        ["Crédito autorizado", "L 18,900", "L 18,900", "L 0"],
    ];
    return `${renderPageHeader("Caja del día", "Sesión CAJA-SPS-20260812", '<button class="sd-button sd-button--secondary" type="button">Movimientos</button><button class="sd-button sd-button--dark" type="button">Preparar cierre</button>')}
    <section class="cash-hero"><div><span>Ventas registradas</span><strong>L 153,330</strong><small>17 facturas · 4 anticipos</small></div><div><span>Esperado en caja</span><strong>L 134,430</strong><small>Excluye crédito autorizado</small></div><div class="cash-difference"><span>Diferencia provisional</span><strong>L -500</strong><small>Revisar transferencia TRX-8841</small></div></section>
    <div class="cash-layout"><section class="cash-table dashboard-block"><div class="block-head"><div><h2>Conciliación por método</h2><p>Los valores definitivos provienen de ERPNext.</p></div></div><div class="sd-table-wrap"><table class="sd-table"><thead><tr><th>Método</th><th>Sistema</th><th>Contado</th><th>Diferencia</th></tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell, index) => `<td${index === 3 && cell !== "L 0" ? ' class="negative"' : ""}>${cell}</td>`).join("")}</tr>`).join("")}</tbody></table></div></section><aside class="closing-checklist dashboard-block"><h2>Antes de cerrar</h2><label><input type="checkbox" checked> Facturas revisadas</label><label><input type="checkbox" checked> Anticipos aplicados</label><label><input type="checkbox"> Transferencia TRX-8841 conciliada</label><label><input type="checkbox"> Efectivo contado por segunda persona</label><button class="sd-button sd-button--dark" type="button" disabled>Cerrar caja</button><small>El botón se habilita cuando no existen diferencias sin justificar.</small></aside></div>`;
}
function renderActiveView() {
    const root = byId("view-root");
    const renderers = { dashboard: renderDashboard, orders: renderOrders, workshop: renderWorkshop, parts: renderParts, alerts: renderAlerts, cash: renderCash };
    root.innerHTML = renderers[state.activeView]();
    document.querySelectorAll("[data-view-target]").forEach((button) => {
        const active = button.dataset.viewTarget === state.activeView;
        if (button.closest(".ops-nav"))
            button.setAttribute("aria-current", active ? "page" : "false");
    });
    root.querySelector("h1")?.focus?.();
}
const nextStatus = {
    RECIBIDO: "DIAGNOSTICO",
    DIAGNOSTICO: "ESPERANDO APROBACIÓN",
    "ESPERANDO APROBACIÓN": "APROBADO",
    APROBADO: "PROGRAMADO",
    PROGRAMADO: "EN TRABAJO",
    "EN TRABAJO": "CONTROL CALIDAD",
    "CONTROL CALIDAD": "LISTO ENTREGA",
};
let toastTimer = 0;
function showToast(message) {
    const toast = byId("ops-toast");
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => { toast.hidden = true; }, 2400);
}
function switchView(view) {
    state.activeView = view;
    renderActiveView();
    closeSidebar();
    byId("ops-main").scrollTop = 0;
}
function advanceOrder(orderId) {
    const order = orders.find((item) => item.id === orderId);
    if (!order)
        return;
    const target = nextStatus[order.status];
    if (!target) {
        showToast(`${order.id} no tiene una transición demo disponible.`);
        return;
    }
    const previous = order.status;
    order.status = target;
    renderActiveView();
    showToast(`${order.id}: ${previous} → ${target}`);
}
function openSidebar() {
    byId("ops-sidebar").classList.add("is-open");
    byId("sidebar-scrim").hidden = false;
    byId("menu-trigger").setAttribute("aria-expanded", "true");
}
function closeSidebar() {
    byId("ops-sidebar").classList.remove("is-open");
    byId("sidebar-scrim").hidden = true;
    byId("menu-trigger").setAttribute("aria-expanded", "false");
}
function bindEvents() {
    document.addEventListener("click", (event) => {
        const target = event.target;
        const viewButton = target.closest("[data-view-target]");
        if (viewButton?.dataset.viewTarget)
            switchView(viewButton.dataset.viewTarget);
        const actionButton = target.closest("[data-action]");
        if (actionButton?.dataset.action === "advance") {
            const card = actionButton.closest("[data-order-id]");
            if (card?.dataset.orderId)
                advanceOrder(card.dataset.orderId);
        }
        if (actionButton?.dataset.action === "new-order")
            showToast("La creación completa se conecta al Service Order de Beveren.");
    });
    byId("menu-trigger").addEventListener("click", () => {
        if (byId("ops-sidebar").classList.contains("is-open"))
            closeSidebar();
        else
            openSidebar();
    });
    byId("sidebar-scrim").addEventListener("click", closeSidebar);
}
function setDate() {
    const formatter = new Intl.DateTimeFormat("es-HN", { weekday: "short", day: "numeric", month: "short" });
    byId("topbar-date").textContent = formatter.format(new Date());
}
function init() {
    setDate();
    bindEvents();
    renderActiveView();
    if ("serviceWorker" in navigator && ["http:", "https:"].includes(window.location.protocol)) {
        navigator.serviceWorker.register("./service-worker.js").catch(() => undefined);
    }
}
init();
