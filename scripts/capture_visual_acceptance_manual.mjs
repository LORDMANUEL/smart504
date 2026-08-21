import { chromium } from 'playwright';

const base = process.env.ERP_BASE_URL || 'https://erp.nexusmedi.org';
const user = process.env.ERP_USER;
const password = process.env.ERP_ADMIN_PASSWORD;
if (!user || !password) throw new Error('ERP_USER y ERP_ADMIN_PASSWORD son obligatorios');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'es-HN' });
const page = await context.newPage();
const errors = [];
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
page.on('pageerror', (error) => errors.push(error.message));

await page.goto(`${base}/login`, { waitUntil: 'domcontentloaded' });
await page.screenshot({ path: '/evidence/manual-01-login.png', fullPage: false });

const login = await context.request.post(`${base}/api/method/login`, { form: { usr: user, pwd: password } });
if (!login.ok()) throw new Error(`Inicio ERP rechazado: ${login.status()}`);

const pages = [
  ['02-centro-smartdiag', '/app/smartdiag-workshop', '.smartdiag-erp'],
  ['03-ordenes-servicio', '/app/service-order', '.smartdiag-global-home'],
  ['04-conexion-social', '/app/social-login-key', '.smartdiag-global-home'],
  ['05-flujos-smartdiag', '/app/smartdiag-event-outbox', '.smartdiag-global-home'],
  ['06-asientos-contables', '/app/gl-entry', '.smartdiag-global-home'],
];
for (const [name, path, selector] of pages) {
  await page.goto(`${base}${path}`, { waitUntil: 'domcontentloaded' });
  await page.locator(selector).waitFor({ state: 'visible', timeout: 30000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `/evidence/manual-${name}.png`, fullPage: false });
}

console.log(JSON.stringify({ ok: errors.length === 0, screenshots: pages.length + 1, errors }, null, 2));
await browser.close();
if (errors.length) process.exit(1);
