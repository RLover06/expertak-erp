# Error Handling Strategy

## Overview

This document describes the comprehensive error handling strategy implemented in the Excel import system. The system follows defensive programming principles to ensure reliability and provide clear feedback.

## Error Handling Philosophy

1. **Fail Fast**: Detect errors early, before processing
2. **Fail Safe**: Never corrupt data, always maintain database integrity
3. **Clear Feedback**: Provide detailed, actionable error messages
4. **Log Everything**: Record all errors for debugging and auditing
5. **Graceful Degradation**: Continue processing valid rows when possible

## Error Categories

### 1. File Upload Errors

**Location**: `ExcelValidator::validateFile()`, `api/import.php`

**Errors**:
- `UPLOAD_ERR_NO_FILE`: No file uploaded
- `UPLOAD_ERR_INI_SIZE`: File exceeds `upload_max_filesize`
- `UPLOAD_ERR_FORM_SIZE`: File exceeds `MAX_FILE_SIZE`
- `UPLOAD_ERR_PARTIAL`: File partially uploaded
- `UPLOAD_ERR_NO_TMP_DIR`: Missing temporary directory
- `UPLOAD_ERR_CANT_WRITE`: Cannot write file
- Invalid file extension (not .xlsx)
- Invalid MIME type
- File too large

**Handling**:
- Return error immediately
- Do not process file
- Delete uploaded file if exists
- Return user-friendly message

**Example Response**:
```json
{
    "success": false,
    "message": "File validation failed",
    "details": ["Invalid file type. Only .xlsx files are allowed."]
}
```

---

### 2. File Structure Errors

**Location**: `ExcelValidator::validateStructure()`

**Errors**:
- Column count mismatch (not 12 columns)
- Column order mismatch
- Column name mismatch
- Missing header row
- Corrupted Excel file

**Handling**:
- Validate before processing any rows
- Return error immediately
- Clean up spreadsheet resources
- Delete uploaded file
- Provide expected structure in error message

**Example Response**:
```json
{
    "success": false,
    "message": "Invalid Excel structure: Column count does not match expected structure. Expected 12 columns, found 10.",
    "details": []
}
```

---

### 3. Row Validation Errors

**Location**: `ExcelValidator::validateRow()`

**Errors**:
- Empty required fields:
  - `empresa`
  - `fecha_contabilizacion`
  - `tipo_documento`
  - `numero_documento`
  - `tercero`
- Invalid date format for `fecha_contabilizacion`
- Invalid numeric values for:
  - `subtotal`, `iva`, `ica`, `inc`, `timbre`, `otros_impuestos`, `total`

