<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Infrastructure\Persistence\Cache;

use App\InvoicingIngest\Application\Ports\Output\CacheBatchPayloadPort;
use App\InvoicingIngest\Domain\Entities\InvoiceBatch;
use Illuminate\Contracts\Cache\Repository as CacheRepository;

final class LaravelCacheBatchPayloadRepository implements CacheBatchPayloadPort
{
    public function __construct(private readonly CacheRepository $cache)
    {
    }

    public function store(InvoiceBatch $invoiceBatch): void
    {
        $batchId = $invoiceBatch->batchId()->toString();
        $cacheKey = $this->cacheKey($batchId);

        $this->cache->put(
            $cacheKey,
            [
                'status' => 'accepted',
                'payload' => $invoiceBatch->payload(),
            ],
            now()->addMinutes((int) config('ingest.payload_ttl_minutes'))
        );
    }

    public function forget(string $batchId): void
    {
        $this->cache->forget($this->cacheKey($batchId));
    }

    private function cacheKey(string $batchId): string
    {
        return sprintf('invoice-batch:%s', $batchId);
    }
}
