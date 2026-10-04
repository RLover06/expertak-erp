# Excel Bulk Import System - FastAPI + Svelte

A modern, production-ready web-based system for bulk data import from Excel files (.xlsx) into a MariaDB database.

## 🏗️ Architecture

- **Frontend**: Svelte 4 with Vite
- **Backend**: Python 3.11 with FastAPI
- **Database**: MariaDB 10.11+
- **Excel Processing**: openpyxl
- **API Communication**: REST (JSON)
- **Deployment**: Docker-ready, production-grade

## ✨ Features

- **Modern Frontend**: Svelte-based UI with drag-and-drop file upload
- **FastAPI Backend**: High-performance async API with automatic documentation
- **Strict Validation**: File structure, column order, and data type validation
- **Bulk Processing**: Efficient batch inserts with transactions
- **Duplicate Detection**: Composite business key prevention
- **Error Reporting**: Detailed error messages with row numbers
- **CRUD Foundation**: List, create, update, and delete endpoints
- **Progress Tracking**: Real-time import progress
- **Production Ready**: Docker support, logging, error handling

## 📋 Requirements

- Python 3.11+
- Node.js 20+
- MariaDB 10.11+ (or MySQL 5.7+)
- Docker & Docker Compose (optional, for containerized deployment)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone or navigate to project directory
cd expertak

# Start all services
docker-compose up -d

# Access frontend
# http://localhost

# Access backend API docs
# http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Create database
mysql -u root -p
CREATE DATABASE expertak CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit

# Import schema
mysql -u root -p expertak < sql/schema.sql

# Run migrations (if using Alembic)
# alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL (optional)
# Create .env file:
# VITE_API_URL=http://localhost:8000/api/v1

# Start development server
npm run dev

# Build for production
npm run build
```

## 📁 Project Structure

```
expertak/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py         # Database connection
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── errors.py           # Centralized error handling
│   │   ├── repositories/       # Data access layer
│   │   │   └── documento_repository.py
│   │   ├── routers/
│   │   │   ├── import.py       # Import endpoints
│   │   │   ├── documentos.py   # CRUD endpoints
│   │   │   └── health.py       # Health check
│   │   └── services/
│   │       ├── excel_validator.py
│   │       ├── excel_processor.py
│   │       ├── database_service.py
│   │       └── documento_service.py
│   ├── sql/
│   │   └── schema.sql          # Database schema
│   ├── uploads/                # Uploaded files
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.svelte
│   │   ├── main.js
│   │   ├── components/
│   │   │   ├── FileUpload.svelte
│   │   │   ├── ImportResults.svelte
│   │   │   └── DocumentList.svelte
│   │   ├── services/
│   │   │   └── api.js
│   │   └── stores/
│   │       └── importStore.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
└── README_NEW.md
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/.env`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=expertak
MAX_FILE_SIZE=52428800  # 50 MB
BATCH_SIZE=500
CORS_ORIGINS=["http://localhost:5173"]
```

### Frontend Configuration

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## 📊 Data Model

The Excel file must have exactly these columns in this order:

1. tipo_documento
2. cufe_cude
3. folio
4. prefijo
5. divisa
6. forma_pago
7. medio_pago
8. fecha_emision
9. fecha_recepcion
10. nit_emisor
11. nombre_emisor
12. nit_receptor
13. nombre_receptor
14. iva
15. ica
16. ic
17. inc
18. timbre
19. inc_bolsas
20. in_carbono
21. in_combustibles
22. ic_datos
23. icl
24. inpp
25. ibua
26. icui
27. rete_iva
28. rete_renta
29. rete_ica
30. total
31. estado
32. grupo

**Important**: The first row must contain these exact column headers.

## 🔌 API Endpoints

### Validate File

```http
POST /api/v1/import/validate
Content-Type: multipart/form-data

file: [Excel file]
```

