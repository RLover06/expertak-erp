"""Data store: Supabase (PostgreSQL) when DATABASE_URL is set, else in-memory."""

from typing import Optional, Union

from .config import get_settings
from .database import is_database_configured
from .memory_store import MemoryStore
from .supabase_store import SupabaseStore

StoreType = Union[MemoryStore, SupabaseStore]

_store: Optional[StoreType] = None


def get_store() -> StoreType:
    global _store
    if _store is None:
        settings = get_settings()
        if settings.use_supabase or is_database_configured():
            _store = SupabaseStore()
        else:
            _store = MemoryStore()
    return _store


def reset_store() -> None:
    """For tests: force re-initialization of store."""
    global _store
    _store = None
