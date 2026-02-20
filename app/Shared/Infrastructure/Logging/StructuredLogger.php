<?php

declare(strict_types=1);

namespace App\Shared\Infrastructure\Logging;

use JsonException;
use Psr\Log\LoggerInterface;
use Psr\Log\LogLevel;
use RuntimeException;

final class StructuredLogger
{
    public function __construct(
        private readonly LoggerInterface $logger,
        private readonly array $baseContext = []
    ) {
    }

    public function withBatchId(string $batchId): self
    {
        return new self($this->logger, [...$this->baseContext, 'batch_id' => $batchId]);
    }

    public function info(string $message, array $context = []): void
    {
        $this->log(LogLevel::INFO, $message, $context);
    }

    public function error(string $message, array $context = []): void
    {
        $this->log(LogLevel::ERROR, $message, $context);
    }

    private function log(string $level, string $message, array $context): void
    {
        $payload = [
            'timestamp' => gmdate('c'),
            'level' => $level,
            'message' => $message,
            ...$this->baseContext,
            ...$context,
        ];

        try {
            $this->logger->log($level, json_encode($payload, JSON_THROW_ON_ERROR));
        } catch (JsonException $exception) {
            throw new RuntimeException('Unable to encode structured log payload.', previous: $exception);
        }
    }
}
