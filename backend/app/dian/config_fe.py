"""Configuración emisión FE — rutas y servicio DIAN."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@lru_cache
def get_fe_settings():
    return FeSettings()


class FeSettings:
    def __init__(self) -> None:
        self.reference_app = Path(
            os.getenv(
                "DIAN_REFERENCE_APP",
                r"C:\path\to\facturacion"
                r"\facturacion-electronica-colombia-main"
                r"\facturacion-electronica-colombia-main",
            )
        )
        self.service_url = os.getenv("DIAN_SERVICE_URL", "http://localhost:8001").rstrip("/")
        self.engine = os.getenv("DIAN_ENGINE", "auto").lower()  # auto | http | inline
        self.http_timeout = float(os.getenv("DIAN_HTTP_TIMEOUT", "120"))
        # El modo 'inline' embebe el motor (GPLv2) en el proceso de Expertak; se bloquea en
        # producción por aislamiento y licencia, salvo override explícito.
        self.allow_inline_produccion = (
            os.getenv("DIAN_ALLOW_INLINE_PRODUCCION", "false").lower() in ("1", "true", "yes")
        )

    @property
    def reference_exists(self) -> bool:
        return self.reference_app.is_dir() and (self.reference_app / "app.py").is_file()
