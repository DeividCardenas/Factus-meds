<?php

declare(strict_types=1);

header('Content-Type: application/json');

$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($method === 'GET' && $path === '/health') {
    http_response_code(200);
    echo json_encode(['status' => 'ok']);
    exit;
}

if ($method !== 'POST' || $path !== '/api/v1/invoice-batches') {
    http_response_code(404);
    echo json_encode(['message' => 'Not Found']);
    exit;
}

$configuredKey = getenv('INGEST_API_KEY') ?: '';
$providedKey = $_SERVER['HTTP_X_INGEST_KEY'] ?? '';

if ($configuredKey === '' || $providedKey === '' || !hash_equals($configuredKey, $providedKey)) {
    http_response_code(401);
    echo json_encode(['message' => 'Unauthorized']);
    exit;
}

$raw = file_get_contents('php://input');
$data = json_decode($raw ?: '', true);

if (!is_array($data) || !isset($data['invoices']) || !is_array($data['invoices']) || count($data['invoices']) === 0) {
    http_response_code(422);
    echo json_encode(['message' => 'Invalid payload']);
    exit;
}

$batchId = bin2hex(random_bytes(16));
$message = json_encode([
    'batch_id' => $batchId,
    'received_at' => gmdate('c'),
    'payload' => $data['invoices'],
], JSON_THROW_ON_ERROR);

$command = [
    'kcat',
    '-P',
    '-b',
    getenv('KAFKA_BROKERS') ?: 'kafka:9092',
    '-t',
    getenv('KAFKA_INGEST_TOPIC') ?: 'invoice.ingest.v1',
    '-k',
    $batchId,
];
$process = proc_open($command, [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);

if (!is_resource($process)) {
    http_response_code(500);
    echo json_encode(['message' => 'Kafka publish error']);
    exit;
}

fwrite($pipes[0], $message);
fclose($pipes[0]);
fclose($pipes[1]);
$stderr = stream_get_contents($pipes[2]);
fclose($pipes[2]);

if (proc_close($process) !== 0) {
    http_response_code(500);
    echo json_encode(['message' => 'Kafka publish error', 'details' => trim((string) $stderr)]);
    exit;
}

http_response_code(202);
echo json_encode([
    'batch_id' => $batchId,
    'status' => 'accepted',
    'message' => 'Batch received and queued for processing.',
]);
