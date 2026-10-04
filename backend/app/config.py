import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_settings():
    return Settings()


class Settings:
    """Application settings. Supabase = PostgreSQL via DATABASE_URL."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.db_host = os.getenv("DB_HOST", "127.0.0.1")
        self.db_port = os.getenv("DB_PORT", "3306")
        self.db_user = os.getenv("DB_USER", "root")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "expertak")
        self.db_charset = os.getenv("DB_CHARSET", "utf8mb4")

        self.supabase_url = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()

        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "52428800"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "500"))
        self.api_v1_prefix = os.getenv("API_V1_PREFIX", "/api/v1")

    @property
    def use_supabase(self) -> bool:
        return bool(self.database_url)

    @property
    def storage_mode(self) -> str:
        return "supabase" if self.use_supabase else "memory"
