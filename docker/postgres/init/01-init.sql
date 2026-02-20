CREATE TABLE IF NOT EXISTS invoices (
    external_id TEXT PRIMARY KEY,
    customer_id TEXT,
    issued_at TIMESTAMPTZ,
    total NUMERIC(18, 2),
    currency TEXT,
    tax_amount NUMERIC(18, 2)
);
