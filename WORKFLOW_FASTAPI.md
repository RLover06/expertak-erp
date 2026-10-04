# Import Workflow - FastAPI + Svelte Version

## Overview

This document describes the complete workflow of the Excel import system using FastAPI backend and Svelte frontend.

## Architecture Flow

```
User (Browser)
    ↓
Svelte Frontend (Vite Dev Server)
    ↓ HTTP POST
FastAPI Backend (Uvicorn)
    ↓
Excel Validator Service
    ↓
Excel Processor Service
    ↓
Database Service (SQLAlchemy)
    ↓
MariaDB Database
```

## Detailed Workflow

### Phase 1: File Upload (Frontend)

**Location**: `frontend/src/components/FileUpload.svelte`

1. **User Interaction**
   - User selects file via file input or drag-and-drop
   - File is stored in component state

2. **Client-Side Validation**
   - Check file extension (.xlsx)
   - Display file information (name, size)

3. **Pre-Validation Request**
   - Call `/api/v1/import/validate` endpoint
   - Send file as `multipart/form-data`
   - Display validation results

4. **Import Request**
   - User clicks "Iniciar Importación"
   - Call `/api/v1/import/` endpoint
   - Show loading indicator
   - Handle response or errors

### Phase 2: File Validation (Backend)

**Location**: `backend/app/routers/import.py` → `validate` endpoint

1. **Request Reception**
   - FastAPI receives multipart/form-data
   - Extract file from request

2. **File Validation**
   - Check file extension
   - Check file size
   - Save to temporary location

3. **Structure Validation**
   - Load Excel file with openpyxl (read-only mode)
   - Read header row (row 1)
   - Validate column count (must be 12)
   - Validate column order and names
   - Compare with `EXPECTED_COLUMNS`

4. **Response**
   - Return validation result
   - Include column information
   - Include any errors

5. **Cleanup**
   - Delete temporary file

### Phase 3: Import Processing (Backend)

**Location**: `backend/app/routers/import.py` → `import` endpoint

1. **File Reception**
   - Receive file from request
   - Generate unique filename
   - Save to `uploads/` directory

2. **Initial Validation**
   - Validate file structure (same as Phase 2)
   - If invalid, return error immediately

3. **Row Processing Loop**
   - Initialize ExcelProcessor
   - Process file row by row (starting from row 2)
   - For each row:
     - Read cell values
     - Skip empty rows
     - Validate row data (required fields, types)
     - Normalize data (dates, decimals)
     - Add to batch

4. **Batch Processing**
   - When batch reaches `BATCH_SIZE` (500 rows):
     - Start database transaction
     - For each row in batch:
       - Check for duplicates (composite key)
       - Insert if not duplicate
     - Commit transaction
     - Collect statistics

5. **Final Batch**
   - Process remaining rows in batch
   - Commit final transaction

6. **Response Generation**
   - Compile statistics:
     - Total rows processed
     - Successfully inserted
     - Duplicates found
     - Rejected rows with errors
   - Calculate processing time
   - Return JSON response

### Phase 4: Result Display (Frontend)

**Location**: `frontend/src/components/ImportResults.svelte`

1. **Receive Response**
   - Store result in Svelte store
   - Update component state

2. **Display Statistics**
   - Show cards with:
     - Total rows processed
     - Inserted (green)
     - Duplicates (yellow)
     - Rejected (red)

3. **Display Errors**
   - Show error list with:
     - Row number
     - Error messages
   - Scrollable list for many errors

4. **File Information**
   - Display file name
   - Display file size
   - Display processing time

## Data Flow Diagram

```
┌─────────────┐
│ Excel File  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Svelte Frontend │
│  FileUpload     │
└──────┬──────────┘
       │ POST /api/v1/import/validate
       ▼
┌─────────────────┐
│ FastAPI Backend │
│  Validate File  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ ExcelValidator  │
│  - Structure    │
│  - Headers      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Validation      │
│  Response       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ User Confirms   │
│  Import         │
└──────┬──────────┘
       │ POST /api/v1/import/
       ▼
┌─────────────────┐
│ ExcelProcessor  │
│  - Read Rows    │
│  - Validate     │
│  - Normalize    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ DatabaseService │
│  - Batch Insert │
│  - Transactions │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ MariaDB         │
│  documentos_    │
│  contables      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Import Result   │
│  Response       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ ImportResults   │
│  Component      │
└─────────────────┘
```

## Error Handling Flow

### Frontend Errors

1. **Network Errors**
   - Connection timeout
   - Server unavailable
   - Display user-friendly message

2. **Validation Errors**
   - File type invalid
   - Structure invalid
   - Display error details

3. **Import Errors**
   - Processing failed
   - Display error message
   - Show partial results if available

### Backend Errors

1. **File Errors**
   - Invalid file type → 400 Bad Request
   - File too large → 400 Bad Request
   - Corrupted file → 400 Bad Request

2. **Validation Errors**
   - Structure invalid → 400 Bad Request
   - Column mismatch → 400 Bad Request

3. **Processing Errors**
   - Row validation failed → Continue, report in errors
   - Duplicate detected → Count as duplicate, continue
   - Database error → Rollback batch, report error

4. **System Errors**
   - Database connection failed → 500 Internal Server Error
   - Unexpected exception → 500 Internal Server Error
   - Logged with full stack trace

## Performance Considerations

### Frontend

- **File Size**: Client-side validation before upload
- **Progress**: Loading indicators during processing
- **Error Handling**: Graceful error messages

### Backend

- **Memory**: Read-only Excel mode, row-by-row processing
- **Database**: Batch inserts, connection pooling
- **Concurrency**: Async FastAPI handles multiple requests
- **Transactions**: Batch operations for efficiency

### Database

- **Indexes**: On frequently queried columns
- **Composite Key**: Efficient duplicate detection
- **Transactions**: Atomic batch operations

## Security Flow

1. **File Upload**
   - Validate file extension
   - Validate MIME type (if available)
   - Limit file size
   - Generate unique filenames

2. **Data Validation**
   - Pydantic models validate all inputs
   - SQLAlchemy ORM prevents SQL injection
   - Type checking prevents type confusion

3. **Database**
   - Prepared statements (SQLAlchemy)
   - Parameter binding
   - Transaction isolation

4. **Error Messages**
   - No sensitive information exposed
   - Detailed errors logged server-side
   - User-friendly messages to client

## Testing Flow

### Unit Tests

- Test ExcelValidator
- Test ExcelProcessor
- Test DatabaseService
- Test Pydantic schemas

### Integration Tests

- Test file upload endpoint
- Test validation endpoint
- Test import endpoint
- Test error handling

### End-to-End Tests

- Test complete import flow
- Test error scenarios
- Test duplicate detection
- Test large file processing

---

**Last Updated**: January 2026
