<?php

return [
    'api_key' => env('INGEST_API_KEY'),
    'payload_ttl_minutes' => env('INGEST_PAYLOAD_TTL_MINUTES', 10),
    'max_batch_size' => env('INGEST_MAX_BATCH_SIZE', 40000),
];
