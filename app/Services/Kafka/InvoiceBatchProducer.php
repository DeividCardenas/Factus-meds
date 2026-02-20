<?php

namespace App\Services\Kafka;

use JsonException;
use RuntimeException;

class InvoiceBatchProducer
{
    private \RdKafka\Producer $producer;

    public function __construct()
    {
        if (! class_exists(\RdKafka\Producer::class)) {
            throw new RuntimeException('php-rdkafka extension is required.');
        }

        $this->producer = new \RdKafka\Producer();
        $this->producer->addBrokers((string) config('kafka.brokers'));
    }

    public function publish(string $batchId, array $payload): void
    {
        $topic = $this->producer->newTopic((string) config('kafka.topic'));

        try {
            $message = json_encode([
                'batch_id' => $batchId,
                'received_at' => now()->toIso8601String(),
                'payload' => $payload,
            ], JSON_THROW_ON_ERROR);
        } catch (JsonException $exception) {
            throw new RuntimeException(
                sprintf('Unable to encode payload for batch %s.', $batchId),
                previous: $exception
            );
        }

        $topic->produce(
            RD_KAFKA_PARTITION_UA,
            0,
            $message,
            $batchId
        );

        $flushResult = $this->producer->flush((int) config('kafka.flush_timeout_ms', 1000));

        if ($flushResult !== RD_KAFKA_RESP_ERR_NO_ERROR) {
            throw new RuntimeException(
                sprintf('Kafka flush failed for batch %s. Error code: %d', $batchId, $flushResult)
            );
        }
    }
}
