import asyncio
import unittest

import httpx

from app.invoicing.application.use_cases.process_invoice_batch import (
    ProcessInvoiceBatchUseCase,
)


class _FakeRepository:
    def __init__(self) -> None:
        self.saved_df = None

    async def save_dataframe(self, df) -> None:
        self.saved_df = df


class _AlwaysTimeoutClient:
    def __init__(self) -> None:
        self.call_count = 0

    async def get_active_numbering_range_id(self) -> int:
        return 1

    async def create_invoice(self, invoice_data: dict, numbering_range_id: int) -> dict:
        self.call_count += 1
        raise httpx.TimeoutException("simulated timeout")


class _TransientTimeoutClient:
    """Fails with timeout on the first `fail_attempts` calls, then succeeds."""

    def __init__(self, fail_attempts: int) -> None:
        self.fail_attempts = fail_attempts
        self.call_count = 0

    async def get_active_numbering_range_id(self) -> int:
        return 1

    async def create_invoice(self, invoice_data: dict, numbering_range_id: int) -> dict:
        self.call_count += 1
        if self.call_count <= self.fail_attempts:
            raise httpx.TimeoutException("transient timeout")
        return {"data": {"id": 42, "qr": "qr-url", "pdf": "pdf-url"}}


_BATCH_PAYLOAD = {
    "batch_id": "retry-batch",
    "payload": {
        "invoices": [
            {
                "external_id": "INV-R1",
                "customer_id": "CUST-R",
                "issued_at": "2026-02-20T00:00:00Z",
                "total": 100,
                "currency": "COP",
            }
        ]
    },
}


class TestRetryMechanism(unittest.IsolatedAsyncioTestCase):
    async def test_exhausted_retries_result_in_error_status(self) -> None:
        repository = _FakeRepository()
        client = _AlwaysTimeoutClient()
        use_case = ProcessInvoiceBatchUseCase(
            invoice_repository=repository,
            factus_client=client,
            retry_base_delay_seconds=0.0,
        )

        batch_id = await use_case.execute(_BATCH_PAYLOAD)

        self.assertEqual(batch_id, "retry-batch")
        self.assertIsNotNone(repository.saved_df)
        row = repository.saved_df.to_dicts()[0]
        self.assertEqual(row["status"], "error")
        # 1 initial attempt + 3 retries = 4 total calls
        self.assertEqual(client.call_count, ProcessInvoiceBatchUseCase._FACTUS_MAX_RETRIES + 1)

    async def test_transient_failure_succeeds_after_retry(self) -> None:
        repository = _FakeRepository()
        # Fail once then succeed (1 failure < max 3 retries)
        client = _TransientTimeoutClient(fail_attempts=1)
        use_case = ProcessInvoiceBatchUseCase(
            invoice_repository=repository,
            factus_client=client,
            retry_base_delay_seconds=0.0,
        )

        batch_id = await use_case.execute(_BATCH_PAYLOAD)

        self.assertEqual(batch_id, "retry-batch")
        self.assertIsNotNone(repository.saved_df)
        row = repository.saved_df.to_dicts()[0]
        self.assertEqual(row["status"], "success")
        self.assertEqual(row["factus_invoice_id"], "42")
        # 1 failure + 1 success = 2 total calls
        self.assertEqual(client.call_count, 2)

    async def test_event_publisher_receives_invoice_after_save(self) -> None:
        published: list[dict] = []

        class _FakePublisher:
            async def publish_invoice_processed(self, invoice_data: dict) -> None:
                published.append(invoice_data)

        repository = _FakeRepository()
        client = _TransientTimeoutClient(fail_attempts=0)
        use_case = ProcessInvoiceBatchUseCase(
            invoice_repository=repository,
            factus_client=client,
            event_publisher=_FakePublisher(),
            retry_base_delay_seconds=0.0,
        )

        await use_case.execute(_BATCH_PAYLOAD)

        self.assertEqual(len(published), 1)
        self.assertEqual(published[0]["external_id"], "INV-R1")
        self.assertEqual(published[0]["status"], "success")


if __name__ == "__main__":
    unittest.main()
