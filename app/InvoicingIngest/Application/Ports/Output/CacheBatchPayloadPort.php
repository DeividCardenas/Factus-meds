<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Application\Ports\Output;

use App\InvoicingIngest\Domain\Entities\InvoiceBatch;

interface CacheBatchPayloadPort
{
    public function store(InvoiceBatch $invoiceBatch): void;

    public function forget(string $batchId): void;
}
