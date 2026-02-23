import { API_BASE_URL } from "@/lib/react-query-client";

export async function fetchInvoices() {
  const res = await fetch(`${API_BASE_URL}/invoices`);
  if (!res.ok) throw new Error("Error al obtener facturas");
  return res.json();
}

export async function fetchInvoiceById(id: string) {
  const res = await fetch(`${API_BASE_URL}/invoices/${id}`);
  if (!res.ok) throw new Error("Error al obtener la factura");
  return res.json();
}
