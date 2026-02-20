import asyncio
import contextlib
import json
import logging
from typing import Any

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.services.etl_service import InvoiceEtlService

logger = logging.getLogger(__name__)


class InvoiceKafkaConsumer:
    def __init__(self, etl_service: InvoiceEtlService):
        self._etl_service = etl_service
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            enable_auto_commit=True,
        )
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        await self._consumer.start()
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

        await self._consumer.stop()

    async def _consume_loop(self) -> None:
        async for message in self._consumer:
            await self._handle_message(message.value)

    async def _handle_message(self, raw_value: bytes) -> None:
        try:
            data: dict[str, Any] = json.loads(raw_value.decode("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Kafka message is not valid JSON. Skipping message.")
            return

        raw_payload = data.get("payload", [])
        invoices = raw_payload.get("invoices", []) if isinstance(raw_payload, dict) else raw_payload

        if not isinstance(invoices, list):
            logger.warning("Kafka message payload is not a list. Skipping message.")
            return

        await asyncio.to_thread(self._etl_service.transform, invoices)
