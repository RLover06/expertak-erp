# Excel Bulk Import System

A production-ready web-based system for bulk data import from Excel files (.xlsx) into a MariaDB database, built with pure PHP 8.x and vanilla JavaScript.

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Import Workflow](#import-workflow)
- [Error Handling](#error-handling)
- [Performance & Scalability](#performance--scalability)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **File Validation**: Extension, MIME type, and structure validation
- **Column Validation**: Strict column count and order checking
- **Row-by-Row Validation**: Detailed validation with error reporting
- **Bulk Insert**: Efficient batch processing with transactions
- **Duplicate Detection**: Composite business key for preventing duplicates
- **Memory Optimization**: Optimized for large files (thousands of rows)
- **Error Reporting**: Comprehensive error details with row numbers
- **Production Ready**: Defensive programming, error logging, transaction support

## 📦 Requirements

- **PHP**: 8.0 or higher
- **MariaDB**: 10.4 or higher (MySQL 5.7+ compatible)
- **Web Server**: Apache (with mod_rewrite) or Nginx
- **PHP Extensions**:
  - PDO
  - PDO_MySQL
  - mbstring
  - fileinfo
  - zip (for PhpSpreadsheet)
  - xml (for PhpSpreadsheet)
  - gd (optional, for PhpSpreadsheet)

## 🚀 Installation

### 1. Clone or Download the Project

```bash
cd /path/to/your/webroot
# Extract or clone the project
```

### 2. Install Dependencies

```bash
composer install
```

If Composer is not available, manually download PhpSpreadsheet:
- Download from: https://github.com/PHPOffice/PhpSpreadsheet
- Extract to `vendor/phpoffice/phpspreadsheet/`

### 3. Database Setup

```bash
# Connect to MariaDB
mysql -u root -p

# Create database (if not exists)
CREATE DATABASE expertak CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Import table schema
mysql -u root -p expertak < sql/create_import_table.sql
```

### 4. Configure Database Connection

Edit `config/database.php` and update the connection parameters:

```php
private const DB_HOST = 'localhost';
private const DB_NAME = 'expertak';
private const DB_USER = 'your_username';
private const DB_PASS = 'your_password';
```

### 5. Set Permissions

```bash
# Ensure uploads directory is writable
chmod 755 uploads/
chown www-data:www-data uploads/  # Adjust user/group as needed
```

### 6. Web Server Configuration

#### Apache
- Ensure `.htaccess` is in the root directory
- Enable `mod_rewrite`
- Point document root to the project root (or `public/` directory)

#### Nginx
Add to your server configuration:

```nginx
location / {
    try_files $uri $uri/ /public/index.php?$query_string;
}

location ~ ^/(config|includes|sql|uploads)/ {
    deny all;
}
```

## ⚙️ Configuration

### File Upload Limits

Edit `config/constants.php` to adjust:

```php
public const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
public const BATCH_SIZE = 500; // Rows per transaction
public const MAX_EXECUTION_TIME = 300; // 5 minutes
public const MEMORY_LIMIT = '512M';
```

### Excel Structure

The system expects exactly these columns in this order:

1. empresa
2. fecha_contabilizacion
3. tipo_documento
4. numero_documento
5. tercero
6. subtotal
7. iva
8. ica
9. inc
10. timbre
11. otros_impuestos
12. total

**Important**: The first row must contain these exact column headers.

## 📖 Usage

### Web Interface

1. Open `http://your-domain/public/index.php` in a browser
2. Click "Seleccionar archivo Excel (.xlsx)"
3. Select your Excel file
4. Click "Iniciar Importación"
5. Review the import results

### API Endpoint

```bash
POST /api/import.php
Content-Type: multipart/form-data

Form Data:
- excel_file: [Excel file]
```

**Response Example:**

```json
{
    "success": true,
    "message": "Import completed successfully",
    "data": {
        "file_name": "data.xlsx",
        "file_size": 123456,
        "total_rows": 1000,
        "inserted": 950,
        "duplicates": 30,
        "rejected": 20,
        "errors": [
            {
                "row": 5,
                "error": "Required field 'empresa' is empty."
            }
        ]
    }
}
```

## 📁 Project Structure

```
expertak/
├── api/
│   └── import.php              # Main import API endpoint
├── config/
│   ├── database.php            # Database configuration
│   └── constants.php           # Application constants
├── includes/
│   ├── autoload.php            # PSR-4 autoloader
│   ├── ExcelValidator.php      # File and row validation
│   ├── ExcelProcessor.php      # Excel reading and processing
│   └── DatabaseOperations.php  # Database operations
├── public/
│   ├── index.php               # Frontend interface
│   ├── styles.css              # Stylesheet
│   └── script.js               # Frontend JavaScript
├── sql/
│   └── create_import_table.sql # Database schema
├── uploads/                    # Uploaded files directory
├── vendor/                     # Composer dependencies
├── .htaccess                   # Apache configuration
├── .gitignore                  # Git ignore rules
├── composer.json               # Composer dependencies
└── README.md                   # This file
```

## 🔄 Import Workflow

### 1. File Upload
- User selects Excel file via web form
- File is validated (extension, MIME type, size)
- File is moved to `uploads/` directory

### 2. File Loading
- PhpSpreadsheet loads the Excel file
- Structure validation (column count and order)
- Header row validation

### 3. Row Processing
- Process rows starting from row 2 (skip header)
- For each row:
  - Read data from Excel
  - Validate required fields
  - Parse and normalize data (dates, numbers)
  - Add to batch

### 4. Batch Insertion
- When batch reaches `BATCH_SIZE` (500 rows):
  - Start database transaction
  - Check for duplicates (composite key)
  - Insert valid records
  - Commit transaction
  - Report errors

### 5. Finalization
- Process remaining batch
- Generate statistics
- Return results to user
- Clean up resources

### Duplicate Detection

Duplicates are detected using a composite business key:
- `empresa` + `tipo_documento` + `numero_documento` + `fecha_contabilizacion`

If a record with the same combination exists, it's marked as duplicate and not inserted.

## ⚠️ Error Handling

### Validation Errors

**File Level:**
- Invalid file type (not .xlsx)
- Invalid MIME type
- File too large
- Upload failure

**Structure Level:**
- Column count mismatch
- Column order mismatch
- Missing header row

**Row Level:**
- Empty required fields
- Invalid date format
- Invalid numeric values
- Duplicate records

### Error Reporting

Errors are reported with:
- Row number
- Error message
- Field name (when applicable)

All errors are logged to PHP error log for debugging.

### Transaction Safety

- Each batch is wrapped in a transaction
- On critical error, entire batch is rolled back
- Individual row errors don't affect the batch
- Database integrity is maintained

## 🚀 Performance & Scalability

### Optimizations

1. **Memory Management**:
   - `setReadDataOnly(true)` - Skip formatting data
   - `setReadEmptyCells(false)` - Skip empty cells
   - Periodic garbage collection
   - Unset variables after use

2. **Database Operations**:
   - Batch inserts (500 rows per transaction)
   - Prepared statements (SQL injection prevention)
   - Indexes on frequently queried columns
   - Composite unique key for duplicate detection

3. **Processing**:
   - Row-by-row processing (not loading entire file)
   - Early validation (fail fast)
   - Efficient date/number parsing

### Scalability Recommendations

1. **For Very Large Files (100K+ rows)**:
   - Increase `BATCH_SIZE` to 1000-2000
   - Increase `MAX_EXECUTION_TIME` to 600+ seconds
   - Increase `MEMORY_LIMIT` to 1G+
   - Consider queue-based processing

2. **For High Concurrency**:
   - Implement file locking
   - Use database connection pooling
   - Consider Redis for duplicate checking
   - Implement rate limiting

3. **For Production**:
   - Enable OPcache
   - Use CDN for static assets
   - Implement caching for validation rules
   - Monitor error logs
   - Set up database replication

## 🔧 Troubleshooting

### Common Issues

**1. "Database connection failed"**
- Check database credentials in `config/database.php`
- Verify database server is running
- Check firewall rules

**2. "File upload failed"**
- Check `upload_max_filesize` in php.ini
- Check `post_max_size` in php.ini
- Verify `uploads/` directory permissions
- Check disk space

**3. "Column count mismatch"**
- Verify Excel file has exactly 12 columns
- Check header row matches expected structure
- Ensure no merged cells in header row

**4. "Memory limit exceeded"**
- Increase `memory_limit` in php.ini
- Reduce `BATCH_SIZE` in constants.php
- Process smaller files

**5. "Execution time exceeded"**
- Increase `max_execution_time` in php.ini
- Increase `MAX_EXECUTION_TIME` in constants.php
- Process files in smaller batches

### Debug Mode

To enable detailed error messages, edit `api/import.php`:

```php
ini_set('display_errors', 1); // Change from 0 to 1
```

**Warning**: Disable in production!

### Logging

Check PHP error log for detailed error messages:
- Linux: `/var/log/php/error.log` or `/var/log/apache2/error.log`
- Windows: Check php.ini `error_log` directive
- cPanel: Usually in `~/logs/error_log`

## 📝 License

This project is provided as-is for use in the Expertak system.

## 👥 Support

For issues or questions:
1. Check error logs
2. Review this documentation
3. Verify configuration settings
4. Test with a small sample file first

---

**Version**: 1.0.0  
**Last Updated**: January 2026
