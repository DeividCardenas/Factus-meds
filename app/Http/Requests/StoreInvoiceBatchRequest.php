<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreInvoiceBatchRequest extends FormRequest
{
    public function authorize(): bool
    {
        $configuredKey = config('ingest.api_key');
        $providedKey = (string) $this->header('X-Ingest-Key', '');

        return is_string($configuredKey)
            && $configuredKey !== ''
            && $providedKey !== ''
            && hash_equals($configuredKey, $providedKey);
    }

    public function rules(): array
    {
        $maxBatchSize = (int) config('ingest.max_batch_size');

        return [
            'source' => ['nullable', 'string', 'in:json,csv'],
            'invoices' => ['required', 'array', 'min:1', "max:{$maxBatchSize}"],
            'invoices.*.external_id' => ['required', 'string', 'max:64'],
            'invoices.*.customer_id' => ['required', 'string', 'max:64'],
            'invoices.*.issued_at' => ['required', 'date'],
            'invoices.*.total' => ['required', 'numeric', 'min:0'],
            'invoices.*.currency' => ['required', 'string', 'size:3'],
        ];
    }
}
