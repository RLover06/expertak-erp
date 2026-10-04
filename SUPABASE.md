# Expertak + Supabase

Expertak puede guardar **documentos DIAN**, **consolidado contable** y **resumen** en [Supabase](https://supabase.com) (PostgreSQL administrado), sin instalar MariaDB.

## 1. Crear proyecto en Supabase

1. Entra en [supabase.com](https://supabase.com) y crea una cuenta.
2. **New project** → elige nombre, contraseña de base de datos y región.
3. Espera a que el proyecto esté listo (~1 minuto).

## 2. Obtener la URL de conexión

1. En el panel: **Project Settings** → **Database**.
2. En **Connection string**, elige **URI**.
3. Modo recomendado: **Session pooler** (puerto `5432`).
4. Copia la URL y reemplaza `[YOUR-PASSWORD]` por la contraseña del proyecto.

Ejemplo:

```text
postgresql://postgres.abcdefgh:TuPassword@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

## 3. Configurar Expertak

```bash
cd backend
cp .env.example .env
```

Edita `backend/.env` y pega tu `DATABASE_URL`:

```env
DATABASE_URL=postgresql://postgres.xxx:TU_PASSWORD@....supabase.com:5432/postgres
```

## 4. Crear tablas

**Opción A — Script Python (recomendado)**

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/init_supabase_tables.py
```

**Opción B — SQL Editor en Supabase**

1. Panel → **SQL Editor** → **New query**.
2. Pega el contenido de `sql/supabase_schema.sql`.
3. Ejecuta (**Run**).

## 5. Iniciar el backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verifica: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

Respuesta esperada:

```json
{
  "status": "ok",
  "mode": "supabase",
  "database": "connected",
  "documentos": "0",
  "resumen": "0",
  "consolidado": "0"
}
```

## 6. Ver datos en Supabase

**Table Editor** → verás:

| Tabla | Contenido |
|-------|-----------|
| `documentos_dian` | Facturas importadas desde Excel DIAN |
| `consolidado_movimientos` | Movimientos contables (débito/crédito) |
| `empresas` / `terceros` | Catálogos del consolidado |
| `resumen_filas` | Resumen pre-agregado (INFORME RELACION_FE) |

## Sin Supabase (desarrollo rápido)

Si **no** configuras `DATABASE_URL`, el backend usa **memoria**: funciona igual para probar, pero los datos se borran al reiniciar.

## Docker sin MariaDB

Puedes levantar solo frontend + backend y apuntar `DATABASE_URL` a Supabase en la nube. El servicio `db` de `docker-compose.yml` es opcional si usas Supabase.

## Seguridad

- No subas `.env` a Git (ya está en `.gitignore`).
- En producción usa variables de entorno del servidor, no archivos locales.
- La clave `service_role` de Supabase solo en backend; nunca en el frontend.

## Próximos pasos

- Facturación electrónica (emisión DIAN)
- Plantillas contables automáticas al aprobar facturas
- Auth con Supabase (opcional)
