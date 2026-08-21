import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    buyers: {
      executor: "shared-iterations",
      vus: Number(__ENV.VUS || 100),
      iterations: Number(__ENV.BUYERS || 1000),
      maxDuration: "10m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1500", "p(99)<3000"],
    checks: ["rate>0.99"],
  },
};

const base = (__ENV.BASE_URL || "https://taller.nexusmedi.org").replace(/\/$/, "");

export default function () {
  const landing = http.get(`${base}/lading`, { tags: { flow: "buyer-landing" } });
  check(landing, { "landing 200": (r) => r.status === 200 });

  const products = http.get(`${base}/api/v1/catalog/products`, { tags: { flow: "buyer-catalog" } });
  check(products, {
    "catalog 200": (r) => r.status === 200,
    "catalog json": (r) => String(r.headers["Content-Type"] || "").includes("application/json"),
  });

  sleep(Math.random() * 1.5);
}
