# RFC: Propuesta de Refactorización Enterprise para Factus-meds

## 1) Objetivo
Elevar la solución actual (Ingesta PHP + ETL/API Python) a un estándar enterprise usando **Clean Architecture + DDD + SOLID + Event-Driven**, sin romper el comportamiento funcional actual (recepción de lotes, publicación a Kafka, transformación ETL, persistencia en PostgreSQL y consulta por GraphQL).

## 2) Diagnóstico crítico del estado actual

### 2.1 Microservicio PHP (Ingesta)
**Fortalezas actuales**
- Existe validación de entrada (`StoreInvoiceBatchRequest`) y autenticación por API key.
- Publicación asíncrona a Kafka a través de Job.

**Hallazgos / deuda técnica**
- Estructura por framework y no por dominio: no hay separación explícita de Application/Domain/Infrastructure.
- El controlador orquesta lógica de aplicación (generación de `batch_id`, cache TTL, despacho del job), mezclando responsabilidades.
- `InvoiceBatchProducer` acopla directamente con `RdKafka` sin interfaz/puerto de salida (difícil testeo y reemplazo).
- Falta estrategia explícita de manejo de excepciones centralizada (errores de publicación/serialización dependen de excepciones locales).
- No se evidencia contrato de idempotencia por `external_id` o `batch_id` aguas abajo.
- No hay evidencia de estandarización PSR-12 automatizada (sin `phpcs`/pint en repo).

### 2.2 Microservicio Python (ETL & API)
**Fortalezas actuales**
- Uso de FastAPI asíncrono, `asyncpg` y `polars` para alto rendimiento.
- Flujo de consumo Kafka y persistencia bulk (`copy_records_to_table`).

**Hallazgos / deuda técnica**
- `main.py` concentra bootstrap, GraphQL schema, acceso a datos y wiring de infraestructura (alto acoplamiento).
- Lógica de consulta GraphQL ejecuta SQL inline desde capa de presentación.
- Consumer Kafka y ETL service dependen de infraestructura concreta sin puertos (interfaces).
- Tipado parcial (`list[dict]`) sin modelos de dominio fuertes (`TypedDict`/Pydantic/dataclasses de dominio).
- Logging no estructurado: uso de `print` en ETL y `logger.warning` mínimo sin correlación (`batch_id`, offsets, partition).
- Manejo de mensajes inválidos solo con skip; no existe Dead Letter Queue (DLQ) ni política de reintentos.
- No se observan controles de calidad estática (mypy/ruff/pytest) versionados.

### 2.3 Docker e infraestructura
**Fortalezas actuales**
- Stack local funcional con healthchecks en PostgreSQL y Kafka.
- Variables de entorno explícitas por servicio.

**Hallazgos / deuda técnica**
- Dockerfiles simples, sin multi-stage ni usuario no-root.
- Sin hardening: faltan prácticas como `read-only rootfs`, `cap_drop`, límites de recursos y política de reinicio.
- `docker-compose.yml` mezcla concerns de desarrollo y operación sin perfiles.
- Sin observabilidad integral (logs estructurados, métricas, trazas).

### 2.4 Manejo de errores y observabilidad
- No existe DLQ para JSON corrupto o payload inválido.
- No hay contrato de error por tipo (validation vs transient infra vs poison message).
- No hay estrategia formal de logging estructurado (JSON logs con campos de correlación).

## 3) Propuesta de arquitectura objetivo (árbol exacto)

### 3.1 PHP Ingesta (Laravel-like)
```text
app/
  Shared/
    Domain/
      ValueObjects/
        Uuid.php
      Exceptions/
        DomainException.php
    Application/
      Contracts/
        Clock.php
      DTO/
        ApiErrorResponse.php
    Infrastructure/
      Logging/
        StructuredLogger.php
      Monitoring/
        Metrics.php

  InvoicingIngest/
    Domain/
      Entities/
        InvoiceBatch.php
        Invoice.php
      ValueObjects/
        BatchId.php
        SourceType.php
      Services/
        BatchValidationPolicy.php
      Repositories/
        BatchPayloadRepository.php        # Puerto de dominio
      Events/
        InvoiceBatchAccepted.php
      Exceptions/
        InvalidInvoiceBatchException.php

    Application/
      UseCases/
        AcceptInvoiceBatch/
          AcceptInvoiceBatchCommand.php
          AcceptInvoiceBatchHandler.php
      Ports/
        Input/
          AcceptInvoiceBatchInputPort.php
        Output/
          PublishInvoiceBatchPort.php
          CacheBatchPayloadPort.php
      DTO/
        InvoiceBatchDTO.php

    Infrastructure/
      Http/
        Controllers/
          InvoiceBatchController.php
        Requests/
          StoreInvoiceBatchRequest.php
        Middleware/
          ApiKeyAuthMiddleware.php
        ExceptionHandling/
          Handler.php
      Messaging/
        Kafka/
          RdKafkaProducerAdapter.php
          MessageSerializer.php
      Persistence/
        Cache/
          LaravelCacheBatchPayloadRepository.php
      Queue/
        Jobs/
          PublishInvoiceBatchToKafkaJob.php

config/
  ingest.php
  kafka.php
routes/
  api.php
```

