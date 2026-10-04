<?php
/**
 * Application Constants
 * 
 * Centralized configuration constants for the Excel import system
 * 
 * @package Expertak\Config
 */

namespace Expertak\Config;

/**
 * Excel import configuration constants
 */
class Constants
{
    // File upload settings
    public const UPLOAD_DIR = __DIR__ . '/../uploads/';
    public const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
    public const ALLOWED_EXTENSIONS = ['xlsx'];
    public const ALLOWED_MIME_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/octet-stream' // Some servers may report this for .xlsx
    ];

    // Excel structure definition (CRITICAL - must match Excel file exactly)
    public const EXPECTED_COLUMNS = [
        'tipo_documento',
        'cufe_cude',
        'folio',
        'prefijo',
        'divisa',
        'forma_pago',
        'medio_pago',
        'fecha_emision',
        'fecha_recepcion',
        'nit_emisor',
        'nombre_emisor',
        'nit_receptor',
        'nombre_receptor',
        'iva',
        'ica',
        'ic',
        'inc',
        'timbre',
        'inc_bolsas',
        'in_carbono',
        'in_combustibles',
        'ic_datos',
        'icl',
        'inpp',
        'ibua',
        'icui',
        'rete_iva',
        'rete_renta',
        'rete_ica',
        'total',
        'estado',
        'grupo'
    ];

    public const COLUMN_COUNT = 32;

    // Processing settings
    public const BATCH_SIZE = 500; // Rows per transaction batch
    public const MAX_EXECUTION_TIME = 300; // 5 minutes (adjust based on server limits)
    public const MEMORY_LIMIT = '512M'; // Memory limit for processing

    // Database table name
    public const TABLE_NAME = 'documentos_dian';

    // Composite business key for duplicate detection
    // Format: array of column names that form the unique key
    public const DUPLICATE_KEY_COLUMNS = [
        'cufe_cude'
    ];

    // Date format for Excel date parsing
    public const DATE_FORMAT = 'Y-m-d';

    // Error messages
    public const ERROR_INVALID_FILE_TYPE = 'Invalid file type. Only .xlsx files are allowed.';
    public const ERROR_INVALID_MIME_TYPE = 'Invalid MIME type. File may be corrupted.';
    public const ERROR_FILE_TOO_LARGE = 'File size exceeds maximum allowed size.';
    public const ERROR_COLUMN_COUNT_MISMATCH = 'Column count does not match expected structure.';
    public const ERROR_COLUMN_ORDER_MISMATCH = 'Column order does not match expected structure.';
    public const ERROR_UPLOAD_FAILED = 'File upload failed.';
    public const ERROR_DATABASE_ERROR = 'Database operation failed.';
    public const ERROR_DUPLICATE_RECORD = 'Duplicate record detected (already exists in database).';
}
