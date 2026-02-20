<?php

namespace App\Jobs;

use App\Services\Kafka\InvoiceBatchProducer;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class PublishInvoiceBatchToKafka implements ShouldQueue
{
    use Dispatchable;
    use InteractsWithQueue;
    use Queueable;
    use SerializesModels;

    public function __construct(
        public string $batchId,
        public array $payload
    ) {
    }

    public function handle(InvoiceBatchProducer $producer): void
    {
        $producer->publish($this->batchId, $this->payload);
    }
}
