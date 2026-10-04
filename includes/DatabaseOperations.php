<?php
/**
 * Database Operations
 * 
 * Handles all database operations for bulk import
 * Uses transactions and prepared statements for data integrity
 * 
 * @package Expertak\Includes
 */

namespace Expertak\Includes;

use PDO;
use PDOException;
use Expertak\Config\Database;
use Expertak\Config\Constants;

/**
 * Database operations class
 */
class DatabaseOperations
{
    /**
     * @var PDO Database connection
     */
    private PDO $db;

    /**
     * Constructor
     */
    public function __construct()
    {
        $this->db = Database::getConnection();
    }

    /**
     * Check if record already exists (duplicate detection)
     * 
     * @param array $row Row data
     * @return bool True if duplicate exists
     */
    public function isDuplicate(array $row): bool
    {
        $keyColumns = Constants::DUPLICATE_KEY_COLUMNS;
        $conditions = [];
        $params = [];

        foreach ($keyColumns as $column) {
            if (!isset($row[$column])) {
                return false; // Incomplete key, cannot be duplicate
            }
            $conditions[] = "`{$column}` = :{$column}";
            $params[":{$column}"] = $row[$column];
        }

        $sql = "SELECT COUNT(*) FROM `" . Constants::TABLE_NAME . "` WHERE " . implode(' AND ', $conditions);
        
        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            $count = $stmt->fetchColumn();
            return $count > 0;
        } catch (PDOException $e) {
            error_log("DatabaseOperations::isDuplicate error: " . $e->getMessage());
            throw new \Exception("Duplicate check failed: " . $e->getMessage());
        }
    }

    /**
     * Insert a single record
     * 
     * @param array $row Row data
     * @param string|null $sourceFileName Source file name
     * @return bool True if inserted successfully
     * @throws \Exception If insertion fails
     */
    public function insertRecord(array $row, ?string $sourceFileName = null): bool
    {
        // Check for duplicate
        if ($this->isDuplicate($row)) {
            throw new \Exception(Constants::ERROR_DUPLICATE_RECORD);
        }

        $columns = Constants::EXPECTED_COLUMNS;
        $placeholders = [];
        $params = [];

        // Build placeholders and parameters
        foreach ($columns as $column) {
            $placeholders[] = ":{$column}";
            $params[":{$column}"] = $row[$column] ?? null;
        }

        // Add source file name if provided
        if ($sourceFileName !== null) {
            $columns[] = 'archivo_origen';
            $placeholders[] = ":archivo_origen";
            $params[":archivo_origen"] = $sourceFileName;
        }

        $sql = sprintf(
            "INSERT INTO `%s` (`%s`) VALUES (%s)",
            Constants::TABLE_NAME,
            implode('`, `', $columns),
            implode(', ', $placeholders)
        );

        try {
            $stmt = $this->db->prepare($sql);
            return $stmt->execute($params);
        } catch (PDOException $e) {
            error_log("DatabaseOperations::insertRecord error: " . $e->getMessage());
            
            // Check if it's a duplicate key error
            if ($e->getCode() == 23000) { // SQLSTATE 23000: Integrity constraint violation
                throw new \Exception(Constants::ERROR_DUPLICATE_RECORD);
            }
            
            throw new \Exception("Insert failed: " . $e->getMessage());
        }
    }

    /**
     * Bulk insert records using transactions
     * 
     * @param array $rows Array of row data arrays
     * @param string|null $sourceFileName Source file name
     * @return array Statistics: ['inserted' => int, 'duplicates' => int, 'errors' => array]
     */
    public function bulkInsert(array $rows, ?string $sourceFileName = null): array
    {
        $stats = [
            'inserted' => 0,
            'duplicates' => 0,
            'errors' => []
        ];

        if (empty($rows)) {
            return $stats;
        }

        // Start transaction
        $this->db->beginTransaction();

        try {
            foreach ($rows as $index => $row) {
                try {
                    if ($this->insertRecord($row, $sourceFileName)) {
                        $stats['inserted']++;
                    }
                } catch (\Exception $e) {
                    if (strpos($e->getMessage(), Constants::ERROR_DUPLICATE_RECORD) !== false) {
                        $stats['duplicates']++;
                    } else {
                        $stats['errors'][] = [
                            'row_index' => $index,
                            'error' => $e->getMessage()
                        ];
                    }
                }
            }

            // Commit transaction
            $this->db->commit();
        } catch (\Exception $e) {
            // Rollback on critical error
            $this->db->rollBack();
            error_log("DatabaseOperations::bulkInsert transaction failed: " . $e->getMessage());
            throw new \Exception("Bulk insert transaction failed: " . $e->getMessage());
        }

        return $stats;
    }

    /**
     * Get import statistics for a file
     * 
     * @param string $fileName Source file name
     * @return array Statistics
     */
    public function getImportStats(string $fileName): array
    {
        $sql = "SELECT 
                    COUNT(*) as total_records,
                    MIN(fecha_importacion) as first_import,
                    MAX(fecha_importacion) as last_import
                FROM `" . Constants::TABLE_NAME . "`
                WHERE archivo_origen = :filename";

        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute([':filename' => $fileName]);
            return $stmt->fetch(PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            error_log("DatabaseOperations::getImportStats error: " . $e->getMessage());
            return [];
        }
    }

    /**
     * Test database connection
     * 
     * @return bool True if connection is working
     */
    public function testConnection(): bool
    {
        try {
            $this->db->query("SELECT 1");
            return true;
        } catch (PDOException $e) {
            return false;
        }
    }
}
