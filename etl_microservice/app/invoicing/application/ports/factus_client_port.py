from typing import Any, Protocol


class FactusClientPort(Protocol):
    async def authenticate(self, force_refresh: bool = False) -> str: ...

    async def get_active_numbering_range_id(self) -> int: ...

    async def create_invoice(
        self, invoice_data: dict[str, Any], numbering_range_id: int
    ) -> dict[str, Any]: ...
