"use strict";
const DEMO_PRODUCTS = [
    { id: "FLT-001", sku: "FL-910S", name: "Filtro de aceite Motorcraft", description: "Filtro de servicio para aplicaciones Ford seleccionadas.", price: 295, stock: 12, category: "Filtros", compatibility: "REQUIERE_VALIDACION", fitment: "Validar por VIN" },
    { id: "FLT-002", sku: "FA-1883", name: "Filtro de aire de motor", description: "Elemento filtrante de alta capacidad para mantenimiento preventivo.", price: 520, stock: 7, category: "Filtros", compatibility: "PROBABLE", fitment: "Escape 2017–2019" },
    { id: "BRK-001", sku: "BRF-1512", name: "Juego de pastillas delanteras", description: "Compuesto cerámico para frenado estable y bajo ruido.", price: 1860, stock: 4, category: "Frenos", compatibility: "REQUIERE_VALIDACION", fitment: "Confirmar disco y versión" },
    { id: "IGN-001", sku: "SP-550", name: "Bujía iridium", description: "Bujía de encendido de larga duración; precio por unidad.", price: 310, stock: 24, category: "Encendido", compatibility: "PROBABLE", fitment: "Motores EcoBoost seleccionados" },
    { id: "AC-001", sku: "YF-1234", name: "Válvula de servicio A/C", description: "Componente para sistema de aire acondicionado R-134a.", price: 440, stock: 3, category: "Aire acondicionado", compatibility: "REQUIERE_VALIDACION", fitment: "Validar presión y puerto" },
    { id: "SNS-001", sku: "DY-1160", name: "Sensor de temperatura", description: "Sensor electrónico con conector sellado.", price: 1240, stock: 2, category: "Sensores", compatibility: "CONFIRMADA", fitment: "Focus 2012 2.0L" },
    { id: "LUB-001", sku: "XO-5W20-5Q", name: "Aceite sintético 5W-20", description: "Presentación de 5 cuartos para servicio de motor.", price: 1425, stock: 9, category: "Lubricantes", compatibility: "PROBABLE", fitment: "Según especificación del fabricante" },
    { id: "TRN-001", sku: "XT-10-QLVC", name: "Fluido transmisión LV", description: "Fluido de transmisión automática de baja viscosidad, 1 cuarto.", price: 390, stock: 18, category: "Transmisión", compatibility: "REQUIERE_VALIDACION", fitment: "Confirmar caja y especificación" },
];
const state = {
    products: [],
    query: "",
    category: "Todos",
    cart: new Map(),
};
const money = new Intl.NumberFormat("es-HN", { style: "currency", currency: "HNL", minimumFractionDigits: 2 });
function apiBaseUrl() {
    return (window.SMARTDIAG_CONFIG?.apiBaseUrl ?? "").replace(/\/+$/, "");
}
function apiEndpoint(path) {
    return `${apiBaseUrl()}${path}`;
}
function shouldCallApi() {
    return Boolean(apiBaseUrl()) || ["http:", "https:"].includes(window.location.protocol);
}
function normalizeCompatibility(status) {
    if (status === "CONFIRMED")
        return "CONFIRMADA";
    if (status === "PROBABLE")
        return "PROBABLE";
    return "REQUIERE_VALIDACION";
}
function inferCategory(product) {
    if (product.category?.trim())
        return product.category.trim();
    const text = `${product.name} ${product.description} ${product.sku}`.toLocaleLowerCase("es");
    if (text.includes("filtro"))
        return "Filtros";
    if (text.includes("freno") || text.includes("pastilla"))
        return "Frenos";
    if (text.includes("transmis"))
        return "Transmisión";
    if (text.includes("aceite") || text.includes("fluido"))
        return "Lubricantes";
    if (text.includes("aire acondicionado") || text.includes("a/c"))
        return "Aire acondicionado";
    if (text.includes("bujía") || text.includes("encendido"))
        return "Encendido";
    return "Repuestos";
}
function normalizeApiProduct(product) {
    return {
        id: product.slug || product.sku,
        sku: product.sku,
        name: product.name,
        description: product.description,
        price: product.price,
        stock: product.online_available_qty,
        category: inferCategory(product),
        compatibility: normalizeCompatibility(product.compatibility_status),
        fitment: product.fitment.length ? product.fitment.join(" · ") : "Validar por VIN",
    };
}
function byId(id) {
    const element = document.getElementById(id);
    if (!element)
        throw new Error(`Missing element #${id}`);
    return element;
}
function escapeHtml(value) {
    return value.replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character] ?? character));
}
function productGraphic(category) {
    const graphics = {
        Filtros: '<svg viewBox="0 0 220 150" aria-hidden="true"><path d="M75 26h70l14 22v74l-14 14H75l-14-14V48l14-22Z"/><path d="M61 51h98M61 113h98M87 50v64M110 50v64M133 50v64"/></svg>',
        Frenos: '<svg viewBox="0 0 220 150" aria-hidden="true"><circle cx="110" cy="75" r="50"/><circle cx="110" cy="75" r="18"/><path d="M70 40c-23 16-25 53-5 74l24-19V57L70 40Z"/></svg>',
        Encendido: '<svg viewBox="0 0 220 150" aria-hidden="true"><path d="M94 18h32v46l13 20-18 49H99L81 84l13-20V18Z"/><path d="M94 36h32M94 49h32M87 76h46M101 104h18"/></svg>',
        "Aire acondicionado": '<svg viewBox="0 0 220 150" aria-hidden="true"><circle cx="110" cy="75" r="45"/><path d="M110 31v88M66 75h88M79 44l62 62M141 44l-62 62"/><circle cx="110" cy="75" r="12"/></svg>',
        Sensores: '<svg viewBox="0 0 220 150" aria-hidden="true"><path d="M91 24h38v30l18 21v39l-16 15H89l-16-15V75l18-21V24Z"/><path d="M91 40h38M82 83h56M97 101h26"/></svg>',
        Lubricantes: '<svg viewBox="0 0 220 150" aria-hidden="true"><path d="M81 19h58v21l12 12v76H69V52l12-12V19Z"/><path d="M81 40h58M87 69h46v35H87z"/></svg>',
        Transmisión: '<svg viewBox="0 0 220 150" aria-hidden="true"><path d="M78 23h64v20l14 16v68H64V59l14-16V23Z"/><path d="M78 43h64M82 68h56v34H82zM96 114h28"/></svg>',
    };
    return graphics[category] ?? graphics.Sensores;
}
function compatibilityLabel(status) {
    if (status === "CONFIRMADA")
        return { text: "Compatibilidad confirmada", className: "confirmed" };
    if (status === "PROBABLE")
        return { text: "Compatibilidad probable", className: "probable" };
    return { text: "Requiere validación", className: "validate" };
}
function renderCategories() {
    const categories = ["Todos", ...new Set(state.products.map((product) => product.category))];
    byId("category-filter").innerHTML = categories.map((category) => `
    <button type="button" class="category-chip${state.category === category ? " is-active" : ""}" data-category="${escapeHtml(category)}" aria-pressed="${state.category === category}">${escapeHtml(category)}</button>
  `).join("");
}
function filteredProducts() {
    const query = state.query.trim().toLocaleLowerCase("es");
    return state.products.filter((product) => {
        const matchesCategory = state.category === "Todos" || product.category === state.category;
        const haystack = `${product.name} ${product.sku} ${product.description} ${product.fitment}`.toLocaleLowerCase("es");
        return matchesCategory && (!query || haystack.includes(query));
    });
}
function renderProducts() {
    const products = filteredProducts();
    byId("catalog-count").textContent = `${products.length} ${products.length === 1 ? "producto" : "productos"}`;
    byId("catalog-empty").hidden = products.length > 0;
    byId("product-grid").innerHTML = products.map((product) => {
        const compatibility = compatibilityLabel(product.compatibility);
        return `
      <article class="product-card" data-product-card data-product-id="${product.id}">
        <div class="product-visual product-visual--${product.category.toLowerCase().replace(/[^a-záéíóúñ]+/g, "-")}">
          ${productGraphic(product.category)}
          <span>${escapeHtml(product.category)}</span>
        </div>
        <div class="product-body">
          <div class="product-meta"><code>${escapeHtml(product.sku)}</code><span>${product.stock > 0 ? `${product.stock} disponibles` : "Pedido especial"}</span></div>
          <h3>${escapeHtml(product.name)}</h3>
          <p>${escapeHtml(product.description)}</p>
          <div class="compatibility compatibility--${compatibility.className}"><i></i><span><strong>${compatibility.text}</strong><small>${escapeHtml(product.fitment)}</small></span></div>
          <div class="product-footer"><strong>${money.format(product.price)}</strong><button class="sd-button sd-button--dark" type="button" data-add-to-cart="${product.id}">Agregar</button></div>
        </div>
      </article>`;
    }).join("");
}
function cartQuantity() {
    return [...state.cart.values()].reduce((sum, line) => sum + line.quantity, 0);
}
function renderCart() {
    const lines = [...state.cart.values()];
    byId("cart-count").textContent = String(cartQuantity());
    byId("cart-empty").hidden = lines.length > 0;
    byId("cart-items").innerHTML = lines.map(({ product, quantity }) => `
    <div class="cart-line" data-cart-line="${product.id}">
      <div class="cart-line-graphic">${productGraphic(product.category)}</div>
      <div><code>${escapeHtml(product.sku)}</code><strong>${escapeHtml(product.name)}</strong><span>${money.format(product.price)}</span></div>
      <div class="quantity-control" aria-label="Cantidad de ${escapeHtml(product.name)}">
        <button type="button" data-cart-decrease="${product.id}" aria-label="Disminuir">−</button><b>${quantity}</b><button type="button" data-cart-increase="${product.id}" aria-label="Aumentar">+</button>
      </div>
    </div>
  `).join("");
    const subtotal = lines.reduce((sum, line) => sum + line.product.price * line.quantity, 0);
    byId("cart-subtotal").textContent = money.format(subtotal);
    byId("checkout-button").disabled = lines.length === 0;
}
function addToCart(productId) {
    const product = state.products.find((item) => item.id === productId);
    if (!product)
        return;
    const existing = state.cart.get(productId);
    state.cart.set(productId, { product, quantity: existing ? existing.quantity + 1 : 1 });
    renderCart();
    showToast(`${product.name} agregado al carrito`);
}
function changeCartQuantity(productId, change) {
    const line = state.cart.get(productId);
    if (!line)
        return;
    const quantity = line.quantity + change;
    if (quantity <= 0)
        state.cart.delete(productId);
    else
        state.cart.set(productId, { ...line, quantity });
    renderCart();
}
function openCart() {
    const drawer = byId("cart-drawer");
    drawer.setAttribute("aria-hidden", "false");
    drawer.classList.add("is-open");
    byId("drawer-backdrop").hidden = false;
    document.body.classList.add("drawer-open");
}
function closeCart() {
    const drawer = byId("cart-drawer");
    drawer.setAttribute("aria-hidden", "true");
    drawer.classList.remove("is-open");
    byId("drawer-backdrop").hidden = true;
    document.body.classList.remove("drawer-open");
}
let toastTimer = 0;
function showToast(message) {
    const toast = byId("toast");
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => { toast.hidden = true; }, 2600);
}
function navigateTo(target) {
    document.getElementById(target)?.scrollIntoView({ behavior: "smooth", block: "start" });
    const mobileNav = byId("mobile-nav");
    mobileNav.hidden = true;
    byId("mobile-menu-button").setAttribute("aria-expanded", "false");
}
async function loadCatalog() {
    state.products = DEMO_PRODUCTS;
    if (shouldCallApi()) {
        try {
            const response = await fetch(apiEndpoint("/api/v1/catalog/products"), { headers: { Accept: "application/json" } });
            if (response.ok) {
                const payload = await response.json();
                const products = Array.isArray(payload) ? payload : payload.items;
                if (products?.length)
                    state.products = products.map(normalizeApiProduct);
            }
        }
        catch {
            // Demo catalog remains available when the API is not running.
        }
    }
    renderCategories();
    renderProducts();
}
function bookingPayload(form) {
    const data = new FormData(form);
    const vin = String(data.get("vin") ?? "").trim();
    return {
        customer_name: String(data.get("customer_name") ?? "").trim(),
        phone: String(data.get("phone") ?? "").trim(),
        email: String(data.get("email") ?? "").trim() || null,
        service_code: String(data.get("service_code") ?? "").trim(),
        requested_date: String(data.get("requested_date") ?? "").trim(),
        vehicle: {
            make: String(data.get("vehicle_make") ?? "").trim(),
            model: String(data.get("vehicle_model") ?? "").trim(),
            year: Number(data.get("vehicle_year")),
            ...(vin ? { vin } : {}),
        },
        notes: String(data.get("notes") ?? "").trim() || null,
    };
}
async function submitBooking(form) {
    const payload = bookingPayload(form);
    const idempotencyKey = globalThis.crypto?.randomUUID?.() ?? `booking-${Date.now()}`;
    let reference = `SD-${new Date().getFullYear()}-${String(Date.now()).slice(-6)}`;
    if (shouldCallApi()) {
        try {
            const response = await fetch(apiEndpoint("/api/v1/bookings"), {
                method: "POST",
                headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
                body: JSON.stringify(payload),
            });
            if (response.ok) {
                const responsePayload = await response.json();
                reference = responsePayload.booking_id ?? responsePayload.reference ?? responsePayload.id ?? reference;
            }
        }
        catch {
            // Local reference documents the request during preview mode.
        }
    }
    byId("booking-reference").textContent = `Referencia ${reference}. Te contactaremos para confirmar.`;
    byId("booking-success").hidden = false;
    form.reset();
}
function bindEvents() {
    document.addEventListener("click", (event) => {
        const target = event.target;
        const nav = target.closest("[data-nav-target]");
        if (nav?.dataset.navTarget)
            navigateTo(nav.dataset.navTarget);
        const category = target.closest("[data-category]");
        if (category?.dataset.category) {
            state.category = category.dataset.category;
            renderCategories();
            renderProducts();
        }
        const add = target.closest("[data-add-to-cart]");
        if (add?.dataset.addToCart)
            addToCart(add.dataset.addToCart);
        const increase = target.closest("[data-cart-increase]");
        if (increase?.dataset.cartIncrease)
            changeCartQuantity(increase.dataset.cartIncrease, 1);
        const decrease = target.closest("[data-cart-decrease]");
        if (decrease?.dataset.cartDecrease)
            changeCartQuantity(decrease.dataset.cartDecrease, -1);
    });
    byId("parts-search").addEventListener("input", (event) => {
        state.query = event.target.value;
        renderProducts();
    });
    byId("open-cart").addEventListener("click", openCart);
    byId("close-cart").addEventListener("click", closeCart);
    byId("drawer-backdrop").addEventListener("click", closeCart);
    byId("mobile-menu-button").addEventListener("click", () => {
        const button = byId("mobile-menu-button");
        const nav = byId("mobile-nav");
        const expanded = button.getAttribute("aria-expanded") === "true";
        button.setAttribute("aria-expanded", String(!expanded));
        nav.hidden = expanded;
    });
    byId("booking-form").addEventListener("submit", (event) => {
        event.preventDefault();
        void submitBooking(event.currentTarget);
    });
    byId("tracking-form").addEventListener("submit", (event) => {
        event.preventDefault();
        const code = byId("tracking-code").value.trim();
        byId("tracking-result").textContent = code
            ? `Modo demostración: ${code} se consultará en el portal autenticado.`
            : "Escribe una orden, placa o código de seguimiento.";
    });
    byId("checkout-button").addEventListener("click", () => {
        showToast("El checkout se habilita al conectar pagos e inventario ERPNext.");
    });
}
function init() {
    byId("current-year").textContent = String(new Date().getFullYear());
    byId("booking-date").min = new Date().toISOString().slice(0, 10);
    bindEvents();
    renderCart();
    void loadCatalog();
}
init();
