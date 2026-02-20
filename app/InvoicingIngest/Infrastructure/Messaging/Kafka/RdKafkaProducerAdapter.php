<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Infrastructure\Messaging\Kafka;

use App\InvoicingIngest\Application\Ports\Output\PublishInvoiceBatchPort;
use App\InvoicingIngest\Domain\Entities\InvoiceBatch;
use App\Shared\Infrastructure\Logging\StructuredLogger;
use RuntimeException;

final class RdKafkaProducerAdapter implements PublishInvoiceBatchPort
{
    private readonly \RdKafka\Producer $producer;

    public function __construct(
        private readonly MessageSerializer $serializer,
        private readonly StructuredLogger $logger
    ) {
        if (! class_exists(\RdKafka\Producer::class)) {
            throw new RuntimeException('php-rdkafka extension is required.');
        }

        $this->producer = new \RdKafka\Producer();
        $this->producer->addBrokers((string) config('kafka.brokers'));
    }

    public function publish(InvoiceBatch $invoiceBatch): void
    {
        $batchId = $invoiceBatch->batchId()->toString();
        $topic = $this->producer->newTopic((string) config('kafka.topic'));

        $topic->produce(
            RD_KAFKA_PARTITION_UA,
            0,
            $this->serializer->serialize($invoiceBatch),
            $batchId
        );

        $flushResult = $this->producer->flush((int) config('kafka.flush_timeout_ms'));

        if ($flushResult !== RD_KAFKA_RESP_ERR_NO_ERROR) {
            $this->logger->withBatchId($batchId)->error('kafka_publish_failure', ['error_code' => $flushResult]);

            throw new RuntimeException(sprintf('Kafka flush failed for batch %s. Error code: %d', $batchId, $flushResult));
        }

        $this->logger->withBatchId($batchId)->info('kafka_publish_success');
    }
}
