<?php

return [
    'brokers' => env('KAFKA_BROKERS', '127.0.0.1:9092'),
    'topic' => env('KAFKA_INGEST_TOPIC', 'invoice.ingest.v1'),
    'flush_timeout_ms' => env('KAFKA_FLUSH_TIMEOUT_MS', 1000),
];
