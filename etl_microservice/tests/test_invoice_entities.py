import unittest

import httpx

from app.invoicing.application.use_cases.process_invoice_batch import (
    ProcessInvoiceBatchUseCase,
)
from app.invoicing.domain.entities.invoice_batch import InvoiceBatch


class _FakeRepository:
    def __init__(self) -> None:
        self.saved_df = None

    async def save_dataframe(self, df) -> None:
        self.saved_df = df


class _FakeFactusClient:
    def __init__(self, fail_external_id: str | None = None) -> None:
        self.fail_external_id = fail_external_id
        self.created_payloads: list[dict] = []
        self.numbering_range_calls = 0

    async def get_active_numbering_range_id(self) -> int:
        self.numbering_range_calls += 1
        return 99

    async def create_invoice(self, invoice_data: dict, numbering_range_id: int) -> dict:
        self.created_payloads.append(
            {"invoice_data": invoice_data, "numbering_range_id": numbering_range_id}
        )
        if invoice_data.get("reference_code") == self.fail_external_id:
            raise httpx.TimeoutException("timeout")
        return {"data": {"id": 1001, "qr": "qr", "pdf": "pdf"}}


class TestInvoiceEntities(unittest.TestCase):
    def test_invoice_batch_from_message_parses_invoices(self) -> None:
        payload = {
            "batch_id": "batch-1",
            "payload": {
                "invoices": [
                    {
                        "external_id": "INV-1",
                        "customer_id": "CUST-1",
                        "issued_at": "2026-02-20T00:00:00Z",
                        "total": 100,
                        "currency": "COP",
                    }
                ]
            },
        }

        batch = InvoiceBatch.from_message(payload)
        self.assertEqual(batch.batch_id, "batch-1")
        self.assertEqual(len(batch.invoices), 1)
        self.assertEqual(batch.invoices[0].external_id, "INV-1")

    def test_invoice_batch_from_message_rejects_non_list_payload(self) -> None:
        payload = {"payload": {"invoices": "invalid"}}
        with self.assertRaises(ValueError):
            InvoiceBatch.from_message(payload)

    def test_process_invoice_batch_use_case_transforms_and_persists(self) -> None:
        import asyncio

        repository = _FakeRepository()
        factus_client = _FakeFactusClient()
        use_case = ProcessInvoiceBatchUseCase(
            invoice_repository=repository, factus_client=factus_client
        )
        payload = {
            "batch_id": "batch-2",
            "payload": {
                "invoices": [
                    {
                        "external_id": "INV-2",
                        "customer_id": "CUST-2",
                        "issued_at": "2026-02-20T00:00:00Z",
                        "total": 200,
                        "currency": "COP",
                    }
                ]
            },
        }

        batch_id = asyncio.run(use_case.execute(payload))
        self.assertEqual(batch_id, "batch-2")
        self.assertIsNotNone(repository.saved_df)
        self.assertEqual(repository.saved_df.height, 1)
        saved_row = repository.saved_df.to_dicts()[0]
        self.assertEqual(saved_row["factus_invoice_id"], "1001")
        self.assertEqual(saved_row["qr_url"], "qr")
        self.assertEqual(saved_row["pdf_url"], "pdf")
        self.assertEqual(saved_row["status"], "success")
        self.assertIsNone(saved_row["error_message"])
        self.assertEqual(factus_client.numbering_range_calls, 1)
        self.assertEqual(len(factus_client.created_payloads), 1)
        self.assertEqual(
            factus_client.created_payloads[0]["numbering_range_id"],
            99,
        )

    def test_process_invoice_batch_use_case_survives_factus_timeout(self) -> None:
        import asyncio

        repository = _FakeRepository()
        factus_client = _FakeFactusClient(fail_external_id="INV-timeout")
        use_case = ProcessInvoiceBatchUseCase(
            invoice_repository=repository,
            factus_client=factus_client,
            retry_base_delay_seconds=0.0,
        )
        payload = {
            "batch_id": "batch-timeout",
            "payload": {
                "invoices": [
                    {
                        "external_id": "INV-timeout",
                        "customer_id": "CUST-3",
                        "issued_at": "2026-02-20T00:00:00Z",
                        "total": 300,
                        "currency": "COP",
                    }
                ]
            },
        }

        batch_id = asyncio.run(use_case.execute(payload))
        self.assertEqual(batch_id, "batch-timeout")
        self.assertIsNotNone(repository.saved_df)
        self.assertEqual(repository.saved_df.height, 1)
        saved_row = repository.saved_df.to_dicts()[0]
        self.assertEqual(saved_row["status"], "error")
        self.assertEqual(saved_row["error_message"], "timeout")
        self.assertIsNone(saved_row["factus_invoice_id"])


if __name__ == "__main__":
    unittest.main()
