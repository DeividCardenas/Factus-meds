import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

import httpx

from app.invoicing.application.ports.factus_client_port import FactusClientPort
from app.invoicing.application.ports.invoice_repository_port import InvoiceRepositoryPort
from app.invoicing.domain.entities.invoice_batch import InvoiceBatch
from app.invoicing.infrastructure.etl.polars_transformer import transform_invoices

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FactusInvoiceResult:
    external_id: str
    factus_invoice_id: str | None
    qr_url: str | None
    pdf_url: str | None
    status: str
    error: str | None = None


class ProcessInvoiceBatchUseCase:
    _FACTUS_CONCURRENCY_LIMIT = 50

    def __init__(
        self,
        invoice_repository: InvoiceRepositoryPort,
        factus_client: FactusClientPort,
    ) -> None:
        self._invoice_repository = invoice_repository
        self._factus_client = factus_client

    async def execute(self, payload: Mapping[str, Any]) -> str:
        batch = InvoiceBatch.from_message(payload)
        df = await asyncio.to_thread(transform_invoices, batch.invoices, batch.batch_id)
        await self._invoice_repository.save_dataframe(df)
        if df.is_empty():
            return batch.batch_id

        numbering_range_id = await self._factus_client.get_active_numbering_range_id()
        semaphore = asyncio.Semaphore(self._FACTUS_CONCURRENCY_LIMIT)
        results = await asyncio.gather(
            *[
                self._send_invoice_to_factus(
                    invoice_row=invoice_row,
                    numbering_range_id=numbering_range_id,
                    semaphore=semaphore,
                    batch_id=batch.batch_id,
                )
                for invoice_row in df.rows(named=True)
            ]
        )
        logger.info(
            "factus_batch_sync_completed sent=%s success=%s failed=%s",
            len(results),
            sum(result.status == "success" for result in results),
            sum(result.status == "error" for result in results),
            extra={"batch_id": batch.batch_id},
        )
        return batch.batch_id

    async def _send_invoice_to_factus(
        self,
        invoice_row: dict[str, Any],
        numbering_range_id: int,
        semaphore: asyncio.Semaphore,
        batch_id: str,
    ) -> FactusInvoiceResult:
        external_id = str(invoice_row.get("external_id", ""))
        try:
            async with semaphore:
                response = await self._factus_client.create_invoice(
                    self._build_factus_invoice_payload(invoice_row, batch_id),
                    numbering_range_id=numbering_range_id,
                )
            data = response.get("data", response)
            if not isinstance(data, dict):
                data = {}
            return FactusInvoiceResult(
                external_id=external_id,
                factus_invoice_id=(
                    str(data.get("id")) if data.get("id") is not None else None
                ),
                qr_url=data.get("qr"),
                pdf_url=data.get("pdf"),
                status="success",
            )
        except httpx.TimeoutException as exc:
            logger.warning(
                "factus_invoice_timeout external_id=%s",
                external_id,
                extra={"batch_id": batch_id},
            )
            return FactusInvoiceResult(
                external_id=external_id,
                factus_invoice_id=None,
                qr_url=None,
                pdf_url=None,
                status="error",
                error=str(exc),
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "factus_invoice_http_error external_id=%s",
                external_id,
                extra={"batch_id": batch_id},
            )
            return FactusInvoiceResult(
                external_id=external_id,
                factus_invoice_id=None,
                qr_url=None,
                pdf_url=None,
                status="error",
                error=str(exc),
            )

    @staticmethod
    def _build_factus_invoice_payload(
        invoice_row: dict[str, Any], batch_id: str
    ) -> dict[str, Any]:
        external_id = str(invoice_row.get("external_id", ""))
        issued_at = invoice_row.get("issued_at")
        if isinstance(issued_at, datetime):
            issue_date = issued_at.date().isoformat()
        else:
            issue_date = None
        total = invoice_row.get("total")
        price = float(total) if total is not None else 0.0
        return {
            "reference_code": external_id,
            "observation": f"batch:{batch_id}",
            "issue_date": issue_date,
            "customer": {
                "identification": str(invoice_row.get("customer_id") or "UNKNOWN"),
            },
            "items": [
                {
                    "code": external_id or "ITEM-1",
                    "description": f"Invoice {external_id}" if external_id else "Invoice",
                    "quantity": 1,
                    "price": price,
                }
            ],
        }
