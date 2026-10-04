"""
Emisión de facturas electrónicas vía motor de referencia (software propio DIAN).

Estrategias (DIAN_ENGINE):
- auto: HTTP si el servicio responde; si no, inline
- http: solo POST al FastAPI de referencia (puerto 8001)
- inline: importa CreateInvoiceCase en el mismo proceso
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Tuple

import requests

from .config_fe import get_fe_settings
from .preflight import run_fe_preflight

logger = logging.getLogger(__name__)

ModoEmision = Literal["habilitacion", "produccion"]

_inline_lock = threading.Lock()
_inline_initialized = False


class DianEmitter:
    def __init__(self) -> None:
        self.settings = get_fe_settings()

    def emit(
        self, invoice: Dict[str, Any], modo: ModoEmision = "habilitacion"
    ) -> Tuple[bool, str, Optional[int], str, str]:
        """
        Returns: success, message, status_code, response_text, engine_used
        """
        engine = self.settings.engine
        if engine == "auto":
            if self._http_ping():
                engine = "http"
            elif self.settings.reference_exists:
                engine = "inline"
            else:
                return (
                    False,
                    "No hay motor DIAN disponible. Inicie el servicio de referencia "
                    f"({self.settings.service_url}) o configure DIAN_REFERENCE_APP.",
                    None,
                    "",
                    "none",
                )
        if (
            engine == "inline"
            and modo == "produccion"
            and not self.settings.allow_inline_produccion
        ):
            return (
                False,
                "Modo 'inline' deshabilitado en producción (aislamiento de proceso y licencia "
                "GPLv2 del motor). Inicie el motor en :8001 y use DIAN_ENGINE=http, o ponga "
                "DIAN_ALLOW_INLINE_PRODUCCION=true para forzarlo bajo su responsabilidad.",
                None,
                "",
                "inline-blocked",
            )
        if engine == "http":
            return (*self._emit_http(invoice, modo), "http")
        if engine == "inline":
            return (*self._emit_inline(invoice, modo), "inline")
        return False, f"DIAN_ENGINE inválido: {engine}", None, "", "none"

    def _http_ping(self) -> bool:
        try:
            r = requests.get(f"{self.settings.service_url}/docs", timeout=5)
            return r.status_code < 500
        except Exception:
            return False

    def _emit_http(
        self, invoice: Dict[str, Any], modo: ModoEmision
    ) -> Tuple[bool, str, Optional[int], str]:
        path = "/api/invoice/send_test" if modo == "habilitacion" else "/api/invoice/create_invoice"
        url = f"{self.settings.service_url}{path}"
        try:
            r = requests.post(url, json=invoice, timeout=self.settings.http_timeout)
            text = r.text
            if r.status_code >= 400:
                return False, f"DIAN HTTP {r.status_code}", r.status_code, text
            return True, "Enviado al servicio DIAN de referencia", r.status_code, text
        except requests.RequestException as exc:
            return False, f"Error conectando servicio DIAN: {exc}", None, str(exc)

    def _emit_inline(
        self, invoice: Dict[str, Any], modo: ModoEmision
    ) -> Tuple[bool, str, Optional[int], str]:
        global _inline_initialized
        ref = self.settings.reference_app
        if not ref.is_dir():
            return False, f"Ruta DIAN_REFERENCE_APP no existe: {ref}", None, ""

        with _inline_lock:
            try:
                self._bootstrap_reference_runtime(ref)
                from domain.dtos import InvoiceDto  # type: ignore
                from application.use_cases.invoice.create_invoice_case import (  # type: ignore
                    CreateInvoiceCase,
                )

                dto = InvoiceDto.model_validate(invoice)
                case = CreateInvoiceCase(dto)
                if modo == "habilitacion":
                    result = case.send_test()
                    if isinstance(result, dict):
                        status = result.get("status")
                        text = result.get("text", "")
                        ok = status is not None and int(status) < 400
                        return (
                            ok,
                            "Factura enviada (habilitación / set de prueba)",
                            int(status) if status else None,
                            str(text),
                        )
                    return True, str(result), None, str(result)
                messages = case.send()
                return True, "Factura enviada a DIAN", 200, str(messages)
            except Exception as exc:
                logger.exception("Error emisión inline DIAN")
                return False, str(exc), None, str(exc)

    def _bootstrap_reference_runtime(self, ref: Path) -> None:
        global _inline_initialized
        ref_str = str(ref.resolve())
        if ref_str not in sys.path:
            sys.path.insert(0, ref_str)
        os.chdir(ref_str)
        if not _inline_initialized:
            from shared import certificate_loader, templates_loader  # type: ignore

            certificate_loader.load()
            templates_loader.load()
            _inline_initialized = True

    def status(self) -> Dict[str, Any]:
        preflight = run_fe_preflight()
        ref_ok = self.settings.reference_exists
        http_ok = self._http_ping()
        cert_ok = any(
            c.get("ok") and "Certificado" in c.get("label", "")
            for c in preflight.get("checks", [])
        )
        ready = preflight.get("ready", False) and (http_ok or ref_ok)
        engine = "http" if http_ok else ("inline" if ref_ok else "none")
        blockers = preflight.get("blockers") or []
        detail = blockers[0] if blockers else None
        if not ready and not detail:
            detail = (
                "Configure certificado en .env del proyecto de referencia y ejecute: "
                f"cd {self.settings.reference_app} && uvicorn app:app --port 8001"
            )
        return {
            "ready": ready,
            "engine": engine,
            "reference_app_path": str(self.settings.reference_app),
            "reference_app_exists": ref_ok,
            "http_service_url": self.settings.service_url,
            "http_service_reachable": http_ok,
            "certificate_configured": cert_ok,
            "detail": detail,
            "blockers": blockers,
        }


def get_dian_emitter() -> DianEmitter:
    return DianEmitter()
