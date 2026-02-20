from time import perf_counter

import polars as pl


class InvoiceEtlService:
    def transform(self, invoices: list[dict]) -> pl.DataFrame:
        started_at = perf_counter()

        df = pl.DataFrame(invoices)
        for column in ("issued_at", "total", "external_id"):
            if column not in df.columns:
                df = df.with_columns(pl.lit(None).alias(column))

        df = df.with_columns(
            pl.col("issued_at")
            .cast(pl.Utf8, strict=False)
            .str.to_datetime(strict=False, time_zone="UTC"),
            (pl.col("total").cast(pl.Float64, strict=False) * 0.19).alias("tax_amount"),
        ).filter(
            pl.col("external_id").is_not_null() & pl.col("total").is_not_null()
        )

        elapsed_ms = (perf_counter() - started_at) * 1000
        print(df)
        print(
            f"ETL completed: rows_in={len(invoices)} rows_out={df.height} elapsed_ms={elapsed_ms:.2f}"
        )

        return df
