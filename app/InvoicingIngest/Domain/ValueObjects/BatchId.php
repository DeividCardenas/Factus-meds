<?php

declare(strict_types=1);

namespace App\InvoicingIngest\Domain\ValueObjects;

use InvalidArgumentException;

final class BatchId
{
    private const UUID_V4_PATTERN = '/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i';

    private function __construct(private readonly string $value)
    {
    }

    public static function generate(): self
    {
        $bytes = random_bytes(16);
        $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
        $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);

        return new self(vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4)));
    }

    public static function fromString(string $value): self
    {
        if (! preg_match(self::UUID_V4_PATTERN, $value)) {
            throw new InvalidArgumentException('Invalid batch id format.');
        }

        return new self(strtolower($value));
    }

    public function toString(): string
    {
        return $this->value;
    }
}
