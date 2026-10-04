<?php
/**
 * Excel File Validator
 * 
 * Validates Excel file structure, format, and content before processing
 * 
 * @package Expertak\Includes
 */

namespace Expertak\Includes;

use Expertak\Config\Constants;

/**
 * Excel file validator class
 */
class ExcelValidator
{
    /**
     * @var array Validation errors
     */
    private array $errors = [];

    /**
     * Validate uploaded file
     * 
     * @param array $file $_FILES array element
     * @return bool True if valid, false otherwise
     */
    public function validateFile(array $file): bool
    {
        $this->errors = [];

        // Check if file was uploaded
        if (!isset($file['tmp_name']) || !is_uploaded_file($file['tmp_name'])) {
            $this->errors[] = Constants::ERROR_UPLOAD_FAILED;
            return false;
        }

        // Check file size
        if ($file['size'] > Constants::MAX_FILE_SIZE) {
            $this->errors[] = Constants::ERROR_FILE_TOO_LARGE;
            return false;
        }

        // Check file extension
        $extension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        if (!in_array($extension, Constants::ALLOWED_EXTENSIONS)) {
            $this->errors[] = Constants::ERROR_INVALID_FILE_TYPE;
            return false;
        }

        // Check MIME type
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mimeType = finfo_file($finfo, $file['tmp_name']);
        finfo_close($finfo);

        if (!in_array($mimeType, Constants::ALLOWED_MIME_TYPES)) {
            $this->errors[] = Constants::ERROR_INVALID_MIME_TYPE;
            return false;
        }

        return true;
    }

    /**
     * Validate Excel file structure (headers)
     * 
     * @param \PhpOffice\PhpSpreadsheet\Worksheet\Worksheet $worksheet Spreadsheet worksheet
     * @return bool True if structure is valid
     */
    public function validateStructure(\PhpOffice\PhpSpreadsheet\Worksheet\Worksheet $worksheet): bool
    {
        $this->errors = [];

        // Get header row (row 1)
        $headerRow = $worksheet->getRowIterator(1, 1)->current();
        $cellIterator = $headerRow->getCellIterator();
        $cellIterator->setIterateOnlyExistingCells(false);

        $headers = [];
        foreach ($cellIterator as $cell) {
            $value = trim($cell->getValue());
            if ($value !== '') {
                $headers[] = strtolower($value);
            }
        }

        // Check column count
        if (count($headers) !== Constants::COLUMN_COUNT) {
            $this->errors[] = sprintf(
                '%s Expected %d columns, found %d.',
                Constants::ERROR_COLUMN_COUNT_MISMATCH,
                Constants::COLUMN_COUNT,
                count($headers)
            );
            return false;
        }

        // Check column order and names
        $expectedHeaders = array_map('strtolower', Constants::EXPECTED_COLUMNS);
        if ($headers !== $expectedHeaders) {
            $this->errors[] = sprintf(
                '%s Expected columns: %s',
                Constants::ERROR_COLUMN_ORDER_MISMATCH,
                implode(', ', Constants::EXPECTED_COLUMNS)
            );
            return false;
        }

        return true;
    }

    /**
     * Validate a single data row
     * 
     * @param array $row Row data as associative array
     * @param int $rowNumber Row number (for error reporting)
     * @return bool True if row is valid
     */
    public function validateRow(array $row, int $rowNumber): bool
    {
        $rowErrors = [];

        // Required fields validation (NOT NULL columns)
        $requiredFields = ['tipo_documento', 'cufe_cude', 'total'];
        
        foreach ($requiredFields as $field) {
            if (!isset($row[$field]) || trim($row[$field]) === '') {
                $rowErrors[] = "Row {$rowNumber}: Required field '{$field}' is empty.";
            }
        }

        // Date validation
        if (isset($row['fecha_emision']) && trim($row['fecha_emision']) !== '') {
            $date = $this->parseDate($row['fecha_emision']);
            if ($date === false) {
                $rowErrors[] = "Row {$rowNumber}: Invalid date format for 'fecha_emision': {$row['fecha_emision']}";
            }
        }
        
        if (isset($row['fecha_recepcion']) && trim($row['fecha_recepcion']) !== '') {
            $dateTime = $this->parseDateTime($row['fecha_recepcion']);
            if ($dateTime === false) {
                $rowErrors[] = "Row {$rowNumber}: Invalid datetime format for 'fecha_recepcion': {$row['fecha_recepcion']}";
            }
        }

        // Numeric fields validation
        $numericFields = [
            'iva', 'ica', 'ic', 'inc', 'timbre',
            'inc_bolsas', 'in_carbono', 'in_combustibles',
            'ic_datos', 'icl', 'inpp', 'ibua', 'icui',
            'rete_iva', 'rete_renta', 'rete_ica', 'total'
        ];
        foreach ($numericFields as $field) {
            if (isset($row[$field]) && trim($row[$field]) !== '') {
                $value = $this->parseNumeric($row[$field]);
                if ($value === false) {
                    $rowErrors[] = "Row {$rowNumber}: Invalid numeric value for '{$field}': {$row[$field]}";
                }
            }
        }
        
        // Integer fields validation
        $intFields = ['nit_emisor', 'nit_receptor'];
        foreach ($intFields as $field) {
            if (isset($row[$field]) && trim($row[$field]) !== '') {
                $value = $this->parseInteger($row[$field]);
                if ($value === false) {
                    $rowErrors[] = "Row {$rowNumber}: Invalid integer value for '{$field}': {$row[$field]}";
                }
            }
        }

        if (!empty($rowErrors)) {
            $this->errors = array_merge($this->errors, $rowErrors);
            return false;
        }

        return true;
    }