**Handling**:
- Collect errors per row
- Skip invalid rows (don't insert)
- Continue processing remaining rows
- Report errors in final summary with row numbers

**Example Error Entry**:
```json
{
    "row": 5,
    "errors": ["Row 5: Required field 'empresa' is empty.", "Row 5: Invalid date format for 'fecha_contabilizacion': 2025-13-45"]
}
```

---

### 4. Database Errors

**Location**: `DatabaseOperations::insertRecord()`, `DatabaseOperations::bulkInsert()`

**Errors**:
- Duplicate record (composite key violation)
- SQL constraint violations
- Connection failures
- Transaction failures
- Prepared statement errors

**Handling**:

**Duplicates**:
- Detected before insert (query) or during insert (unique constraint)
- Not treated as error, counted separately
- Row skipped, processing continues

**SQL Errors**:
- Logged with full details
- Row added to error list
- Batch continues (other rows still processed)

**Transaction Failures**:
- Entire batch rolled back
- All rows in batch added to errors
- Processing stops for that batch
- Remaining batches still processed

**Example Error Entry**:
```json
{
    "row": 42,
    "error": "Duplicate record detected (already exists in database)."
}
```

---

### 5. System Errors

**Location**: `api/import.php` (try-catch blocks)

**Errors**:
- Memory exhaustion
- Execution time exceeded
- PHP fatal errors
- Unexpected exceptions

**Handling**:
- Caught by top-level try-catch
- Logged with stack trace
- Resources cleaned up
- User-friendly error returned
- Uploaded file deleted

**Example Response**:
```json
{
    "success": false,
    "message": "Internal server error: Memory limit exceeded",
    "details": []
}
```

---

## Error Reporting Structure

### Frontend Display

Errors are displayed in three categories:

1. **Statistics Cards**:
   - Total rows processed
   - Successfully inserted (green)
   - Duplicates found (yellow)
   - Rejected rows (red)

2. **Error Details Section**:
   - Expandable list of all errors
   - Row number for each error
   - Error message(s)
   - Grouped by row

3. **Success/Error Messages**:
   - Top-level message
   - Color-coded (green/yellow/red)

### API Response Structure

```json
{
    "success": true|false,
    "message": "Human-readable message",
    "data": {
        "file_name": "example.xlsx",
        "file_size": 123456,
        "total_rows": 1000,
        "inserted": 950,
        "duplicates": 30,
        "rejected": 20,
        "errors": [
            {
                "row": 5,
                "errors": ["Error message 1", "Error message 2"]
            },
            {
                "row": 42,
                "error": "Single error message"
            }
        ]
    },
    "details": []  // Additional error details (for validation errors)
}
```

---

## Error Logging

### Log Format

All errors are logged to PHP error log with:

```
[Timestamp] Error Type: Error Message
Context: File: filename.xlsx, Row: 42
Stack Trace: [if exception]
```

### Log Locations

- **Linux**: `/var/log/php/error.log` or `/var/log/apache2/error.log`
- **Windows**: Check `php.ini` `error_log` directive
- **cPanel**: `~/logs/error_log` or `~/public_html/logs/error_log`

### Logging Levels

1. **Error**: Validation failures, SQL errors
2. **Warning**: Duplicates, skipped rows
3. **Info**: Import start, completion, statistics

---

## Error Recovery Strategies

### 1. Partial Import Recovery

**Scenario**: Some rows fail validation, others succeed

**Strategy**:
- Continue processing valid rows
- Report failed rows in summary
- User can fix Excel file and re-import only failed rows

### 2. Batch Failure Recovery

**Scenario**: Entire batch fails (transaction rollback)

**Strategy**:
- Batch rolled back (no partial data)
- Errors reported for all rows in batch
- Remaining batches still processed
- User can retry import after fixing issues

### 3. System Failure Recovery

**Scenario**: Server crash, memory exhaustion, timeout

**Strategy**:
- Transaction ensures no partial data
- Error logged with details
- User receives error message
- Can retry import after resolving issue

---

## Defensive Programming Practices

### 1. Input Validation

- **File Level**: Extension, MIME, size
- **Structure Level**: Column count, order, names
- **Row Level**: Required fields, data types, formats
- **Database Level**: Prepared statements, type checking

### 2. Resource Management

- **File Handles**: Always closed
- **Database Connections**: Singleton pattern, proper cleanup
- **Memory**: Unset variables, garbage collection
- **Spreadsheet**: Disconnect worksheets after use

### 3. Transaction Safety

- **Atomicity**: Batch operations in transactions
- **Rollback**: On any critical error
- **Isolation**: Each batch independent
- **Durability**: Committed data persisted

### 4. Error Propagation

- **Exceptions**: Caught at appropriate levels
- **Errors**: Logged and returned to user
- **Warnings**: Logged but don't stop processing
- **Silent Failures**: Never allowed

---

## Testing Error Scenarios

### Test Cases

1. **Invalid File Type**:
   - Upload .xls, .csv, .pdf
   - Expected: Rejected with clear message

2. **Wrong Column Count**:
   - Excel with 10 columns
   - Expected: Structure validation error

3. **Missing Required Fields**:
   - Row with empty `empresa`
   - Expected: Row rejected, others processed

4. **Invalid Dates**:
   - Date: "2025-13-45"
   - Expected: Row rejected with date error

5. **Duplicate Records**:
   - Import same file twice
   - Expected: Second import shows duplicates

6. **Large File**:
   - 10,000+ rows
   - Expected: Processed in batches, no memory issues

7. **Database Connection Failure**:
   - Stop database server
   - Expected: Connection error, no processing

---

## Best Practices

1. **Always validate before processing**
2. **Use transactions for batch operations**
3. **Log all errors with context**
4. **Provide clear, actionable error messages**
5. **Never expose system internals to users**
6. **Clean up resources even on errors**
7. **Test error scenarios thoroughly**
8. **Monitor error logs regularly**

---

## Error Message Guidelines

### User-Facing Messages

- **Clear**: Use plain language
- **Actionable**: Tell user what to do
- **Specific**: Include relevant details (row number, field name)
- **Professional**: No technical jargon

**Good Examples**:
- "Row 5: Required field 'empresa' is empty."
- "Invalid file type. Only .xlsx files are allowed."
- "File structure invalid. Expected 12 columns, found 10."

**Bad Examples**:
- "Error occurred."
- "SQLSTATE[23000]: Integrity constraint violation"
- "Fatal error: Call to undefined function"

### Developer-Facing Messages (Logs)

- **Detailed**: Include stack traces
- **Contextual**: File name, row number, values
- **Technical**: Include error codes, SQL queries
- **Complete**: Full exception details

---

**Last Updated**: January 2026
