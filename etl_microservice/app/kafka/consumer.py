import asyncio
import contextlib
import json
import logging
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.core.config import settings
from app.invoicing.application.use_cases.process_invoice_batch import (
    ProcessInvoiceBatchUseCase,
)

logger = logging.getLogger(__name__)


class InvoiceKafkaConsumer:
    def __init__(self, process_invoice_batch_use_case: ProcessInvoiceBatchUseCase):
        self._process_invoice_batch_use_case = process_invoice_batch_use_case
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            enable_auto_commit=True,
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
        )
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        await self._consumer.start()
        await self._producer.start()
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        await self._consumer.stop()
        await self._producer.stop()

    async def _consume_loop(self) -> None:
        async for message in self._consumer:
            await self._handle_message(message)

    async def _handle_message(self, message: Any) -> None:
        batch_id = "unknown"
        try:
            data: dict[str, Any] = json.loads(message.value.decode("utf-8"))
            batch_id = str(data.get("batch_id") or "unknown")
            await self._process_invoice_batch_use_case.execute(data)
            logger.info("invoice_batch_processed", extra={"batch_id": batch_id})
        except Exception as exc:
            await self._send_to_dlq(message=message, batch_id=batch_id, error=exc)
            logger.exception("invoice_batch_failed_and_sent_to_dlq", extra={"batch_id": batch_id})

    async def _send_to_dlq(self, message: Any, batch_id: str, error: Exception) -> None:
        dlq_payload = {
            "batch_id": batch_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "metadata": {
                "topic": message.topic,
                "partition": message.partition,
                "offset": message.offset,
                "timestamp": message.timestamp,
            },
            "raw_value": message.value.decode("utf-8", errors="replace"),
        }
        await self._producer.send_and_wait(
            settings.kafka_dlq_topic,
            json.dumps(dlq_payload).encode("utf-8"),
        )