    /**
     * Parse and validate date value
     * 
     * @param mixed $value Date value from Excel
     * @return string|false Formatted date string (Y-m-d) or false on failure
     */
    public function parseDate($value)
    {
        if ($value instanceof \DateTime) {
            return $value->format(Constants::DATE_FORMAT);
        }

        if (is_numeric($value)) {
            // Excel date serial number
            try {
                $date = \PhpOffice\PhpSpreadsheet\Shared\Date::excelToDateTimeObject($value);
                return $date->format(Constants::DATE_FORMAT);
            } catch (\Exception $e) {
                return false;
            }
        }

        if (is_string($value)) {
            $value = trim($value);
            if ($value === '') {
                return false;
            }

            // Try to parse various date formats
            $formats = ['Y-m-d', 'd/m/Y', 'm/d/Y', 'Y/m/d', 'd-m-Y'];
            foreach ($formats as $format) {
                $date = \DateTime::createFromFormat($format, $value);
                if ($date !== false) {
                    return $date->format(Constants::DATE_FORMAT);
                }
            }

            // Try strtotime as fallback
            $timestamp = strtotime($value);
            if ($timestamp !== false) {
                return date(Constants::DATE_FORMAT, $timestamp);
            }
        }

        return false;
    }

    /**
     * Parse and validate numeric value
     * 
     * @param mixed $value Numeric value from Excel
     * @return float|false Parsed float value or false on failure
     */
    public function parseNumeric($value)
    {
        if (is_numeric($value)) {
            return (float) $value;
        }

        if (is_string($value)) {
            $value = trim($value);
            if ($value === '') {
                return 0.0;
            }

            // Remove common formatting characters
            $value = str_replace(['$', ',', ' '], '', $value);
            
            if (is_numeric($value)) {
                return (float) $value;
            }
        }

        return false;
    }

    /**
     * Parse and validate datetime value
     *
     * @param mixed $value Datetime value from Excel
     * @return string|false Formatted datetime string (Y-m-d H:i:s) or false on failure
     */
    public function parseDateTime($value)
    {
        if ($value instanceof \DateTime) {
            return $value->format('Y-m-d H:i:s');
        }

        if (is_numeric($value)) {
            try {
                $date = \PhpOffice\PhpSpreadsheet\Shared\Date::excelToDateTimeObject($value);
                return $date->format('Y-m-d H:i:s');
            } catch (\Exception $e) {
                return false;
            }
        }

        if (is_string($value)) {
            $value = trim($value);
            if ($value === '') {
                return false;
            }

            $formats = [
                'Y-m-d H:i:s',
                'Y-m-d H:i',
                'd/m/Y H:i:s',
                'd/m/Y H:i',
                'm/d/Y H:i:s',
                'm/d/Y H:i',
                'Y-m-d',
                'd/m/Y',
                'm/d/Y'
            ];
            foreach ($formats as $format) {
                $date = \DateTime::createFromFormat($format, $value);
                if ($date !== false) {
                    return $date->format('Y-m-d H:i:s');
                }
            }

            $timestamp = strtotime($value);
            if ($timestamp !== false) {
                return date('Y-m-d H:i:s', $timestamp);
            }
        }

        return false;
    }

    /**
     * Parse and validate integer value
     *
     * @param mixed $value Integer value from Excel
     * @return int|false Parsed int value or false on failure
     */
    public function parseInteger($value)
    {
        if (is_int($value)) {
            return $value;
        }

        if (is_numeric($value)) {
            return (int) $value;
        }

        if (is_string($value)) {
            $value = trim($value);
            if ($value === '') {
                return false;
            }

            $value = str_replace(['.', ',', ' '], '', $value);
            if (is_numeric($value)) {
                return (int) $value;
            }
        }

        return false;
    }

    /**
     * Get validation errors
     * 
     * @return array Array of error messages
     */
    public function getErrors(): array
    {
        return $this->errors;
    }

    /**
     * Clear validation errors
     */
    public function clearErrors(): void
    {
        $this->errors = [];
    }
}
