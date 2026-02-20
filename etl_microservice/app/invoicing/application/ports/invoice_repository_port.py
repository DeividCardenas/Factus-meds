from typing import Protocol

import polars as pl

from app.invoicing.domain.entities.invoice import Invoice


class InvoiceRepositoryPort(Protocol):
    async def save_dataframe(self, df: pl.DataFrame) -> None: ...

    async def fetch_invoices(self, customer_id: str | None = None) -> list[Invoice]: ...
