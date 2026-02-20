<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Application\UseCases\AcceptInvoiceBatch;

use App\InvoicingIngest\Application\Ports\Input\AcceptInvoiceBatchInputPort;
use App\InvoicingIngest\Application\Ports\Output\CacheBatchPayloadPort;
use App\InvoicingIngest\Application\Ports\Output\PublishInvoiceBatchPort;
use App\InvoicingIngest\Domain\Entities\InvoiceBatch;
use App\InvoicingIngest\Domain\ValueObjects\BatchId;
use App\Shared\Infrastructure\Logging\StructuredLogger;
use Throwable;

final class AcceptInvoiceBatchHandler implements AcceptInvoiceBatchInputPort
{
    public function __construct(
        private readonly CacheBatchPayloadPort $cacheBatchPayload,
        private readonly PublishInvoiceBatchPort $publishInvoiceBatch,
        private readonly StructuredLogger $logger
    ) {
    }

    public function handle(AcceptInvoiceBatchCommand $command): string
    {
        $batchId = BatchId::generate();
        $invoiceBatch = InvoiceBatch::accept($batchId, $command->invoiceBatch->toPayload());
        $batchIdValue = $batchId->toString();

        $this->cacheBatchPayload->store($invoiceBatch);
        try {
            $this->publishInvoiceBatch->publish($invoiceBatch);
            $this->logger->withBatchId($batchIdValue)->info('invoice_batch_accepted');
        } catch (Throwable $exception) {
            $this->cacheBatchPayload->forget($batchIdValue);
            $this->logger->withBatchId($batchIdValue)->error('invoice_batch_publish_failed', [
                'error_type' => $exception::class,
                'error_message' => $exception->getMessage(),
            ]);

            throw $exception;
        }

        return $batchIdValue;
    }
}
