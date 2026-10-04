# System Architecture

## Overview

The Excel Bulk Import System follows a layered architecture with clear separation of concerns:

```
Presentation Layer (Frontend)
    ↓
API Layer (Controller)
    ↓
Business Logic Layer (Services)
    ↓
Data Access Layer (Database)
```

## Architecture Layers

### 1. Presentation Layer

**Location**: `public/`

**Components**:
- `index.php` - Main HTML interface
- `styles.css` - Styling
- `script.js` - Client-side JavaScript

**Responsibilities**:
- User interface rendering
- File upload handling
- Form validation (client-side)
- Result display
- User feedback

**Technologies**:
- HTML5
- CSS3
- Vanilla JavaScript (ES6+)
- Fetch API

---

### 2. API Layer

**Location**: `api/import.php`

**Responsibilities**:
- HTTP request handling
- File upload processing
- Request validation
- Response formatting
- Error handling
- Resource management

**Key Functions**:
- `sendResponse()` - JSON response formatting
- `sendError()` - Error response
- `sendSuccess()` - Success response

**Security**:
- Input validation
- File type checking
- Error message sanitization
- Resource cleanup

---

### 3. Business Logic Layer

**Location**: `includes/`

#### 3.1 Excel Validator (`ExcelValidator.php`)

**Responsibilities**:
- File validation (extension, MIME, size)
- Structure validation (columns, headers)
- Row validation (required fields, data types)
- Data parsing (dates, numbers)

**Key Methods**:
- `validateFile()` - File-level validation
- `validateStructure()` - Excel structure validation
- `validateRow()` - Row-level validation
- `parseDate()` - Date parsing and validation
- `parseNumeric()` - Numeric parsing and validation

#### 3.2 Excel Processor (`ExcelProcessor.php`)

**Responsibilities**:
- Excel file loading
- Row-by-row reading
- Data normalization
- Memory management
- Resource cleanup

**Key Methods**:
- `loadFile()` - Load Excel file
- `processRows()` - Process all rows with callback
- `readRow()` - Read single row
- `normalizeRow()` - Normalize row data
- `cleanup()` - Resource cleanup

**Optimizations**:
- Read-only mode (no formatting)
- Skip empty cells
- Row-by-row processing
- Periodic garbage collection

#### 3.3 Database Operations (`DatabaseOperations.php`)

**Responsibilities**:
- Database connection management
- Duplicate detection
- Record insertion
- Batch operations
- Transaction management

**Key Methods**:
- `isDuplicate()` - Check for duplicates
- `insertRecord()` - Insert single record
- `bulkInsert()` - Batch insert with transactions
- `getImportStats()` - Get import statistics

**Features**:
- Prepared statements (SQL injection prevention)
- Transaction support (atomicity)
- Composite key duplicate detection
- Error handling and logging

---

### 4. Configuration Layer

**Location**: `config/`

#### 4.1 Database Configuration (`database.php`)

**Responsibilities**:
- Database connection management
- Connection pooling (singleton pattern)
- Connection testing
- UTF-8 encoding setup

**Key Features**:
- PDO connection
- Error handling
- UTF-8 support
- Connection reuse

#### 4.2 Constants (`constants.php`)

**Responsibilities**:
- Application-wide constants
- Configuration values
- Error messages
- Excel structure definition

**Key Constants**:
- File upload limits
- Batch size
- Execution time limits
- Expected columns
- Duplicate key definition

---

### 5. Data Access Layer

**Location**: Database (MariaDB)

**Components**:
- `documentos_contables` table
- Indexes
- Constraints
- Transactions

**Schema**:
```sql
CREATE TABLE documentos_contables (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    empresa VARCHAR(255) NOT NULL,
    fecha_contabilizacion DATE NOT NULL,
    tipo_documento VARCHAR(100) NOT NULL,
    numero_documento VARCHAR(100) NOT NULL,
    tercero VARCHAR(255) NOT NULL,
    subtotal DECIMAL(15,2) DEFAULT 0.00,
    iva DECIMAL(15,2) DEFAULT 0.00,
    ica DECIMAL(15,2) DEFAULT 0.00,
    inc DECIMAL(15,2) DEFAULT 0.00,
    timbre DECIMAL(15,2) DEFAULT 0.00,
    otros_impuestos DECIMAL(15,2) DEFAULT 0.00,
    total DECIMAL(15,2) DEFAULT 0.00,
    fecha_importacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archivo_origen VARCHAR(255),
    UNIQUE KEY (empresa, tipo_documento, numero_documento, fecha_contabilizacion),
    INDEX idx_empresa (empresa),
    INDEX idx_fecha_contabilizacion (fecha_contabilizacion),
    INDEX idx_tercero (tercero)
);
```

---

## Data Flow

### Import Process Flow

```
1. User uploads file
   ↓
2. Frontend validates (client-side)
   ↓
3. POST request to api/import.php
   ↓
4. File validation (ExcelValidator)
   ↓
5. Excel loading (ExcelProcessor)
   ↓
6. Structure validation (ExcelValidator)
   ↓
7. Row processing loop:
   ├─ Read row (ExcelProcessor)
   ├─ Validate row (ExcelValidator)
   ├─ Normalize data (ExcelProcessor)
   └─ Add to batch
   ↓
8. Batch full? → Database insert (DatabaseOperations)
   ↓
9. Process remaining batch
   ↓
10. Generate statistics
   ↓
11. Return JSON response
   ↓
12. Display results (Frontend)
```

---

## Design Patterns

### 1. Singleton Pattern

