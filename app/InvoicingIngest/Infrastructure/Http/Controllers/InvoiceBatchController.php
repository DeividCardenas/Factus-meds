<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Infrastructure\Http\Controllers;

use App\Http\Controllers\Controller;
use App\InvoicingIngest\Application\Ports\Input\AcceptInvoiceBatchInputPort;
use App\InvoicingIngest\Application\UseCases\AcceptInvoiceBatch\AcceptInvoiceBatchCommand;
use App\InvoicingIngest\Infrastructure\Http\Requests\StoreInvoiceBatchRequest;
use Illuminate\Http\JsonResponse;

final class InvoiceBatchController extends Controller
{
    public function store(StoreInvoiceBatchRequest $request, AcceptInvoiceBatchInputPort $useCase): JsonResponse
    {
        $batchId = $useCase->handle(new AcceptInvoiceBatchCommand($request->toDto()));

        return response()->json(['batch_id' => $batchId, 'status' => 'accepted'], 202);
    }
}
