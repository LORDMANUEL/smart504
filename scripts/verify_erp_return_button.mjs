import { chromium } from 'playwright';

const base = process.env.ERP_BASE_URL || 'https://erp.nexusmedi.org';
const user = process.env.ERP_USER;
const password = process.env.ERP_ADMIN_PASSWORD;
if (!user || !password) throw new Error('ERP_USER y ERP_ADMIN_PASSWORD son obligatorios');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, locale: 'es-HN' });
const page = await context.newPage();
const consoleErrors = [];
page.on('console', (message) => { if (message.type() === 'error') consoleErrors.push(message.text()); });
page.on('pageerror', (error) => consoleErrors.push(error.message));

const login = await context.request.post(`${base}/api/method/login`, { form: { usr: user, pwd: password } });
if (!login.ok()) throw new Error(`Inicio ERP rechazado: ${login.status()}`);
await page.goto(`${base}/app/smartdiag-workshop`, { waitUntil: 'domcontentloaded' });
await page.locator('.smartdiag-erp').waitFor({ state: 'visible' });
await page.locator('[data-route-type="List"][data-doctype="Service Order"]').click();
const button = page.locator('.smartdiag-global-home');
await button.waitFor({ state: 'visible', timeout: 15000 });
const label = (await button.innerText()).trim();
await button.click();
await page.locator('.smartdiag-erp').waitFor({ state: 'visible', timeout: 15000 });
const result = { ok: /Volver a SmartDiag504/.test(label) && /\/(app|desk)\/smartdiag-workshop/.test(page.url()) && consoleErrors.length === 0, label, finalUrl: page.url(), consoleErrors };
console.log(JSON.stringify(result, null, 2));
await page.screenshot({ path: '/evidence/erp-smartdiag-return-button.png', fullPage: true });
await browser.close();
if (!result.ok) process.exit(1);
