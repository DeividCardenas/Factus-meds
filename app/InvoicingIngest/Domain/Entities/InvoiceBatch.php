<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Domain\Entities;

use App\InvoicingIngest\Domain\ValueObjects\BatchId;
use DateTimeImmutable;

final class InvoiceBatch
{
    private function __construct(
        private readonly BatchId $batchId,
        private readonly array $payload,
        private readonly DateTimeImmutable $acceptedAt
    ) {
    }

    public static function accept(BatchId $batchId, array $payload): self
    {
        return new self($batchId, $payload, new DateTimeImmutable());
    }

    public function batchId(): BatchId
    {
        return $this->batchId;
    }

    public function payload(): array
    {
        return $this->payload;
    }

    public function acceptedAt(): DateTimeImmutable
    {
        return $this->acceptedAt;
    }
}
