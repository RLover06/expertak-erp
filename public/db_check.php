<?php
/**
 * Quick database connection check
 */

header('Content-Type: application/json; charset=utf-8');

require_once __DIR__ . '/../includes/autoload.php';

use Expertak\Config\Database;

try {
    $connected = Database::testConnection();
    if (!$connected) {
        throw new Exception('Database::testConnection() returned false');
    }

    echo json_encode([
        'success' => true,
        'message' => 'Database connection OK'
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
} catch (Throwable $e) {
    error_log('DB check failed: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'message' => 'Database connection failed',
        'error' => $e->getMessage()
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
}
