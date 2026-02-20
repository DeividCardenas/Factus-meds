import asyncpg
import polars as pl

from app.invoicing.domain.entities.invoice import Invoice
from app.invoicing.infrastructure.etl.polars_transformer import INVOICE_COLUMNS


class InvoiceRepositoryAsyncpg:
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self._db_pool = db_pool

    async def save_dataframe(self, df: pl.DataFrame) -> None:
        if df.is_empty():
            return

        records = df.select(INVOICE_COLUMNS).rows()
        async with self._db_pool.acquire() as connection:
            await connection.copy_records_to_table(
                "invoices",
                records=records,
                columns=INVOICE_COLUMNS,
            )

    async def fetch_invoices(self, customer_id: str | None = None) -> list[Invoice]:
        query = (
            "SELECT external_id, customer_id, issued_at, total, currency, tax_amount "
            "FROM invoices"
        )
        params: tuple[str, ...] = ()
        if customer_id:
            query += " WHERE customer_id = $1"
            params = (customer_id,)
        query += " ORDER BY issued_at DESC NULLS LAST"

        async with self._db_pool.acquire() as connection:
            rows = await connection.fetch(query, *params)

        return [
            Invoice(
                external_id=row["external_id"],
                customer_id=row["customer_id"],
                issued_at=row["issued_at"],
                total=row["total"],
                currency=row["currency"],
                tax_amount=row["tax_amount"],
            )
            for row in rows
        ]
