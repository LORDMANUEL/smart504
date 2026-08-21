import { request } from 'playwright';

const base = process.env.ERP_BASE_URL || 'https://erp.nexusmedi.org';
const user = process.env.ERP_USER;
const password = process.env.ERP_ADMIN_PASSWORD;
if (!user || !password) throw new Error('ERP_USER y ERP_ADMIN_PASSWORD son obligatorios');

const client = await request.newContext({ baseURL: base });
const login = await client.post('/api/method/login', { form: { usr: user, pwd: password } });
if (!login.ok()) throw new Error(`Inicio ERP rechazado: ${login.status()}`);

async function list(doctype, fields, filters = []) {
  const query = new URLSearchParams({
    fields: JSON.stringify(fields),
    filters: JSON.stringify(filters),
    limit_page_length: '1000',
  });
  const response = await client.get(`/api/resource/${encodeURIComponent(doctype)}?${query}`);
  if (!response.ok()) throw new Error(`${doctype} respondió ${response.status()}`);
  return (await response.json()).data || [];
}

const invoices = await list('Sales Invoice', ['name', 'docstatus', 'grand_total'], [['docstatus', '=', 1]]);
const entries = await list('GL Entry', ['voucher_no', 'debit', 'credit'], [
  ['voucher_type', '=', 'Sales Invoice'],
  ['is_cancelled', '=', 0],
]);
const byVoucher = new Map();
for (const row of entries) {
  const totals = byVoucher.get(row.voucher_no) || { debit: 0, credit: 0, rows: 0 };
  totals.debit += Number(row.debit || 0);
  totals.credit += Number(row.credit || 0);
  totals.rows += 1;
  byVoucher.set(row.voucher_no, totals);
}
const checks = invoices.map((invoice) => {
  const totals = byVoucher.get(invoice.name) || { debit: 0, credit: 0, rows: 0 };
  return {
    invoice: invoice.name,
    rows: totals.rows,
    debit: Number(totals.debit.toFixed(2)),
    credit: Number(totals.credit.toFixed(2)),
    balanced: totals.rows > 0 && Math.abs(totals.debit - totals.credit) < 0.01,
  };
});
const result = {
  ok: invoices.length > 0 && checks.every((item) => item.balanced),
  submittedInvoices: invoices.length,
  ledgerRows: entries.length,
  checks,
};
console.log(JSON.stringify(result, null, 2));
await client.dispose();
if (!result.ok) process.exit(1);
