<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Infrastructure\Providers;

use App\InvoicingIngest\Application\Ports\Input\AcceptInvoiceBatchInputPort;
use App\InvoicingIngest\Application\Ports\Output\CacheBatchPayloadPort;
use App\InvoicingIngest\Application\Ports\Output\PublishInvoiceBatchPort;
use App\InvoicingIngest\Application\UseCases\AcceptInvoiceBatch\AcceptInvoiceBatchHandler;
use App\InvoicingIngest\Infrastructure\Messaging\Kafka\MessageSerializer;
use App\InvoicingIngest\Infrastructure\Messaging\Kafka\RdKafkaProducerAdapter;
use App\InvoicingIngest\Infrastructure\Persistence\Cache\LaravelCacheBatchPayloadRepository;
use App\Shared\Infrastructure\Logging\StructuredLogger;
use Illuminate\Cache\CacheManager;
use Illuminate\Log\LogManager;
use Illuminate\Support\ServiceProvider;

final class InvoicingIngestServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(StructuredLogger::class, fn (): StructuredLogger => new StructuredLogger(
            app(LogManager::class)->channel((string) config('logging.default', 'stack')),
            [
                'service' => 'invoicing-ingest',
                'env' => (string) config('app.env', 'local'),
            ]
        ));

        $this->app->bind(CacheBatchPayloadPort::class, fn (): LaravelCacheBatchPayloadRepository => new LaravelCacheBatchPayloadRepository(
            app(CacheManager::class)->store()
        ));

        $this->app->singleton(MessageSerializer::class);

        $this->app->singleton(PublishInvoiceBatchPort::class, fn (): RdKafkaProducerAdapter => new RdKafkaProducerAdapter(
            app(MessageSerializer::class),
            app(StructuredLogger::class)
        ));
        $this->app->bind(AcceptInvoiceBatchInputPort::class, AcceptInvoiceBatchHandler::class);
    }
}
