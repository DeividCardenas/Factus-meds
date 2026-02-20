<?php

use App\Http\Controllers\Api\InvoiceBatchController;
use Illuminate\Support\Facades\Route;

Route::post('/v1/invoice-batches', [InvoiceBatchController::class, 'store']);
