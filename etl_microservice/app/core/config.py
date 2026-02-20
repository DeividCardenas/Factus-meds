import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BROKERS", "127.0.0.1:9092")
    kafka_topic: str = os.getenv("KAFKA_INGEST_TOPIC", "invoice.ingest.v1")
    kafka_dlq_topic: str = os.getenv("KAFKA_DLQ_TOPIC", "invoice.ingest.v1.dlq")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "invoice-etl-v1")
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://factus:factus@postgres:5432/factus"
    )
    factus_base_url: str = os.getenv(
        "FACTUS_BASE_URL", "https://api-sandbox.factus.com.co"
    )
    factus_email: str = os.getenv("FACTUS_EMAIL", "")
    factus_password: str = os.getenv("FACTUS_PASSWORD", "")
    factus_client_id: str = os.getenv("FACTUS_CLIENT_ID", "")
    factus_client_secret: str = os.getenv("FACTUS_CLIENT_SECRET", "")


settings = Settings()
