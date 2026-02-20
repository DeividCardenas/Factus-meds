# Factus-meds

## Etapa 1 - Ingesta con Laravel + Kafka

```text
app/
  Http/
    Controllers/
      Api/
        InvoiceBatchController.php
    Requests/
      StoreInvoiceBatchRequest.php
  Jobs/
    PublishInvoiceBatchToKafka.php
  Services/
    Kafka/
      InvoiceBatchProducer.php
config/
  ingest.php
  kafka.php
routes/
  api.php
```

## Etapa 2 - Microservicio ETL (Python)

```text
etl_microservice/
  requirements.txt
  app/
    core/
      config.py
    kafka/
      consumer.py
    services/
      etl_service.py
    main.py
```

## Contenedorización local (Kafka + Laravel + ETL)

1. Levanta todo el stack:

```bash
docker compose up --build
```

2. En otra terminal, envía un lote de prueba al endpoint de ingesta:

```bash
curl -X POST http://localhost:8080/api/v1/invoice-batches \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Key: local-dev-ingest-key" \
  -d '{
    "source": "json",
    "invoices": [
      {
        "external_id": "INV-1001",
        "customer_id": "CUST-77",
        "issued_at": "2026-02-20T00:00:00Z",
        "total": 150000,
        "currency": "COP"
      }
    ]
  }'
```

3. Revisa la consola del contenedor `etl` para ver el `DataFrame` transformado por Polars.
