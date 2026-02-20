from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.kafka.consumer import InvoiceKafkaConsumer
from app.services.etl_service import InvoiceEtlService


@asynccontextmanager
async def lifespan(app: FastAPI):
    etl_service = InvoiceEtlService()
    consumer = InvoiceKafkaConsumer(etl_service=etl_service)
    await consumer.start()
    app.state.consumer = consumer

    try:
        yield
    finally:
        await consumer.stop()


app = FastAPI(title="Invoice ETL Microservice", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
