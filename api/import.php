<?php
/**
 * Excel Import API Endpoint
 * 
 * Main handler for Excel file upload and import processing
 * 
 * @package Expertak\API
 */

// Set error reporting for development (disable in production)
error_reporting(E_ALL);
ini_set('display_errors', 0); // Don't display errors to users
ini_set('log_errors', 1);

// Set execution time and memory limits
set_time_limit(\Expertak\Config\Constants::MAX_EXECUTION_TIME);
ini_set('memory_limit', \Expertak\Config\Constants::MEMORY_LIMIT);

// Set UTF-8 encoding
header('Content-Type: application/json; charset=utf-8');

// Basic CORS for local frontend
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
mb_internal_encoding('UTF-8');

// Include autoloader
require_once __DIR__ . '/../includes/autoload.php';

use Expertak\Config\Constants;
use Expertak\Config\Database;
use Expertak\Includes\ExcelValidator;
use Expertak\Includes\ExcelProcessor;
use Expertak\Includes\DatabaseOperations;

/**
 * Send JSON response
 */
function sendResponse(array $data, int $statusCode = 200): void
{
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

/**
 * Send error response
 */
function sendError(string $message, int $statusCode = 400, array $details = []): void
{
    sendResponse([
        'success' => false,
        'message' => $message,
        'details' => $details
    ], $statusCode);
}

/**
 * Send success response
 */
function sendSuccess(array $data = []): void
{
    sendResponse([
        'success' => true,
        'message' => 'Import completed successfully',
        'data' => $data
    ], 200);
}

// Main execution
try {
    // Handle preflight
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        sendResponse(['success' => true], 200);
    }

    // Check if request method is POST
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        sendError('Only POST method is allowed', 405);
    }

    // Check if file was uploaded (supports "file" or "excel_file")
    $fileKey = null;
    if (isset($_FILES['file'])) {
        $fileKey = 'file';
    } elseif (isset($_FILES['excel_file'])) {
        $fileKey = 'excel_file';
    }

    if ($fileKey === null || $_FILES[$fileKey]['error'] !== UPLOAD_ERR_OK) {
        $errorMessages = [
            UPLOAD_ERR_INI_SIZE => 'File exceeds upload_max_filesize directive',
            UPLOAD_ERR_FORM_SIZE => 'File exceeds MAX_FILE_SIZE directive',
            UPLOAD_ERR_PARTIAL => 'File was only partially uploaded',
            UPLOAD_ERR_NO_FILE => 'No file was uploaded',
            UPLOAD_ERR_NO_TMP_DIR => 'Missing temporary folder',
            UPLOAD_ERR_CANT_WRITE => 'Failed to write file to disk',
            UPLOAD_ERR_EXTENSION => 'File upload stopped by extension'
        ];

        $errorCode = $fileKey ? ($_FILES[$fileKey]['error'] ?? UPLOAD_ERR_NO_FILE) : UPLOAD_ERR_NO_FILE;
        $errorMessage = $errorMessages[$errorCode] ?? 'Unknown upload error';
        
        sendError('File upload failed: ' . $errorMessage);
    }

    $uploadedFile = $_FILES[$fileKey];

    // Validate file
    $validator = new ExcelValidator();
    if (!$validator->validateFile($uploadedFile)) {
        sendError('File validation failed', 400, $validator->getErrors());
    }

    // Ensure upload directory exists
    if (!is_dir(Constants::UPLOAD_DIR)) {
        if (!mkdir(Constants::UPLOAD_DIR, 0755, true)) {
            sendError('Failed to create upload directory');
        }
    }

    // Generate unique filename
    $fileExtension = pathinfo($uploadedFile['name'], PATHINFO_EXTENSION);
    $uniqueFileName = date('YmdHis') . '_' . uniqid() . '.' . $fileExtension;
    $targetPath = Constants::UPLOAD_DIR . $uniqueFileName;

    // Move uploaded file
    if (!move_uploaded_file($uploadedFile['tmp_name'], $targetPath)) {
        sendError('Failed to save uploaded file');
    }

    // Test database connection
    if (!Database::testConnection()) {
        unlink($targetPath); // Clean up uploaded file
        sendError('Database connection failed');
    }

    // Initialize components
    $processor = new ExcelProcessor();
    $dbOps = new DatabaseOperations();

    // Load Excel file
    try {
        $processor->loadFile($targetPath);
    } catch (\Exception $e) {
        unlink($targetPath); // Clean up uploaded file
        sendError('Failed to load Excel file: ' . $e->getMessage());
    }

    // Process rows
    $batch = [];
    $batchSize = Constants::BATCH_SIZE;
    $importStats = [
        'total_rows' => 0,
        'inserted' => 0,
        'duplicates' => 0,
        'errors' => [],
        'processing_errors' => []
    ];

    $rowCallback = function (array $row, int $rowNumber) use (&$batch, &$importStats, $dbOps, $uniqueFileName, $batchSize) {
        $importStats['total_rows']++;

        // Add to batch
        $batch[] = $row;

        // Process batch when it reaches batch size
        if (count($batch) >= $batchSize) {
            $batchStats = $dbOps->bulkInsert($batch, $uniqueFileName);
            $importStats['inserted'] += $batchStats['inserted'];
            $importStats['duplicates'] += $batchStats['duplicates'];
            
            // Add batch errors with row numbers
            foreach ($batchStats['errors'] as $error) {
                $importStats['errors'][] = [
                    'row' => $rowNumber - count($batch) + $error['row_index'] + 1,
                    'error' => $error['error']
                ];
            }

            $batch = []; // Clear batch
        }

        return true;
    };

    // Process all rows
    try {
        $processingStats = $processor->processRows($rowCallback);
        
        // Process remaining batch
        if (!empty($batch)) {
            $batchStats = $dbOps->bulkInsert($batch, $uniqueFileName);
            $importStats['inserted'] += $batchStats['inserted'];
            $importStats['duplicates'] += $batchStats['duplicates'];
            
            foreach ($batchStats['errors'] as $error) {
                $importStats['errors'][] = [
                    'row' => $importStats['total_rows'] - count($batch) + $error['row_index'] + 1,
                    'error' => $error['error']
                ];
            }
        }

        // Add processing errors (validation errors)
        $importStats['processing_errors'] = $processingStats['errors'];
    } catch (\Exception $e) {
        $processor->cleanup();
        unlink($targetPath); // Clean up uploaded file
        sendError('Processing failed: ' . $e->getMessage());
    }

    // Cleanup
    $processor->cleanup();
    
    // Optionally delete uploaded file after processing (or keep for audit)
    // unlink($targetPath);

    // Prepare response
    $responseData = [
        'file_name' => $uploadedFile['name'],
        'file_size' => $uploadedFile['size'],
        'total_rows' => $importStats['total_rows'],
        'inserted' => $importStats['inserted'],
        'duplicates' => $importStats['duplicates'],
        'rejected' => count($importStats['errors']) + count($importStats['processing_errors']),
        'errors' => array_merge($importStats['errors'], $importStats['processing_errors'])
    ];

    sendSuccess($responseData);

} catch (\Exception $e) {
    error_log("Import API error: " . $e->getMessage());
    error_log("Stack trace: " . $e->getTraceAsString());
    sendError('Internal server error: ' . $e->getMessage(), 500);
}
