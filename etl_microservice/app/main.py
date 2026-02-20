from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal

import asyncpg
from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.kafka.consumer import InvoiceKafkaConsumer
from app.services.etl_service import InvoiceEtlService


@strawberry.type
class InvoiceType:
    external_id: str
    customer_id: str | None
    issued_at: datetime | None
    total: Decimal | None
    currency: str | None
    tax_amount: Decimal | None


@strawberry.type
class Query:
    @strawberry.field
    async def invoices(
        self,
        info: strawberry.Info,
        customer_id: str | None = None,
    ) -> list[InvoiceType]:
        query = (
            "SELECT external_id, customer_id, issued_at, total, currency, tax_amount "
            "FROM invoices"
        )
        params = ()
        if customer_id:
            query += " WHERE customer_id = $1"
            params = (customer_id,)
        query += " ORDER BY issued_at DESC NULLS LAST"

        async with info.context["request"].app.state.db_pool.acquire() as connection:
            rows = await connection.fetch(query, *params)

        return [
            InvoiceType(
                external_id=row["external_id"],
                customer_id=row["customer_id"],
                issued_at=row["issued_at"],
                total=row["total"],
                currency=row["currency"],
                tax_amount=row["tax_amount"],
            )
            for row in rows
        ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(settings.database_url)
    etl_service = InvoiceEtlService(db_pool=app.state.db_pool)
    consumer = InvoiceKafkaConsumer(etl_service=etl_service)
    await consumer.start()
    app.state.consumer = consumer

    try:
        yield
    finally:
        await consumer.stop()
        await app.state.db_pool.close()


app = FastAPI(title="Invoice ETL Microservice", lifespan=lifespan)
schema = strawberry.Schema(query=Query)
app.include_router(GraphQLRouter(schema), prefix="/graphql")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
