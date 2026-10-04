<?php
/**
 * Excel Validation API Endpoint
 *
 * Validates Excel file structure without importing
 *
 * @package Expertak\API
 */

// Set error reporting for development (disable in production)
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);

// Set UTF-8 encoding
header('Content-Type: application/json; charset=utf-8');

// Basic CORS for local frontend
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Include autoloader
require_once __DIR__ . '/../includes/autoload.php';

use Expertak\Config\Constants;
use Expertak\Includes\ExcelValidator;
use PhpOffice\PhpSpreadsheet\IOFactory;
use PhpOffice\PhpSpreadsheet\Reader\Xlsx;

function sendResponse(array $data, int $statusCode = 200): void
{
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

try {
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        sendResponse(['success' => true], 200);
    }

    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        sendResponse([
            'valid' => false,
            'message' => 'Only POST method is allowed'
        ], 405);
    }

    $fileKey = null;
    if (isset($_FILES['file'])) {
        $fileKey = 'file';
    } elseif (isset($_FILES['excel_file'])) {
        $fileKey = 'excel_file';
    }

    if ($fileKey === null || $_FILES[$fileKey]['error'] !== UPLOAD_ERR_OK) {
        sendResponse([
            'valid' => false,
            'message' => 'File upload failed'
        ], 400);
    }

    $uploadedFile = $_FILES[$fileKey];
    $validator = new ExcelValidator();

    if (!$validator->validateFile($uploadedFile)) {
        sendResponse([
            'valid' => false,
            'message' => 'File validation failed',
            'expected_columns' => Constants::EXPECTED_COLUMNS,
            'errors' => $validator->getErrors()
        ], 400);
    }

    // Load spreadsheet and validate structure
    $reader = new Xlsx();
    $reader->setReadDataOnly(true);
    $reader->setReadEmptyCells(false);
    $spreadsheet = $reader->load($uploadedFile['tmp_name']);
    $worksheet = $spreadsheet->getActiveSheet();

    $isValidStructure = $validator->validateStructure($worksheet);

    // Extract actual columns from header row
    $headerRow = $worksheet->getRowIterator(1, 1)->current();
    $cellIterator = $headerRow->getCellIterator();
    $cellIterator->setIterateOnlyExistingCells(false);
    $actualColumns = [];
    foreach ($cellIterator as $cell) {
        $value = trim((string) $cell->getValue());
        if ($value !== '') {
            $actualColumns[] = $value;
        }
    }

    $spreadsheet->disconnectWorksheets();
    $spreadsheet = null;

    if (!$isValidStructure) {
        sendResponse([
            'valid' => false,
            'message' => 'File validation failed',
            'column_count' => count($actualColumns),
            'expected_columns' => Constants::EXPECTED_COLUMNS,
            'actual_columns' => $actualColumns,
            'errors' => $validator->getErrors()
        ], 400);
    }

    sendResponse([
        'valid' => true,
        'message' => 'File is valid',
        'column_count' => count($actualColumns),
        'expected_columns' => Constants::EXPECTED_COLUMNS,
        'actual_columns' => $actualColumns,
        'errors' => []
    ], 200);
} catch (\Exception $e) {
    error_log("Validate API error: " . $e->getMessage());
    sendResponse([
        'valid' => false,
        'message' => 'Internal server error: ' . $e->getMessage()
    ], 500);
}
