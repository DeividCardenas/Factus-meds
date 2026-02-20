<?php

declare(strict_types=1);

use App\InvoicingIngest\Infrastructure\Http\Controllers\InvoiceBatchController;
use Illuminate\Support\Facades\Route;

Route::post('/v1/invoice-batches', [InvoiceBatchController::class, 'store'])
    ->middleware('throttle:api');
