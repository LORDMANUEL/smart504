import { chromium } from 'playwright';

const base = process.env.BASE_URL || 'https://taller.nexusmedi.org';
const email = process.env.OPS_E2E_EMAIL || 'demo.admin@smartdiag504.com';
const password = process.env.OPS_E2E_PASSWORD;
if (!password) throw new Error('OPS_E2E_PASSWORD es obligatorio');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
const page = await context.newPage();
const errors = [];
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
page.on('pageerror', (error) => errors.push(error.message));

await page.goto(`${base}/tallerv1/login`, { waitUntil: 'domcontentloaded' });
await page.getByLabel('Correo del empleado').fill(email);
await page.getByLabel('Contraseña').fill(password);
await page.getByRole('button', { name: /Entrar/ }).click();
await page.locator('.ops-shell').waitFor({ state: 'visible' });
// The initial anonymous /me probe is expected before login and is not a runtime error.
errors.length = 0;

const routes = [
  ['/tallerv1/login', 'Kanban'], ['/tallerv1/bahias', 'Bahías'], ['/tallerv1/tecnico', 'Mi trabajo técnico'],
  ['/tallerv1/citas', 'Citas'], ['/tallerv1/pedidos', 'Pedidos web'], ['/tallerv1/catalogo', 'Catálogo'],
  ['/tallerv1/cotizaciones', 'Cotizaciones'], ['/tallerv1/mostrador', 'Mostrador'], ['/tallerv1/caja', 'Caja'],
  ['/tallerv1/bodega', 'Bodega'], ['/tallerv1/compras', 'Compras e importación'], ['/tallerv1/rrhh', 'RR. HH. y nómina'],
  ['/tallerv1/usados', 'Vehículos usados'], ['/tallerv1/procesos', 'Procesos y calidad'], ['/tallerv1/flujos', 'Procesos y calidad'],
  ['/tallerv1/leads', 'Leads CRM'], ['/tallerv1/gerencia', 'Gerencia'], ['/tallerv1/contador', 'Contador'],
  ['/tallerv1/publicida', 'Publicidad'], ['/tallerv1/social', 'Hub Social'], ['/tallerv1/3gj', 'Administración'],
  ['/tallerv1/personal', 'Personal y accesos'], ['/tallerv1/documentos', 'Documentos'], ['/tallerv1/guias', 'Guía interactiva'],
  ['/tallerv1/configuracion', 'Configuración'], ['/tallerv1/sistema', 'Sistema'],
];
const results = [];
for (const [path, expectedActive] of routes) {
  await page.goto(`${base}${path}`, { waitUntil: 'domcontentloaded' });
  await page.locator('.nav-item--active').waitFor({ state: 'visible' });
  const text = await page.locator('body').innerText();
  const overlay = await page.locator('.vite-error-overlay, #webpack-dev-server-client-overlay, [data-nextjs-dialog]').count();
  const active = (await page.locator('.nav-item--active span').first().textContent())?.trim() || '';
  const activeOk = path === '/tallerv1/login' ? ['Kanban', 'Bahías'].includes(active) : active === expectedActive;
  const ok = text.trim().length > 180 && activeOk && overlay === 0;
  results.push({ path, ok, active, expectedActive, characters: text.trim().length, overlay });
}

await page.goto(`${base}/tallerv1/configuracion`, { waitUntil: 'domcontentloaded' });
await page.locator('.branding-preview img').waitFor({ state: 'visible' });
await page.locator('.branding-preview img[src^="/media/"]').waitFor({ state: 'visible' });
const brandingText = await page.locator('main').innerText();
const brandImage = await page.locator('.branding-preview img').getAttribute('src');
results.push({ path: '/tallerv1/configuracion#marca', ok: /Marca de la empresa/i.test(brandingText) && Boolean(brandImage), characters: brandingText.length, brandImage, overlay: 0 });
await page.screenshot({ path: '/evidence/configuracion-marca.png', fullPage: true });

