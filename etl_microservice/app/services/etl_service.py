import asyncio
from time import perf_counter

import asyncpg
import polars as pl

from app.core.config import settings

TAX_RATE = 0.19


class InvoiceEtlService:
    INVOICE_COLUMNS = [
        "external_id",
        "customer_id",
        "issued_at",
        "total",
        "currency",
        "tax_amount",
    ]

    def __init__(self, db_pool: asyncpg.Pool | None = None) -> None:
        self._database_url = settings.database_url
        self._db_pool = db_pool

    def transform(self, invoices: list[dict]) -> pl.DataFrame:
        started_at = perf_counter()

        df = pl.DataFrame(invoices)
        for column in (
            "external_id",
            "customer_id",
            "issued_at",
            "total",
            "currency",
        ):
            if column not in df.columns:
                df = df.with_columns(pl.lit(None).alias(column))

        total_column = pl.col("total").cast(pl.Float64, strict=False)
        df = df.with_columns(
            pl.col("issued_at")
            .cast(pl.Utf8, strict=False)
            .str.to_datetime(strict=False, time_zone="UTC"),
            total_column.alias("total"),
            (total_column * TAX_RATE).alias("tax_amount"),
        ).filter(
            pl.col("external_id").is_not_null() & pl.col("total").is_not_null()
        )

        elapsed_ms = (perf_counter() - started_at) * 1000
        print(df)
        print(
            f"ETL completed: rows_in={len(invoices)} rows_out={df.height} elapsed_ms={elapsed_ms:.2f}"
        )

        return df

    async def persist(self, df: pl.DataFrame) -> None:
        if df.is_empty():
            return

        records = df.select(self.INVOICE_COLUMNS).rows()

        if self._db_pool is not None:
            async with self._db_pool.acquire() as connection:
                await connection.copy_records_to_table(
                    "invoices",
                    records=records,
                    columns=self.INVOICE_COLUMNS,
                )
            return

        connection = await asyncpg.connect(self._database_url)
        try:
            await connection.copy_records_to_table(
                "invoices",
                records=records,
                columns=self.INVOICE_COLUMNS,
            )
        finally:
            await connection.close()

    async def transform_and_persist(self, invoices: list[dict]) -> None:
        df = await asyncio.to_thread(self.transform, invoices)
        await self.persist(df)
