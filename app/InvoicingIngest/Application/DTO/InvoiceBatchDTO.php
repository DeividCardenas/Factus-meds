<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Application\DTO;

final readonly class InvoiceBatchDTO
{
    public function __construct(
        public ?string $source,
        public array $invoices
    ) {
    }

    public function toPayload(): array
    {
        return [
            'source' => $this->source,
            'invoices' => $this->invoices,
        ];
    }
}
