from typing import Protocol


class FactusClientPort(Protocol):
    async def authenticate(self, force_refresh: bool = False) -> str: ...

    async def get_active_numbering_range_id(self) -> int: ...
