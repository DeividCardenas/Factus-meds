CREATE TABLE IF NOT EXISTS invoices (
    external_id TEXT PRIMARY KEY,
    customer_id TEXT,
    issued_at TIMESTAMPTZ,
    total NUMERIC(18, 2),
    currency TEXT,
    tax_amount NUMERIC(18, 2),
    factus_invoice_id TEXT,
    qr_url TEXT,
    pdf_url TEXT,
    status TEXT,
    error_message TEXT
);