**Used in**: `Database` class

**Purpose**: Ensure single database connection instance

**Implementation**:
```php
private static ?PDO $connection = null;

public static function getConnection(): PDO {
    if (self::$connection === null) {
        self::$connection = self::createConnection();
    }
    return self::$connection;
}
```

### 2. Strategy Pattern

**Used in**: Validation and processing

**Purpose**: Different validation strategies for different data types

**Implementation**:
- `parseDate()` - Date parsing strategy
- `parseNumeric()` - Numeric parsing strategy
- Different validators for different field types

### 3. Template Method Pattern

**Used in**: Batch processing

**Purpose**: Define algorithm skeleton, defer steps to subclasses

**Implementation**:
- `processRows()` defines the algorithm
- Callback function handles row-specific logic

### 4. Factory Pattern

**Used in**: PDO connection creation

**Purpose**: Create database connections

**Implementation**:
- `createConnection()` creates PDO instances
- Centralized configuration

---

## Security Architecture

### 1. Input Validation

**Layers**:
- Client-side (JavaScript)
- Server-side (PHP)
- Database (Constraints)

**Validations**:
- File type (extension + MIME)
- File size
- Column structure
- Data types
- Required fields

### 2. SQL Injection Prevention

**Mechanism**: Prepared statements exclusively

**Implementation**:
```php
$stmt = $this->db->prepare($sql);
$stmt->execute($params);
```

**No string concatenation in SQL queries**

### 3. File Upload Security

**Measures**:
- File type validation
- MIME type checking
- Size limits
- Unique filenames
- Secure storage location

### 4. Error Handling

**Strategy**:
- Don't expose system internals
- Log detailed errors server-side
- Return user-friendly messages
- No sensitive data in responses

---

## Performance Architecture

### 1. Memory Optimization

**Strategies**:
- Read-only Excel mode
- Skip empty cells
- Row-by-row processing
- Variable cleanup
- Garbage collection

**Implementation**:
```php
$reader->setReadDataOnly(true);
$reader->setReadEmptyCells(false);
unset($rowData);
gc_collect_cycles();
```

### 2. Database Optimization

**Strategies**:
- Batch inserts (reduce round trips)
- Transactions (atomicity)
- Prepared statements (performance)
- Indexes (query speed)
- Composite keys (duplicate detection)

**Implementation**:
- Batch size: 500 rows
- Transaction per batch
- Indexes on query columns

### 3. Execution Time Management

**Strategies**:
- Set appropriate time limits
- Process in batches
- Early validation (fail fast)
- Efficient algorithms

**Configuration**:
- `MAX_EXECUTION_TIME`: 300 seconds
- `BATCH_SIZE`: 500 rows
- Time limit per batch

---

## Scalability Considerations

### Horizontal Scaling

**Challenges**:
- File uploads
- Database connections
- Concurrent imports

**Solutions**:
- File locking
- Connection pooling
- Queue system (future)

### Vertical Scaling

**Optimizations**:
- Increase batch size
- Increase memory limit
- Increase execution time
- Optimize database queries

### Database Scaling

**Strategies**:
- Read replicas
- Partitioning
- Caching
- Index optimization

---

## Error Handling Architecture

### Error Categories

1. **Fatal Errors**: Stop processing
2. **Row Errors**: Skip row, continue
3. **Batch Errors**: Rollback batch
4. **System Errors**: Log and return

### Error Propagation

```
Exception thrown
    ↓
Caught at appropriate layer
    ↓
Logged (server-side)
    ↓
Formatted (user-friendly)
    ↓
Returned to user
```

### Error Recovery

- **Partial Import**: Continue with valid rows
- **Batch Failure**: Rollback batch, continue
- **System Failure**: Log, return error, allow retry

---

## Testing Architecture

### Unit Testing (Recommended)

**Test Targets**:
- `ExcelValidator` - Validation logic
- `ExcelProcessor` - Processing logic
- `DatabaseOperations` - Database operations

### Integration Testing

**Test Scenarios**:
- End-to-end import
- Error handling
- Duplicate detection
- Large file processing

### Performance Testing

**Metrics**:
- Import speed (rows/second)
- Memory usage
- Execution time
- Database load

---

## Deployment Architecture

### Development Environment

- Local PHP server
- Local MariaDB
- Debug mode enabled
- Detailed error messages

### Production Environment

- Web server (Apache/Nginx)
- Production database
- Error logging only
- Optimized settings
- Security hardening

### Shared Hosting (cPanel)

- Compatible with cPanel
- Uses `.htaccess` for configuration
- No server access required
- Standard PHP extensions

---

## Maintenance Architecture

### Logging

**Locations**:
- PHP error log
- Application logs (future)
- Database logs

**Information**:
- Errors with context
- Performance metrics
- User actions

### Monitoring

**Metrics**:
- Import success rate
- Error frequency
- Processing time
- Database performance

### Backup Strategy

**Backup**:
- Database (regular backups)
- Uploaded files (optional)
- Configuration files

---

## Future Enhancements

### Potential Additions

1. **Queue System**: Process large files asynchronously
2. **Progress Tracking**: Real-time import progress
3. **Email Notifications**: Notify on completion
4. **Import History**: Track all imports
5. **Rollback Feature**: Undo imports
6. **Export Feature**: Export data to Excel
7. **API Authentication**: Secure API endpoints
8. **Multi-file Upload**: Upload multiple files
9. **Scheduled Imports**: Automated imports
10. **Data Transformation**: Custom field mappings

---

**Last Updated**: January 2026
