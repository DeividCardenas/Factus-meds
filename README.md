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
