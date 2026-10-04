<?php
/**
 * Database Configuration and Connection Class
 * 
 * Pure PHP implementation for MariaDB connection
 * Compatible with shared hosting (cPanel) environments
 * 
 * @package Expertak\Config
 */

namespace Expertak\Config;

use PDO;
use PDOException;

/**
 * Database configuration and connection handler
 */
class Database
{
    /**
     * @var PDO|null Singleton database connection instance
     */
    private static ?PDO $connection = null;

    /**
     * Database configuration
     * 
     * IMPORTANT: Update these values for your environment
     * For production, use environment variables or a separate config file
     */
    private const DB_HOST = '127.0.0.1';
    private const DB_PORT = '3306';
    private const DB_NAME = 'expertak';
    private const DB_USER = 'root';
    private const DB_PASS = ''; // set your local password
    private const DB_CHARSET = 'utf8mb4';

    /**
     * Get database connection (singleton pattern)
     * 
     * @return PDO Database connection instance
     * @throws PDOException If connection fails
     */
    public static function getConnection(): PDO
    {
        if (self::$connection === null) {
            self::$connection = self::createConnection();
        }

        return self::$connection;
    }

    /**
     * Create a new database connection
     * 
     * @return PDO Database connection instance
     * @throws PDOException If connection fails
     */
    private static function createConnection(): PDO
    {
        $dsn = sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=%s',
            self::DB_HOST,
            self::DB_PORT,
            self::DB_NAME,
            self::DB_CHARSET
        );

        $options = [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false, // Use native prepared statements
            PDO::MYSQL_ATTR_INIT_COMMAND => "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"
        ];

        try {
            $pdo = new PDO($dsn, self::DB_USER, self::DB_PASS, $options);
            return $pdo;
        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw new PDOException(
                "Database connection failed. Please check your configuration.",
                0,
                $e
            );
        }
    }

    /**
     * Close database connection
     */
    public static function closeConnection(): void
    {
        self::$connection = null;
    }

    /**
     * Test database connection
     * 
     * @return bool True if connection is successful
     */
    public static function testConnection(): bool
    {
        try {
            $conn = self::getConnection();
            $conn->query("SELECT 1");
            return true;
        } catch (PDOException $e) {
            return false;
        }
    }
}
