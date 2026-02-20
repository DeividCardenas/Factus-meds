from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Invoice:
    external_id: str
    customer_id: str | None
    issued_at: datetime | None
    total: Decimal | None
    currency: str | None
    tax_amount: Decimal | None = None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None

    @staticmethod
    def _parse_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except Exception:
            return None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Invoice":
        return cls(
            external_id=str(payload.get("external_id", "")),
            customer_id=payload.get("customer_id"),
            issued_at=cls._parse_datetime(payload.get("issued_at")),
            total=cls._parse_decimal(payload.get("total")),
            currency=payload.get("currency"),
            tax_amount=cls._parse_decimal(payload.get("tax_amount")),
        )