### 3.2 Python ETL & API (FastAPI + GraphQL + Kafka)
```text
etl_microservice/
  app/
    shared/
      domain/
        errors.py
        value_objects.py
      application/
        dto.py
      infrastructure/
        logging/
          structured_logger.py

    invoicing/
      domain/
        entities/
          invoice.py
          invoice_batch.py
        value_objects/
          money.py
          currency.py
        services/
          tax_policy.py
        repositories/
          invoice_repository.py          # Puerto (Protocol)
        events/
          invoice_batch_received.py
        exceptions/
          invoice_validation_error.py

      application/
        use_cases/
          process_invoice_batch.py
          query_invoices.py
        ports/
          message_consumer_port.py
          dlq_publisher_port.py
          invoice_repository_port.py
        dto/
          invoice_batch_dto.py
          invoice_query_dto.py

      infrastructure/
        api/
          fastapi_app.py
          dependencies.py
          graphql/
            schema.py
            resolvers.py
            types.py
        messaging/
          kafka/
            consumer.py
            producer.py
            dlq_publisher.py
            deserializers.py
        persistence/
          postgres/
            invoice_repository_asyncpg.py
            migrations/
        etl/
          polars_transformer.py

    bootstrap/
      container.py
      settings.py
      lifespan.py

  tests/
    unit/
    integration/
    contract/

  requirements.txt
  mypy.ini
  ruff.toml
```

## 4) Refactorizaciones necesarias priorizadas

### P0 (crítico: estabilidad + seguridad operativa)
1. **Separar capas en ambos servicios** con casos de uso explícitos y puertos/adaptadores.
2. **Implementar DLQ en Kafka** para mensajes corruptos o inválidos:
   - Topic sugerido: `invoice.ingest.v1.dlq`.
   - Enviar payload original + `error_type` + `error_message` + `stack` resumido + `batch_id` + metadata (`topic`, `partition`, `offset`, `timestamp`).
3. **Logging estructurado JSON** en PHP y Python con correlación (`trace_id`, `batch_id`, `external_id`, `kafka_offset`).
4. **Eliminar SQL inline de GraphQL resolver** moviendo queries a caso de uso/repositorio.
5. **Hardening mínimo de contenedores**: usuario no-root, base image slim/alpine segura, dependencias fijadas y limpieza de capas.

### P1 (calidad de ingeniería)
6. **Tipado estático estricto en Python** (`mypy --strict` por módulos nuevos + Protocols + DTO tipados).
7. **Estandarización PSR-12 en PHP** y reglas automáticas de estilo.
8. **Manejo centralizado de excepciones** (HTTP y background workers) con taxonomía de errores.
9. **Inyección de dependencias formal** en bootstrap (container/factory) para desacoplar infraestructura.
10. **Idempotencia y deduplicación** por `external_id`/`batch_id` en persistencia.

### P2 (escalabilidad enterprise)
11. **Docker multi-stage + compose optimizado** por perfiles (`dev`, `ci`, `prod`) y límites de recursos.
12. **Observabilidad extendida**: métricas de latencia ETL, throughput Kafka, tasa de DLQ, fallos de bulk insert.
13. **Pruebas por capas** (unit, contract, integration) y pruebas de carga ETL.
14. **Política de reintentos/backoff** diferenciando errores transitorios vs mensajes venenosos.

## 5) Estrategia DLQ propuesta
1. Intentar deserialización y validación de contrato.
2. Si falla validación de negocio o JSON corrupto: publicar en DLQ inmediatamente (sin retry infinito).
3. Si falla infraestructura transitoria (DB/Kafka timeout): reintento con backoff exponencial acotado.
4. Si excede reintentos: mover a DLQ con causa `TRANSIENT_RETRY_EXHAUSTED`.
5. Exponer métricas y alerta por umbral de DLQ.

## 6) Estrategia de logs estructurados
Formato JSON recomendado:
- `timestamp`, `level`, `service`, `env`, `message`
- `trace_id`, `span_id`, `batch_id`, `external_id`
- `kafka_topic`, `kafka_partition`, `kafka_offset`
- `error_type`, `error_code`, `stack` (cuando aplique)

Ejemplo de eventos de log clave:
- `invoice_batch_received`
- `invoice_batch_validated`
- `kafka_publish_success|failure`
- `etl_transform_completed`
- `bulk_insert_completed|failure`
- `message_sent_to_dlq`

## 7) Plan de ejecución recomendado (incremental)
1. Introducir puertos/casos de uso sin romper endpoints ni contratos Kafka actuales.
2. Mover infraestructura actual a adaptadores concretos.
3. Activar DLQ y logging estructurado.
4. Añadir tipado estricto/linting y pruebas por capas.
5. Hardening de Docker y ajustes de performance finales.

## 8) Criterios de aceptación para el reto
- Separación limpia de Presentation / Application / Domain / Infrastructure en ambos microservicios.
- Uso de casos de uso explícitos y puertos de salida para Kafka/DB/cache.
- DLQ operativa con metadata completa y trazabilidad.
- Logs estructurados end-to-end con correlación por lote.
- Dockerfiles endurecidos y compose más mantenible por perfiles.
- Evidencia de estándares de calidad (mypy/PEP-8 y PSR-12) en pipeline.
