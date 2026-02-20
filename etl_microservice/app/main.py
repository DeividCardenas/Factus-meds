from contextlib import asynccontextmanager
from datetime import datetime
import os

import asyncpg
from fastapi import FastAPI
import strawberry
from strawberry.fastapi import GraphQLRouter

from app.kafka.consumer import InvoiceKafkaConsumer
from app.services.etl_service import InvoiceEtlService


@strawberry.type
class InvoiceType:
    external_id: str
    customer_id: str | None
    issued_at: datetime | None
    total: float | None
    currency: str | None
    tax_amount: float | None


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
        params: tuple[str, ...] = ()
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
                total=float(row["total"]) if row["total"] is not None else None,
                currency=row["currency"],
                tax_amount=float(row["tax_amount"]) if row["tax_amount"] is not None else None,
            )
            for row in rows
        ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL", "postgresql://factus:factus@postgres:5432/factus")
    app.state.db_pool = await asyncpg.create_pool(database_url)
    etl_service = InvoiceEtlService()
    consumer = InvoiceKafkaConsumer(etl_service=etl_service)
    await consumer.start()
    app.state.consumer = consumer

    try:
        yield
    finally:
        await consumer.stop()
        await app.state.db_pool.close()


app = FastAPI(title="Invoice ETL Microservice", lifespan=lifespan)
app.include_router(GraphQLRouter(strawberry.Schema(query=Query)), prefix="/graphql")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