await page.goto(`${base}/tallerv1/compras`, { waitUntil: 'domcontentloaded' });
for (const label of ['Proveedores', 'Órdenes y recepción', 'Importaciones']) {
  await page.getByRole('button', { name: label, exact: true }).click();
  await page.waitForTimeout(150);
  results.push({ path: `/tallerv1/compras#${label}`, ok: (await page.locator('main').innerText()).length > 120, characters: (await page.locator('main').innerText()).length, overlay: 0 });
}

await page.goto(`${base}/tallerv1/rrhh`, { waitUntil: 'domcontentloaded' });
for (const label of ['Expedientes y contratos', 'Marcaciones y horas', 'Permisos y vacaciones', 'Nómina y vouchers', 'Seguro y prestaciones']) {
  await page.getByRole('button', { name: label, exact: true }).click();
  const text = await page.locator('main').innerText();
  results.push({ path: `/tallerv1/rrhh#${label}`, ok: text.length > 140, characters: text.length, overlay: 0 });
}

await page.goto(`${base}/tallerv1/tecnico`, { waitUntil: 'domcontentloaded' });
for (const label of ['Mis órdenes', 'Marcar entrada/salida', 'Mis permisos', 'Mis vouchers']) {
  await page.getByRole('button', { name: label, exact: true }).click();
  const text = await page.locator('main').innerText();
  results.push({ path: `/tallerv1/tecnico#${label}`, ok: text.length > 100, characters: text.length, overlay: 0 });
}

await page.goto(`${base}/tallerv1/documentos`, { waitUntil: 'domcontentloaded' });
await page.locator('.document-center').waitFor({ state: 'visible' });
const documentText = await page.locator('body').innerText();
const payslipOption = await page.locator('option', { hasText: 'PAYSLIP' }).count();
results.push({ path: '/tallerv1/documentos', ok: /Centro único de formatos e impresión/i.test(documentText) && /Subir formato nuevo|Reemplazar formato/i.test(documentText) && /Asistente de impresión/i.test(documentText) && payslipOption > 0, characters: documentText.length, payslipOption, overlay: 0 });

await page.goto(`${base}/tallerv1/guias`, { waitUntil: 'domcontentloaded' });
await page.locator('.guided-hub').waitFor({ state: 'visible' });
const guideText = await page.locator('main').innerText();
results.push({ path: '/tallerv1/guias#menus', ok: /RR\. HH\. y nómina/i.test(guideText) && /Documentos/i.test(guideText) && /Mi trabajo técnico/i.test(guideText), characters: guideText.length, overlay: 0 });

await page.goto(`${base}/tallerv1/publicida/tv`, { waitUntil: 'domcontentloaded' });
const tvText = await page.locator('body').innerText();
results.push({ path: '/tallerv1/publicida/tv', ok: tvText.trim().length > 30, characters: tvText.trim().length, overlay: 0 });
await page.screenshot({ path: '/evidence/publicidad-tv.png', fullPage: true });

for (const path of ['/lading', '/lading/repuestos', '/lading/acceso', '/lading/loginclie']) {
  await page.goto(`${base}${path}`, { waitUntil: 'domcontentloaded' });
  await page.locator('main').waitFor({ state: 'visible' });
  const text = await page.locator('body').innerText();
  const overlay = await page.locator('.vite-error-overlay, #webpack-dev-server-client-overlay, [data-nextjs-dialog]').count();
  results.push({ path, ok: text.trim().length > 180 && overlay === 0, characters: text.trim().length, overlay });
}
await page.goto(`${base}/lading`, { waitUntil: 'domcontentloaded' });
await page.locator('.brand__logo[src^="/media/"]').first().waitFor({ state: 'visible' });
const publicBrandImage = await page.locator('.brand__logo').first().getAttribute('src');
results.push({ path: '/lading#marca', ok: Boolean(publicBrandImage?.startsWith('/media/')), brandImage: publicBrandImage, overlay: 0 });
await page.screenshot({ path: '/evidence/landing-marca.png', fullPage: true });

await browser.close();
console.log(JSON.stringify({ results, consoleErrors: errors }, null, 2));
if (results.some((item) => !item.ok) || errors.length) process.exit(1);
