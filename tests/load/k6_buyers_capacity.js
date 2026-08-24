import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

const base = __ENV.BASE_URL || 'https://taller.169.58.217.146.sslip.io';
const api = __ENV.API_URL || 'https://api.169.58.217.146.sslip.io';
const maxVus = Number(__ENV.MAX_VUS || '100');

// Ten thousand is an explicit opt-in capacity run. Normal smoke executions stay bounded.
export const options = {
  scenarios: {
    buyers: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: __ENV.RAMP_UP || '2m', target: maxVus },
        { duration: __ENV.HOLD || '3m', target: maxVus },
        { duration: __ENV.RAMP_DOWN || '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1200', 'p(99)<2500'],
    checks: ['rate>0.99'],
  },
  noConnectionReuse: false,
  userAgent: 'SmartDiag504-Authorized-Capacity-Test/1.0',
};

export default function () {
  const landing = http.get(`${base}/lading`, { tags: { flow: 'landing' } });
  check(landing, { 'landing 200': (response) => response.status === 200 });

  const catalog = http.get(`${api}/api/v1/catalog/products?limit=24`, { tags: { flow: 'catalog' } });
  check(catalog, {
    'catalog available': (response) => response.status === 200,
    'catalog is json': (response) => String(response.headers['Content-Type'] || '').includes('application/json'),
  });

  // Deterministic browsing variation without creating financial or inventory records.
  if (exec.scenario.iterationInTest % 3 === 0) {
    const branding = http.get(`${api}/api/v1/branding`, { tags: { flow: 'branding' } });
    check(branding, { 'branding 200': (response) => response.status === 200 });
  }
  sleep(Math.random() * 2 + 0.5);
}
