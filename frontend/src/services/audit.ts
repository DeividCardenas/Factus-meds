import { API_BASE_URL } from "@/lib/react-query-client";

export async function fetchAuditEvents() {
  const res = await fetch(`${API_BASE_URL}/audit`);
  if (!res.ok) throw new Error("Error al obtener eventos de auditoría");
  return res.json();
}
