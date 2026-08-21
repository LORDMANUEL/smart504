import fs from 'node:fs';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const baseURL = process.env.QA_BASE_URL || 'https://taller.nexusmedi.org';
const password = process.env.QA_STAFF_PASSWORD;
const users = JSON.parse(process.env.QA_ROLE_USERS || '{}');
const output = process.env.QA_AXE_OUTPUT || '/workspace/artifacts/visual-qa/axe-authenticated.json';
if (!password || !Object.keys(users).length) throw new Error('QA_STAFF_PASSWORD y QA_ROLE_USERS son obligatorios');

const publicCases = [
  ['/lading', 'landing'],
  ['/lading/repuestos', 'tienda'],
  ['/tallerv1/login', 'login'],
];
const viewports = [
  { name: 'mobile-360', width: 360, height: 800 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1366', width: 1366, height: 900 },
  { name: 'wide-1920', width: 1920, height: 1080 },
];
const findings = [];

async function audit(page, label, viewport, role = 'PUBLIC') {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  findings.push({ label, role, viewport: viewport.name, url: page.url(), violations: result.violations });
}

const browser = await chromium.launch({ headless: true });
try {
  for (const viewport of viewports) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    for (const [path, label] of publicCases) {
      await page.goto(`${baseURL}${path}`, { waitUntil: 'networkidle' });
      await audit(page, label, viewport);
    }
    await context.close();
  }

  for (const [role, email] of Object.entries(users)) {
    for (const viewport of [viewports[0], viewports[2]]) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();
      await page.goto(`${baseURL}/tallerv1/login`, { waitUntil: 'networkidle' });
      await page.getByLabel(/correo/i).fill(email);
      await page.getByLabel(/contrase/i).fill(password);
      await page.getByRole('button', { name: /^entrar$/i }).click();
      await page.waitForSelector('.ops-shell', { timeout: 20_000 });
      const dismiss = page.getByRole('button', { name: /omitir recorrido/i });
      if (await dismiss.count()) await dismiss.click();
      await page.waitForLoadState('networkidle');
      await audit(page, 'inicio-autenticado', viewport, role);

      const nav = page.locator('nav[aria-label="Módulos de operación"] button');
      const count = await nav.count();
      for (let index = 0; index < count; index += 1) {
        if (viewport.width < 980) {
          const openMenu = page.getByRole('button', { name: /abrir menú/i });
          if (await openMenu.isVisible()) await openMenu.click();
        }
        const button = nav.nth(index);
        const label = (await button.innerText()).trim().replace(/\s+/g, '-').toLowerCase();
        await button.click();
        await page.waitForTimeout(250);
        await audit(page, label, viewport, role);
      }
      await context.close();
    }
  }
} finally {
  await browser.close();
}

fs.mkdirSync(new URL('.', `file://${output}`).pathname, { recursive: true });
fs.writeFileSync(output, JSON.stringify({ generated_at: new Date().toISOString(), baseURL, findings }, null, 2));
const totals = findings.reduce((acc, item) => {
  acc.pages += 1;
  acc.violations += item.violations.length;
  acc.serious += item.violations.filter((v) => ['serious', 'critical'].includes(v.impact)).length;
  return acc;
}, { pages: 0, violations: 0, serious: 0 });
console.log(JSON.stringify(totals));
process.exitCode = totals.serious ? 2 : 0;
