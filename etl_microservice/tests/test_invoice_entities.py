import unittest

from app.invoicing.application.use_cases.process_invoice_batch import (
    ProcessInvoiceBatchUseCase,
)
from app.invoicing.domain.entities.invoice_batch import InvoiceBatch


class _FakeRepository:
    def __init__(self) -> None:
        self.saved_df = None

    async def save_dataframe(self, df) -> None:
        self.saved_df = df


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
        use_case = ProcessInvoiceBatchUseCase(invoice_repository=repository)
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


if __name__ == "__main__":
    unittest.main()
