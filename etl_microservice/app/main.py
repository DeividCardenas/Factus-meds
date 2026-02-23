from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from typing import Any, AsyncIterator

import asyncpg  # type: ignore[import-untyped]
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiokafka import AIOKafkaInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator
import strawberry
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.invoicing.application.ports.invoice_event_publisher_port import InvoiceEventPublisherPort
from app.invoicing.application.use_cases.process_invoice_batch import (
    ProcessInvoiceBatchUseCase,
)
from app.invoicing.infrastructure.persistence.postgres.invoice_repository_asyncpg import (
    InvoiceRepositoryAsyncpg,
)
from app.invoicing.infrastructure.api.factus.factus_async_client import FactusAsyncClient
from app.kafka.consumer import InvoiceKafkaConsumer
from app.shared.infrastructure.logging.structured_logger import configure_json_logging
from app.shared.infrastructure.pubsub.broadcaster import InvoiceEventBroadcaster


@strawberry.type
class InvoiceType:
    external_id: str
    customer_id: str | None
    issued_at: datetime | None
    total: Decimal | None
    currency: str | None
    tax_amount: Decimal | None
    factus_invoice_id: str | None
    qr_url: str | None
    pdf_url: str | None
    status: str | None
    error_message: str | None


@strawberry.type
class Query:
    @strawberry.field
    async def invoices(
        self,
        info: strawberry.Info,
        customer_id: str | None = None,
    ) -> list[InvoiceType]:
        repository = info.context["request"].app.state.invoice_repository
        invoices = await repository.fetch_invoices(customer_id=customer_id)

        return [
            InvoiceType(
                external_id=invoice.external_id,
                customer_id=invoice.customer_id,
                issued_at=invoice.issued_at,
                total=invoice.total,
                currency=invoice.currency,
                tax_amount=invoice.tax_amount,
                factus_invoice_id=invoice.factus_invoice_id,
                qr_url=invoice.qr_url,
                pdf_url=invoice.pdf_url,
                status=invoice.status,
                error_message=invoice.error_message,
            )
            for invoice in invoices
        ]


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def invoice_processed(
        self,
        info: strawberry.Info,
    ) -> AsyncGenerator[InvoiceType, None]:
        context_obj = info.context.get("ws") or info.context.get("request")
        broadcaster: InvoiceEventBroadcaster = context_obj.app.state.invoice_broadcaster
        async for event in broadcaster.subscribe():
            yield _invoice_dict_to_type(event)


def _invoice_dict_to_type(event: dict[str, Any]) -> InvoiceType:
    total = event.get("total")
    tax_amount = event.get("tax_amount")
    return InvoiceType(
        external_id=str(event.get("external_id") or ""),
        customer_id=event.get("customer_id"),
        issued_at=event.get("issued_at"),
        total=Decimal(str(total)) if total is not None else None,
        currency=event.get("currency"),
        tax_amount=Decimal(str(tax_amount)) if tax_amount is not None else None,
        factus_invoice_id=event.get("factus_invoice_id"),
        qr_url=event.get("qr_url"),
        pdf_url=event.get("pdf_url"),
        status=event.get("status"),
        error_message=event.get("error_message"),
    )


class _BroadcasterEventPublisher:
    def __init__(self, broadcaster: InvoiceEventBroadcaster) -> None:
        self._broadcaster = broadcaster

    async def publish_invoice_processed(self, invoice_data: dict[str, Any]) -> None:
        await self._broadcaster.publish(invoice_data)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_json_logging()
    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: settings.otel_service_name})
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otel_exporter_endpoint,
                insecure=True,
            )
        )
    )
    trace.set_tracer_provider(tracer_provider)
    aiokafka_instrumentor = AIOKafkaInstrumentor()
    asyncpg_instrumentor = AsyncPGInstrumentor()
    aiokafka_instrumentor.instrument()
    asyncpg_instrumentor.instrument()
    app.state.db_pool = await asyncpg.create_pool(settings.database_url)
    missing_factus_settings = [
        name
        for name, value in (
            ("FACTUS_EMAIL", settings.factus_email),
            ("FACTUS_PASSWORD", settings.factus_password),
            ("FACTUS_CLIENT_ID", settings.factus_client_id),
            ("FACTUS_CLIENT_SECRET", settings.factus_client_secret),
        )
        if not value
    ]
    if missing_factus_settings:
        raise RuntimeError(
            "Missing required Factus environment variables: "
            + ", ".join(missing_factus_settings)
        )
    factus_client = FactusAsyncClient(
        base_url=settings.factus_base_url,
        email=settings.factus_email,
        password=settings.factus_password,
        client_id=settings.factus_client_id,
        client_secret=settings.factus_client_secret,
    )
    invoice_repository = InvoiceRepositoryAsyncpg(db_pool=app.state.db_pool)
    broadcaster = InvoiceEventBroadcaster()
    event_publisher = _BroadcasterEventPublisher(broadcaster)
    process_invoice_batch_use_case = ProcessInvoiceBatchUseCase(
        invoice_repository=invoice_repository,
        factus_client=factus_client,
        event_publisher=event_publisher,
    )
    consumer = InvoiceKafkaConsumer(
        process_invoice_batch_use_case=process_invoice_batch_use_case
    )
    app.state.factus_client = factus_client
    app.state.invoice_repository = invoice_repository
    app.state.invoice_broadcaster = broadcaster
    await consumer.start()
    app.state.consumer = consumer

    try:
        yield
    finally:
        await consumer.stop()
        await factus_client.close()
        await app.state.db_pool.close()
        asyncpg_instrumentor.uninstrument()
        aiokafka_instrumentor.uninstrument()
        await tracer_provider.shutdown()


app = FastAPI(title="Invoice ETL Microservice", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
schema = strawberry.Schema(query=Query, subscription=Subscription)
app.include_router(GraphQLRouter(schema), prefix="/graphql")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
