<?php

namespace App\Jobs;

use App\Services\Kafka\InvoiceBatchProducer;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Cache;

class PublishInvoiceBatchToKafka implements ShouldQueue
{
    use Dispatchable;
    use InteractsWithQueue;
    use Queueable;
    use SerializesModels;

    public function __construct(
        public string $batchId,
        public string $payloadCacheKey
    ) {
    }

    public function handle(InvoiceBatchProducer $producer): void
    {
        $payload = Cache::pull($this->payloadCacheKey);

        if (is_array($payload)) {
            $producer->publish($this->batchId, $payload);
        }
    }
}
