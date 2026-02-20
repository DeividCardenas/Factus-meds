<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Application\UseCases\AcceptInvoiceBatch;

use App\InvoicingIngest\Application\DTO\InvoiceBatchDTO;

final readonly class AcceptInvoiceBatchCommand
{
    public function __construct(public InvoiceBatchDTO $invoiceBatch)
    {
    }
}
