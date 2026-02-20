<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\StoreInvoiceBatchRequest;
use App\Jobs\PublishInvoiceBatchToKafka;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Str;

class InvoiceBatchController extends Controller
{
    public function store(StoreInvoiceBatchRequest $request): JsonResponse
    {
        $batchId = (string) Str::uuid();
        $payload = $request->validated();
        $payloadCacheKey = "invoice-batch:{$batchId}";

        Cache::put($payloadCacheKey, $payload, now()->addMinutes(10));
        PublishInvoiceBatchToKafka::dispatch($batchId, $payloadCacheKey);

        return response()->json([
            'batch_id' => $batchId,
            'status' => 'accepted',
            'message' => 'Batch received and queued for processing.',
        ], 202);
    }
}
