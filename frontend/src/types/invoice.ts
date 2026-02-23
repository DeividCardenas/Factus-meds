export type InvoiceStatus = "SUCCESS" | "SENT" | "PENDING" | "FAILED" | "ERROR";

export interface Invoice {
  external_id: string;
  customer_id: string;
  issued_at: string;
  total: number;
  tax_amount: number;
  status: InvoiceStatus;
  factus_invoice_id: string;
  qr_url: string | null;
  error_message: string | null;
}
