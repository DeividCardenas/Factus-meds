import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 100 },
    { duration: "1m", target: 100 },
    { duration: "1m", target: 0 },
  ],
};

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function buildInvoice(iteration, index) {
  const externalSuffix = `${__VU}-${iteration}-${index}`;
  return {
    external_id: `INV-${externalSuffix}`,
    customer_id: `CUST-${randomInt(1, 5000)}`,
    issued_at: new Date().toISOString(),
    total: randomInt(10000, 900000),
    currency: "COP",
  };
}

export default function () {
  const invoiceCount = randomInt(50, 500);
  const invoices = Array.from({ length: invoiceCount }, (_, index) =>
    buildInvoice(__ITER, index),
  );

  const payload = JSON.stringify({
    source: "json",
    invoices,
  });

  const response = http.post(
    "http://laravel:8080/api/v1/invoice-batches",
    payload,
    {
      headers: {
        "Content-Type": "application/json",
        "X-Ingest-Key": "local-dev-ingest-key",
      },
      timeout: "120s",
    },
  );

  check(response, {
    "status is 202": (r) => r.status === 202,
  });

  sleep(1);
}
