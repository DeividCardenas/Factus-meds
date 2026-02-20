<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Application\Ports\Input;

use App\InvoicingIngest\Application\UseCases\AcceptInvoiceBatch\AcceptInvoiceBatchCommand;

interface AcceptInvoiceBatchInputPort
{
    public function handle(AcceptInvoiceBatchCommand $command): string;
}
