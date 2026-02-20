<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Application\Ports\Output;

use App\InvoicingIngest\Domain\Entities\InvoiceBatch;

interface PublishInvoiceBatchPort
{
    public function publish(InvoiceBatch $invoiceBatch): void;
}
