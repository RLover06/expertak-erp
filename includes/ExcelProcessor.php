<?php
/**
 * Excel Processor
 * 
 * Handles reading and processing Excel files using PhpSpreadsheet
 * Optimized for large files with memory management
 * 
 * @package Expertak\Includes
 */

namespace Expertak\Includes;

use PhpOffice\PhpSpreadsheet\IOFactory;
use PhpOffice\PhpSpreadsheet\Reader\Xlsx;
use PhpOffice\PhpSpreadsheet\Spreadsheet;
use Expertak\Config\Constants;
use Expertak\Includes\ExcelValidator;

/**
 * Excel file processor class
 */
class ExcelProcessor
{
    /**
     * @var ExcelValidator Validator instance
     */
    private ExcelValidator $validator;

    /**
     * @var Spreadsheet|null Loaded spreadsheet instance
     */
    private ?Spreadsheet $spreadsheet = null;

    /**
     * Constructor
     */
    public function __construct()
    {
        $this->validator = new ExcelValidator();
    }

    /**
     * Load Excel file
     * 
     * @param string $filePath Path to Excel file
     * @return bool True if loaded successfully
     * @throws \Exception If file cannot be loaded
     */
    public function loadFile(string $filePath): bool
    {
        if (!file_exists($filePath)) {
            throw new \Exception("File not found: {$filePath}");
        }

        try {
            // Configure reader for memory efficiency
            $reader = new Xlsx();
            $reader->setReadDataOnly(true); // Read only data, skip formatting
            $reader->setReadEmptyCells(false); // Skip empty cells

            // Load spreadsheet
            $this->spreadsheet = $reader->load($filePath);

            // Validate structure
            $worksheet = $this->spreadsheet->getActiveSheet();
            if (!$this->validator->validateStructure($worksheet)) {
                throw new \Exception("Invalid Excel structure: " . implode(', ', $this->validator->getErrors()));
            }

            return true;
        } catch (\Exception $e) {
            error_log("ExcelProcessor::loadFile error: " . $e->getMessage());
            throw $e;
        }
    }

    /**
     * Process Excel file row by row
     * 
     * @param callable $rowCallback Callback function for each row: function(array $row, int $rowNumber): bool
     * @return array Statistics: ['total' => int, 'processed' => int, 'errors' => array]
     */
    public function processRows(callable $rowCallback): array
    {
        if ($this->spreadsheet === null) {
            throw new \Exception("No spreadsheet loaded. Call loadFile() first.");
        }

        $worksheet = $this->spreadsheet->getActiveSheet();
        $highestRow = $worksheet->getHighestRow();
        
        $stats = [
            'total' => 0,
            'processed' => 0,
            'errors' => []
        ];

        // Start from row 2 (skip header row)
        for ($rowNumber = 2; $rowNumber <= $highestRow; $rowNumber++) {
            $stats['total']++;

            // Read row data
            $rowData = $this->readRow($worksheet, $rowNumber);

            // Skip empty rows
            if ($this->isRowEmpty($rowData)) {
                continue;
            }

            // Validate row
            if (!$this->validator->validateRow($rowData, $rowNumber)) {
                $stats['errors'][] = [
                    'row' => $rowNumber,
                    'errors' => $this->validator->getErrors()
                ];
                $this->validator->clearErrors();
                continue;
            }

            // Normalize row data
            $normalizedRow = $this->normalizeRow($rowData);

            // Call callback
            try {
                if ($rowCallback($normalizedRow, $rowNumber)) {
                    $stats['processed']++;
                }
            } catch (\Exception $e) {
                $stats['errors'][] = [
                    'row' => $rowNumber,
                    'errors' => [$e->getMessage()]
                ];
            }

            // Memory management: unset row data
            unset($rowData, $normalizedRow);

            // Periodic garbage collection for large files
            if ($rowNumber % 1000 === 0) {
                gc_collect_cycles();
            }
        }

        return $stats;
    }

    /**
     * Read a single row from worksheet
     * 
     * @param \PhpOffice\PhpSpreadsheet\Worksheet\Worksheet $worksheet Worksheet instance
     * @param int $rowNumber Row number (1-based)
     * @return array Associative array with column names as keys
     */
    private function readRow(\PhpOffice\PhpSpreadsheet\Worksheet\Worksheet $worksheet, int $rowNumber): array
    {
        $rowData = [];
        
        foreach (Constants::EXPECTED_COLUMNS as $index => $columnName) {
            $cellAddress = \PhpOffice\PhpSpreadsheet\Cell\Coordinate::stringFromColumnIndex($index + 1) . $rowNumber;
            $cell = $worksheet->getCell($cellAddress);
            $rowData[$columnName] = $cell->getValue();
        }

        return $rowData;
    }

    /**
     * Check if row is empty
     * 
     * @param array $rowData Row data
     * @return bool True if row is empty
     */
    private function isRowEmpty(array $rowData): bool
    {
        foreach ($rowData as $value) {
            if (trim($value) !== '') {
                return false;
            }
        }
        return true;
    }

    /**
     * Normalize row data (convert types, format dates, etc.)
     * 
     * @param array $rowData Raw row data
     * @return array Normalized row data
     */
    private function normalizeRow(array $rowData): array
    {
        $normalized = [];

        // Normalize each field
        $decimalFields = [
            'iva', 'ica', 'ic', 'inc', 'timbre',
            'inc_bolsas', 'in_carbono', 'in_combustibles',
            'ic_datos', 'icl', 'inpp', 'ibua', 'icui',
            'rete_iva', 'rete_renta', 'rete_ica', 'total'
        ];
        $intFields = ['nit_emisor', 'nit_receptor'];

        foreach ($rowData as $key => $value) {
            switch ($key) {
                case 'fecha_emision':
                    $normalized[$key] = $this->validator->parseDate($value);
                    break;

                case 'fecha_recepcion':
                    $normalized[$key] = $this->validator->parseDateTime($value);
                    break;

                default:
                    if (in_array($key, $decimalFields, true)) {
                        $normalized[$key] = $this->validator->parseNumeric($value) ?? 0.0;
                    } elseif (in_array($key, $intFields, true)) {
                        $normalized[$key] = $this->validator->parseInteger($value);
                    } else {
                        // String fields: trim and convert to string
                        $normalized[$key] = trim((string) $value);
                    }
                    break;
            }
        }

        return $normalized;
    }

    /**
     * Clean up resources
     */
    public function cleanup(): void
    {
        if ($this->spreadsheet !== null) {
            $this->spreadsheet->disconnectWorksheets();
            $this->spreadsheet = null;
        }
        gc_collect_cycles();
    }

    /**
     * Get validator instance
     * 
     * @return ExcelValidator Validator instance
     */
    public function getValidator(): ExcelValidator
    {
        return $this->validator;
    }
}
