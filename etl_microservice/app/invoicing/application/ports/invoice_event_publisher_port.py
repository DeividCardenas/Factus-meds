from typing import Any, Protocol


class InvoiceEventPublisherPort(Protocol):
    async def publish_invoice_processed(self, invoice_data: dict[str, Any]) -> None: ...
