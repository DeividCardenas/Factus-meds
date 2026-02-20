from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from app.invoicing.domain.entities.invoice import Invoice


@dataclass(frozen=True, slots=True)
class InvoiceBatch:
    batch_id: str
    invoices: tuple[Invoice, ...]

    @classmethod
    def from_message(cls, message: Mapping[str, Any]) -> "InvoiceBatch":
        batch_id = str(message.get("batch_id") or uuid4())
        payload = message.get("payload", [])
        invoices_data: Any = payload.get("invoices", []) if isinstance(payload, dict) else payload

        if not isinstance(invoices_data, list):
            raise ValueError("Kafka message payload must contain a list of invoices")
        if not all(isinstance(invoice, dict) for invoice in invoices_data):
            raise ValueError("Each invoice payload must be a dictionary")

        invoices = tuple(Invoice.from_dict(invoice) for invoice in invoices_data)
        return cls(batch_id=batch_id, invoices=invoices)
