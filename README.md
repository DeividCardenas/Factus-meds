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
    invoicing/
      application/
        use_cases/
          process_invoice_batch.py
      domain/
        entities/
          invoice.py
          invoice_batch.py
      infrastructure/
        etl/
          polars_transformer.py
        persistence/
          postgres/
            invoice_repository_asyncpg.py
    kafka/
      consumer.py
    shared/
      infrastructure/
        logging/
          structured_logger.py
    main.py
```

## Contenedorización local (Kafka + Laravel + ETL)

1. Crea tu archivo de entorno para Docker:

```bash
cp .env.example .env
```

2. Ajusta en `.env` las credenciales `FACTUS_*` si vas a usar credenciales reales.

3. Levanta todo el stack:

```bash
docker compose up --build
```

4. En otra terminal, envía un lote de prueba al endpoint de ingesta:

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

5. Revisa la consola del contenedor `etl` para ver el `DataFrame` transformado por Polars.

## Observabilidad

- Jaeger UI: `http://localhost:16686`
- Prometheus UI: `http://localhost:9090`

## Prueba de estrés con k6 (Docker)

```bash
docker run --rm --network factus-meds_default \
  -v "$PWD/load_testing:/scripts" \
  grafana/k6 run /scripts/stress_test.js
```
