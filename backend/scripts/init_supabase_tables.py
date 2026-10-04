#!/usr/bin/env python3
"""Crea las tablas de Expertak en Supabase (PostgreSQL)."""

import sys
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import check_database_connection, init_database, is_database_configured


def main() -> int:
    if not is_database_configured():
        print("ERROR: Configura DATABASE_URL en backend/.env (URI de Supabase)")
        return 1

    print("Creando tablas en Supabase...")
    init_database()

    if check_database_connection():
        print("OK: Conexión exitosa y tablas listas.")
        return 0

    print("ERROR: No se pudo verificar la conexión.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
