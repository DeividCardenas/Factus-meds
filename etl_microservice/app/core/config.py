from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BROKERS", "127.0.0.1:9092")
    kafka_topic: str = os.getenv("KAFKA_INGEST_TOPIC", "invoice.ingest.v1")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "invoice-etl-v1")


settings = Settings()
