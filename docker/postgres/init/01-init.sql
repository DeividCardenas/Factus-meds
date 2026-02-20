DROP TABLE IF EXISTS invoices CASCADE;

CREATE TABLE invoices (
    external_id TEXT,
    customer_id TEXT,
    issued_at TIMESTAMPTZ NOT NULL,
    total NUMERIC(18, 2),
    currency TEXT,
    tax_amount NUMERIC(18, 2),
    factus_invoice_id TEXT,
    qr_url TEXT,
    pdf_url TEXT,
    status TEXT,
    error_message TEXT,
    PRIMARY KEY (external_id, issued_at)
) PARTITION BY RANGE (issued_at);

DO $$
DECLARE
    start_month DATE := date_trunc('month', CURRENT_DATE)::date;
    partition_start DATE;
    partition_end DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..2 LOOP
        partition_start := (start_month + make_interval(months => i))::date;
        partition_end := (start_month + make_interval(months => i + 1))::date;
        partition_name := format('invoices_%s', to_char(partition_start, 'YYYY_MM'));

        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF invoices FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_start,
            partition_end
        );
    END LOOP;
END
$$;

CREATE TABLE IF NOT EXISTS invoices_default PARTITION OF invoices DEFAULT;

CREATE INDEX IF NOT EXISTS idx_invoices_customer_issued_at ON invoices (customer_id, issued_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_issued_at_brin ON invoices USING BRIN (issued_at);
