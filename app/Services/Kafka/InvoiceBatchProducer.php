<?php

namespace App\Services\Kafka;

use RuntimeException;

class InvoiceBatchProducer
{
    public function publish(string $batchId, array $payload): void
    {
        if (! class_exists(\RdKafka\Producer::class)) {
            throw new RuntimeException('php-rdkafka extension is required.');
        }

        $producer = new \RdKafka\Producer();
        $producer->addBrokers((string) config('kafka.brokers'));

        $topic = $producer->newTopic((string) config('kafka.topic'));
        $topic->produce(
            RD_KAFKA_PARTITION_UA,
            0,
            json_encode([
                'batch_id' => $batchId,
                'received_at' => now()->toIso8601String(),
                'payload' => $payload,
            ], JSON_THROW_ON_ERROR),
            $batchId
        );

        $producer->flush((int) config('kafka.flush_timeout_ms', 1000));
    }
}
