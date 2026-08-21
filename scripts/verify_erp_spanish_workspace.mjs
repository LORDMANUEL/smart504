import { chromium } from 'playwright';

const base = process.env.ERP_BASE_URL || 'https://erp.nexusmedi.org';
const user = process.env.ERP_USER || 'Administrator';
const password = process.env.ERP_ADMIN_PASSWORD;
if (!password) throw new Error('ERP_ADMIN_PASSWORD es obligatorio');

const browser = await chromium.launch({ headless: true });
const errors = [];
const results = [];

async function verifyViewport(name, viewport) {
  const context = await browser.newContext({ viewport, locale: 'es-HN' });
  const page = await context.newPage();
  page.on('console', (message) => { if (message.type() === 'error') errors.push(`${name}:${message.text()}`); });
  page.on('pageerror', (error) => errors.push(`${name}:${error.message}`));
  const login = await context.request.post(`${base}/api/method/login`, { form: { usr: user, pwd: password } });
  if (!login.ok()) throw new Error(`Inicio ERP rechazado: ${login.status()}`);

  await page.goto(`${base}/app/smartdiag-workshop`, { waitUntil: 'domcontentloaded' });
  try {
    await page.locator('.smartdiag-erp').waitFor({ state: 'visible', timeout: 30000 });
  } catch (error) {
    console.log(JSON.stringify({ diagnostic: { viewport: name, url: page.url(), title: await page.title(), body: (await page.locator('body').innerText()).slice(0, 1200), errors } }, null, 2));
    await page.screenshot({ path: `/evidence/erp-smartdiag-${name}-failed.png`, fullPage: true });
    throw error;
  }
  await page.waitForFunction(() => document.querySelector('.smartdiag-erp__logo')?.naturalWidth > 0);
  const text = await page.locator('.smartdiag-erp').innerText();
  const expectedLinks = [
    'https://taller.nexusmedi.org/tallerv1/login',
    'https://taller.nexusmedi.org/tallerv1/tecnico',
    'https://taller.nexusmedi.org/lading/cliente',
    'https://taller.nexusmedi.org/lading',
  ];
  const hrefs = await page.locator('.smartdiag-erp__actions a').evaluateAll((links) => links.map((item) => item.href));
  const noHorizontalOverflow = await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
  await page.locator('[data-activity-grid] article').first().waitFor({ state: 'visible' });
  const activityColumns = await page.locator('[data-activity-grid] article').count();
  const activityRows = await page.locator('[data-activity-grid] [data-name]').count();
  const systemCards = await page.locator('[data-system-grid] article').count();
  const sidebarText = await page.locator('body').innerText();
  const ok = /Centro administrativo SmartDiag504/.test(text)
    && /Taller y servicio/.test(text)
    && /Ventas, caja y clientes/.test(text)
    && /Repuestos, compras y bodega/.test(text)
    && /Personal y nómina/.test(text)
    && /Redes, correo y automatización/.test(text)
    && /Logs, flujos y contabilidad/.test(text)
    && expectedLinks.every((href) => hrefs.includes(href))
    && activityColumns === 3
    && activityRows > 0
    && systemCards === 4
    && !/Connected App|OAuth Provider|Google Settings/.test(sidebarText)
    && noHorizontalOverflow;
  results.push({ viewport: name, ok, externalLinks: hrefs.length, activityColumns, activityRows, systemCards, technicalModulesHidden: !/Connected App|OAuth Provider|Google Settings/.test(sidebarText), noHorizontalOverflow, characters: text.length });
  await page.screenshot({ path: `/evidence/erp-smartdiag-${name}.png`, fullPage: true });

  if (name === 'desktop') {
    const links = await page.locator('[data-route-type]').evaluateAll((items) => items.map((link) => ({
      label: link.textContent.trim(),
      doctype: link.dataset.doctype,
      routeType: link.dataset.routeType,
    })));
    const failures = [];
    for (const link of links) {
      await page.goto(`${base}/app/smartdiag-workshop`, { waitUntil: 'domcontentloaded' });
      await page.locator('.smartdiag-erp').waitFor({ state: 'visible' });
      await page.locator(`[data-route-type="${link.routeType}"][data-doctype="${link.doctype}"]`).click();
      await page.waitForTimeout(900);
      const dialogs = await page.locator('.modal-dialog:visible').allInnerTexts();
      const failure = dialogs.find((value) => /Permission Error|Insufficient Permission|Not found|no encontrado/i.test(value));
      if (failure) failures.push({ label: link.label, message: failure.slice(0, 250) });
    }
    await page.goto(`${base}/app/smartdiag-workshop`, { waitUntil: 'domcontentloaded' });
    await page.locator('.smartdiag-erp').waitFor({ state: 'visible' });
    await page.locator('[data-route-type="List"][data-doctype="Service Order"]').click();
    const returnButton = page.locator('.smartdiag-global-home');
    await returnButton.waitFor({ state: 'visible' });
    await returnButton.click();
    await page.locator('.smartdiag-erp').waitFor({ state: 'visible' });
    const returnedHome = /\/(app|desk)\/smartdiag-workshop/.test(page.url());
    results.push({ viewport: `${name}-visible-links`, ok: failures.length === 0 && returnedHome, tested: links.length, returnButton: returnedHome, failures });
  }

  const [settings, workspace, customPage, logo] = await Promise.all([
    context.request.get(`${base}/api/resource/System%20Settings/System%20Settings`),
    context.request.get(`${base}/api/resource/Workspace/SmartDiag504`),
    context.request.get(`${base}/api/resource/Page/smartdiag-workshop`),
    context.request.get(`${base}/assets/smartdiag_workshop/smartdiag504-logo.png`),
  ]);
  const settingsBody = await settings.json();
  const settingsData = settingsBody.message ?? settingsBody.data ?? {};
  results.push({
    viewport: `${name}-configuration`,
    ok: settings.ok() && workspace.ok() && customPage.ok() && logo.ok()
      && settingsData.language === 'es'
      && settingsData.time_zone === 'America/Tegucigalpa'
      && settingsData.country === 'Honduras',
    settingsStatus: settings.status(),
    language: settingsData.language,
    timeZone: settingsData.time_zone,
    country: settingsData.country,
    workspaceStatus: workspace.status(),
    pageStatus: customPage.status(),
    logoStatus: logo.status(),
  });
  await context.close();
}

await verifyViewport('desktop', { width: 1440, height: 1000 });
await verifyViewport('mobile', { width: 390, height: 844 });
await browser.close();

console.log(JSON.stringify({ results, consoleErrors: errors }, null, 2));
if (results.some((item) => !item.ok) || errors.length) process.exit(1);
