import asyncio
from typing import Any, Mapping

from app.invoicing.application.ports.invoice_repository_port import InvoiceRepositoryPort
from app.invoicing.domain.entities.invoice_batch import InvoiceBatch
from app.invoicing.infrastructure.etl.polars_transformer import transform_invoices


class ProcessInvoiceBatchUseCase:
    def __init__(self, invoice_repository: InvoiceRepositoryPort) -> None:
        self._invoice_repository = invoice_repository

    async def execute(self, payload: Mapping[str, Any]) -> str:
        batch = InvoiceBatch.from_message(payload)
        df = await asyncio.to_thread(transform_invoices, batch.invoices, batch.batch_id)
        await self._invoice_repository.save_dataframe(df)
        return batch.batch_id
