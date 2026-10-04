# Import Workflow Documentation

## Detailed Import Process Flow

This document explains the step-by-step workflow of the Excel import system.

## Overview

The import process follows a strict sequence to ensure data integrity and provide detailed feedback:

```
File Upload → Validation → Loading → Processing → Insertion → Reporting
```

## Step-by-Step Workflow

### Phase 1: File Upload & Initial Validation

**Location**: `api/import.php` (lines 50-80)

1. **HTTP Request Validation**
   - Verify request method is POST
   - Check if file was uploaded (`$_FILES['excel_file']`)
   - Validate upload error code (`UPLOAD_ERR_OK`)

2. **File Validation** (`ExcelValidator::validateFile()`)
   - Check file exists and is uploaded file
   - Validate file size against `MAX_FILE_SIZE` (50MB)
   - Check file extension (must be `.xlsx`)
   - Verify MIME type (Excel MIME types)

3. **File Storage**
   - Create uploads directory if not exists
   - Generate unique filename (timestamp + uniqid)
   - Move uploaded file to `uploads/` directory
   - Store original filename for reference

**Error Handling**: If any step fails, file is deleted and error returned to user.

---

### Phase 2: Database Connection & Excel Loading

**Location**: `api/import.php` (lines 82-95), `ExcelProcessor::loadFile()`

1. **Database Connection Test**
   - Test connection using `Database::testConnection()`
   - If fails, delete uploaded file and return error

2. **Excel File Loading**
   - Initialize PhpSpreadsheet Xlsx reader
   - Configure reader for efficiency:
     - `setReadDataOnly(true)` - Skip formatting
     - `setReadEmptyCells(false)` - Skip empty cells
   - Load spreadsheet into memory

3. **Structure Validation** (`ExcelValidator::validateStructure()`)
   - Read header row (row 1)
   - Extract column names
   - Validate column count (must be 12)
   - Validate column order (must match `EXPECTED_COLUMNS`)
   - Validate column names (case-insensitive)

**Error Handling**: If structure is invalid, spreadsheet is cleaned up, file deleted, error returned.

---

### Phase 3: Row-by-Row Processing

**Location**: `ExcelProcessor::processRows()`, `api/import.php` (lines 97-150)

1. **Row Iteration**
   - Start from row 2 (skip header)
   - Iterate through all rows until `getHighestRow()`
   - Track row number for error reporting

2. **Row Reading** (`ExcelProcessor::readRow()`)
   - Read cell values for each expected column
   - Create associative array: `['column_name' => value]`
   - Preserve original data types

