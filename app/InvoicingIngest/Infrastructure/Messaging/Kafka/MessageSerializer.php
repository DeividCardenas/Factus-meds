<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Infrastructure\Messaging\Kafka;

use App\InvoicingIngest\Domain\Entities\InvoiceBatch;
use JsonException;
use RuntimeException;

final class MessageSerializer
{
    public function serialize(InvoiceBatch $invoiceBatch): string
    {
        try {
            return json_encode([
                'batch_id' => $invoiceBatch->batchId()->toString(),
                'received_at' => $invoiceBatch->acceptedAt()->format(DATE_ATOM),
                'payload' => $invoiceBatch->payload(),
            ], JSON_THROW_ON_ERROR);
        } catch (JsonException $exception) {
            throw new RuntimeException('Unable to encode batch payload for kafka.', previous: $exception);
        }
    }
}
