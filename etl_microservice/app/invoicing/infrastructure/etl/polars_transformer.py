import logging
from time import perf_counter

import polars as pl

from app.invoicing.domain.entities.invoice import Invoice

TAX_RATE = 0.19
INVOICE_COLUMNS = [
    "external_id",
    "customer_id",
    "issued_at",
    "total",
    "currency",
    "tax_amount",
    "factus_invoice_id",
    "qr_url",
    "pdf_url",
    "status",
    "error_message",
]
logger = logging.getLogger(__name__)


def transform_invoices(invoices: tuple[Invoice, ...], batch_id: str = "unknown") -> pl.DataFrame:
    started_at = perf_counter()
    rows = [
        {
            "external_id": invoice.external_id,
            "customer_id": invoice.customer_id,
            "issued_at": invoice.issued_at,
            "total": float(invoice.total) if invoice.total is not None else None,
            "currency": invoice.currency,
        }
        for invoice in invoices
    ]

    df = pl.DataFrame(rows)
    for column in ("external_id", "customer_id", "issued_at", "total", "currency"):
        if column not in df.columns:
            df = df.with_columns(pl.lit(None).alias(column))

    total_column = pl.col("total").cast(pl.Float64, strict=False)
    df = df.with_columns(
        pl.col("issued_at").cast(pl.Datetime(time_zone="UTC"), strict=False),
        total_column.alias("total"),
        (total_column * TAX_RATE).alias("tax_amount"),
    ).filter(pl.col("external_id").is_not_null() & pl.col("total").is_not_null())

    elapsed_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "etl_transform_completed rows_in=%s rows_out=%s elapsed_ms=%.2f",
        len(invoices),
        df.height,
        elapsed_ms,
        extra={"batch_id": batch_id},
    )
    return df
