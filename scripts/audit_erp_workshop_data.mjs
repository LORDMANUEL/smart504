import { request } from 'playwright';

const baseURL = process.env.ERP_BASE_URL || 'https://erp.nexusmedi.org';
const user = process.env.ERP_USER || 'Administrator';
const password = process.env.ERP_ADMIN_PASSWORD;
if (!password) throw new Error('ERP_ADMIN_PASSWORD es obligatorio');

const context = await request.newContext({ baseURL });
const login = await context.post('/api/method/login', { form: { usr: user, pwd: password } });
if (!login.ok()) throw new Error(`Inicio ERP rechazado: ${login.status()}`);
const userResponse = await context.get(`/api/resource/User/${encodeURIComponent(user)}`);
const userBody = await userResponse.json().catch(() => ({}));
const profileResponse = userBody.data?.module_profile ? await context.get(`/api/resource/Module%20Profile/${encodeURIComponent(userBody.data.module_profile)}`) : null;
const profileBody = profileResponse ? await profileResponse.json().catch(() => ({})) : {};
const permissionResponse = await context.get('/api/resource/Custom%20DocPerm?fields=%5B%22parent%22,%22role%22,%22read%22,%22select%22,%22create%22,%22write%22%5D&filters=%5B%5B%22parent%22,%22in%22,%5B%22Service%20Order%22,%22Service%20Quotation%22,%22SmartDiag%20Vehicle%22,%22Item%22%5D%5D%5D&limit_page_length=100');
const permissionBody = await permissionResponse.json().catch(() => ({}));

const doctypes = [
  'Service Order', 'Service Quotation', 'SmartDiag Vehicle', 'Vehicle Check In',
  'Workshop Bay', 'Workshop Quality Check', 'Item', 'Customer', 'Supplier',
  'Purchase Order', 'Sales Invoice', 'Payment Entry', 'Employee', 'Attendance', 'Salary Slip',
];
const counts = {};
for (const doctype of doctypes) {
  const response = await context.get(`/api/resource/${encodeURIComponent(doctype)}?fields=%5B%22name%22%5D&limit_page_length=1000`);
  const body = await response.json().catch(() => ({}));
  counts[doctype] = response.ok() ? (body.data || []).length : { status: response.status(), error: body.exception || body.message };
}
console.log(JSON.stringify({ user, roles: (userBody.data?.roles || []).map((row) => row.role), moduleProfile: userBody.data?.module_profile, blockedModules: (profileBody.data?.block_modules || []).map((row) => row.module), permissions: permissionBody.data || [], counts }, null, 2));
await context.dispose();