3. **Empty Row Detection**
   - Check if all cells in row are empty
   - Skip empty rows (don't count as errors)

4. **Row Validation** (`ExcelValidator::validateRow()`)
   - **Required Fields Check**:
     - `empresa`, `fecha_contabilizacion`, `tipo_documento`, `numero_documento`, `tercero`
     - Must not be empty after trimming
   
   - **Date Validation** (`ExcelValidator::parseDate()`):
     - Handle Excel date serial numbers
     - Parse string dates (multiple formats)
     - Convert to `Y-m-d` format
     - Return false if invalid
   
   - **Numeric Validation** (`ExcelValidator::parseNumeric()`):
     - Parse Excel numeric values
     - Remove formatting ($, commas, spaces)
     - Convert to float
     - Return 0.0 for empty values

5. **Data Normalization** (`ExcelProcessor::normalizeRow()`)
   - Convert dates to standardized format
   - Convert numeric fields to float
   - Trim string fields
   - Ensure all expected columns present

6. **Batch Accumulation**
   - Add normalized row to batch array
   - Continue until batch reaches `BATCH_SIZE` (500 rows)

**Error Handling**: 
- Validation errors are collected with row numbers
- Invalid rows are skipped (not inserted)
- Processing continues for remaining rows

---

### Phase 4: Batch Database Insertion

**Location**: `DatabaseOperations::bulkInsert()`, `api/import.php` (callback)

1. **Transaction Start**
   - Begin database transaction
   - All inserts in batch are atomic

2. **Duplicate Detection** (`DatabaseOperations::isDuplicate()`)
   - For each row, check composite key:
     - `empresa` + `tipo_documento` + `numero_documento` + `fecha_contabilizacion`
   - Query database for existing record
   - Return true if duplicate found

3. **Record Insertion** (`DatabaseOperations::insertRecord()`)
   - Build INSERT statement with placeholders
   - Use prepared statement (SQL injection prevention)
   - Include source filename in insert
   - Execute insert

4. **Error Handling**
   - **Duplicate Error**: Catch and count as duplicate (not error)
   - **SQL Error**: Log and add to error list
   - **Critical Error**: Rollback entire batch

5. **Transaction Commit**
   - If all inserts successful, commit transaction
   - If critical error, rollback entire batch

**Statistics Tracking**:
- Count inserted records
- Count duplicate records
- Collect errors with row numbers

**Memory Management**:
- After each batch, unset batch array
- Periodic garbage collection (every 1000 rows)

---

### Phase 5: Finalization & Reporting

**Location**: `api/import.php` (lines 152-180)

1. **Process Remaining Batch**
   - If batch not empty after loop, process final batch
   - Apply same insertion logic

2. **Resource Cleanup**
   - Disconnect spreadsheet worksheets
   - Unset spreadsheet object
   - Force garbage collection
   - Optionally delete uploaded file (or keep for audit)

3. **Statistics Compilation**
   - Total rows processed
   - Successfully inserted
   - Duplicates found
   - Rejected rows (validation errors + insertion errors)
   - Detailed error list with row numbers

4. **Response Generation**
   - Format JSON response
   - Include all statistics
   - Include error details
   - Return to frontend

---

## Data Flow Diagram

```
┌─────────────┐
│ Excel File  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ File Validation │ ◄─── Extension, MIME, Size
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Load Spreadsheet │ ◄─── PhpSpreadsheet
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Validate Headers │ ◄─── Column count, order, names
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Process Rows   │
│  ┌───────────┐  │
│  │ Read Row  │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Validate  │  │ ◄─── Required fields, dates, numbers
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Normalize │  │ ◄─── Type conversion, formatting
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Add Batch │  │
│  └─────┬─────┘  │
│        │        │
│        ▼        │
│  Batch Full?    │
│        │        │
│    YES │ NO     │
│        │        │
└────┬───┴────────┘
     │
     ▼
┌─────────────────┐
│  Database Insert │
│  ┌───────────┐  │
│  │ Transaction│ │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Duplicate?│  │ ◄─── Composite key check
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │   Insert  │  │ ◄─── Prepared statement
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Commit   │  │
│  └───────────┘  │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  Return Results │ ◄─── Statistics, errors
└─────────────────┘
```

## Error Handling Strategy

### Error Categories

1. **Fatal Errors** (Stop processing):
   - Database connection failure
   - File structure invalid
   - Critical system errors

2. **Row Errors** (Skip row, continue):
   - Validation failures
   - Duplicate records
   - Data type errors

3. **Batch Errors** (Rollback batch):
   - SQL constraint violations
   - Transaction failures

### Error Reporting

- **File-level errors**: Returned immediately, no processing
- **Row-level errors**: Collected, reported in final summary
- **Batch errors**: Logged, batch rolled back, errors reported

### Error Logging

All errors are logged to PHP error log with:
- Timestamp
- Error message
- Stack trace (for exceptions)
- Context (file name, row number, etc.)

## Performance Considerations

### Memory Optimization

- Read-only mode (no formatting data)
- Skip empty cells
- Process row-by-row (not load entire file)
- Unset variables after use
- Periodic garbage collection

### Database Optimization

- Batch inserts (reduce round trips)
- Transactions (atomicity)
- Prepared statements (performance + security)
- Indexes on query columns
- Composite unique key (efficient duplicate check)

### Execution Time

- Set appropriate time limits
- Process in batches
- Allow for large files
- Monitor execution time

## Security Considerations

1. **File Upload Security**:
   - Validate file type (extension + MIME)
   - Limit file size
   - Store in non-web-accessible directory (optional)
   - Generate unique filenames

2. **SQL Injection Prevention**:
   - Prepared statements exclusively
   - Parameter binding
   - No string concatenation in SQL

3. **Input Validation**:
   - Validate all inputs
   - Sanitize file names
   - Validate data types

4. **Error Information**:
   - Don't expose system details to users
   - Log detailed errors server-side
   - Return user-friendly messages

---

**Last Updated**: January 2026