**Response:**
```json
{
  "valid": true,
  "message": "File is valid",
  "column_count": 12,
  "expected_columns": [...],
  "actual_columns": [...],
  "errors": []
}
```

### Import File

```http
POST /api/v1/import/
Content-Type: multipart/form-data

file: [Excel file]
```

**Response:**
```json
{
  "success": true,
  "message": "Import completed successfully",
  "file_name": "data.xlsx",
  "file_size": 123456,
  "total_rows": 1000,
  "inserted": 950,
  "duplicates": 30,
  "rejected": 20,
  "errors": [
    {
      "row_number": 5,
      "errors": ["Required field 'empresa' is empty"]
    }
  ],
  "processing_time_seconds": 12.34
}
```

### Documentos CRUD

```http
GET /api/v1/documentos?skip=0&limit=20&estado=APROBADO
GET /api/v1/documentos/{id}
POST /api/v1/documentos
PUT /api/v1/documentos/{id}
DELETE /api/v1/documentos/{id}
```

Example payload for create/update:

```json
{
  "tipo_documento": "FACTURA",
  "cufe_cude": "123456",
  "nit_emisor": 900123456,
  "nit_receptor": 800123456,
  "total": "1500.00",
  "estado": "APROBADO"
}
```

### Health Check

```http
GET /api/v1/health/
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Manual Testing

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Open http://localhost:5173
4. Upload a test Excel file
5. Check results

## 🔐 Extending With Auth & Roles

The backend is organized with services and repositories so you can add:

- JWT authentication middleware
- Role-based access via dependencies
- Audit logging per endpoint

## 🐳 Docker Deployment

### Development

```bash
docker-compose up
```

### Production

1. Update `docker-compose.yml` with production settings
2. Set environment variables
3. Use production database
4. Configure reverse proxy (nginx)
5. Enable SSL/TLS

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 Performance Optimization

### Backend

- **Batch Size**: Adjust `BATCH_SIZE` in config (default: 500)
- **Connection Pooling**: Configured in `database.py`
- **Read-Only Mode**: Excel files opened in read-only mode
- **Memory Management**: Process row-by-row, not load entire file

### Database

- **Indexes**: Already created on frequently queried columns
- **Composite Key**: Efficient duplicate detection
- **Transactions**: Batch operations for atomicity

### Frontend

- **Code Splitting**: Vite handles automatically
- **Asset Optimization**: Configured in `vite.config.js`
- **API Timeout**: Set to 5 minutes for large files

## 🔒 Security

- **Input Validation**: Pydantic models validate all inputs
- **SQL Injection**: SQLAlchemy ORM prevents SQL injection
- **File Validation**: Extension, MIME type, and structure validation
- **CORS**: Configured for specific origins
- **Error Handling**: No sensitive information exposed

## 📝 Logging

Logs are written to stdout/stderr. In production, configure logging:

```python
# In app/main.py
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
```

## 🐛 Troubleshooting

### Database Connection Failed

- Check database credentials in `.env`
- Verify database is running
- Check firewall rules
- Test connection: `mysql -u user -p -h host`

### File Upload Fails

- Check `MAX_FILE_SIZE` setting
- Verify `uploads/` directory permissions
- Check disk space
- Review error logs

### Import Errors

- Verify Excel file structure matches expected format
- Check column names and order
- Review error details in response
- Check database logs

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Code**: Fully documented with docstrings

## 🚀 Production Deployment

1. **Environment Variables**: Set production values
2. **Database**: Use production MariaDB instance
3. **Reverse Proxy**: Configure nginx/Apache
4. **SSL/TLS**: Enable HTTPS
5. **Monitoring**: Set up logging and monitoring
6. **Backups**: Configure database backups
7. **Scaling**: Use load balancer for multiple instances

## 📄 License

This project is provided as-is for use in the Expertak system.

## 👥 Support

For issues:
1. Check logs
2. Review API documentation
3. Verify configuration
4. Test with sample file

---

**Version**: 1.0.0  
**Last Updated**: January 2026
