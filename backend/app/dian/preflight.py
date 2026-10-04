"""Verificación previa a la primera emisión DIAN (habilitación)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import dotenv_values

from .config_fe import get_fe_settings


def _check_path(path: Path, label: str) -> Dict[str, Any]:
    return {
        "label": label,
        "path": str(path),
        "ok": path.exists(),
    }


def run_fe_preflight() -> Dict[str, Any]:
    settings = get_fe_settings()
    checks: List[Dict[str, Any]] = []
    blockers: List[str] = []

    ref_ok = settings.reference_exists
    checks.append({
        "label": "Motor DIAN (referencia)",
        "path": str(settings.reference_app),
        "ok": ref_ok,
    })
    if not ref_ok:
        blockers.append("Ruta DIAN_REFERENCE_APP inválida o sin app.py")

    motor_env_path = settings.reference_app / ".env"
    motor_env = dotenv_values(motor_env_path) if motor_env_path.is_file() else {}
    checks.append(_check_path(motor_env_path, "Motor .env"))

    path_base_raw = (motor_env.get("PATH_BASE") or "").strip()
    path_base = Path(path_base_raw) if path_base_raw else None
    sign_name = (motor_env.get("SIGN_NAME") or "").strip()
    sign_password_set = bool((motor_env.get("SIGN_PASSWORD") or "").strip())
    politica_name = (motor_env.get("POLITICA_NAME") or "").strip()

    if not path_base_raw:
        checks.append({"label": "PATH_BASE", "path": "", "ok": False})
        blockers.append("PATH_BASE no configurado en el .env del motor DIAN")
    else:
        checks.append(_check_path(path_base, "PATH_BASE"))
        if path_base and not path_base.exists():
            blockers.append(f"PATH_BASE no existe: {path_base}")

        cert_dir = path_base / "certificados" if path_base else None
        if cert_dir:
            checks.append(_check_path(cert_dir, "certificados/"))
            if not cert_dir.exists():
                blockers.append(f"Carpeta certificados no existe: {cert_dir}")

        if sign_name and path_base:
            cert_file = path_base / "certificados" / sign_name
            checks.append(_check_path(cert_file, f"Certificado ({sign_name})"))
            if not cert_file.is_file():
                blockers.append(f"Certificado .pfx no encontrado: {cert_file}")
        else:
            checks.append({"label": "SIGN_NAME", "path": "", "ok": False})
            blockers.append("SIGN_NAME no configurado en el .env del motor DIAN")

        if not sign_password_set:
            checks.append({"label": "SIGN_PASSWORD", "path": "(oculto)", "ok": False})
            blockers.append("SIGN_PASSWORD no configurado en el .env del motor DIAN")
        else:
            checks.append({"label": "SIGN_PASSWORD", "path": "(configurado)", "ok": True})

        if politica_name and path_base:
            politica_file = path_base / "certificados" / politica_name
            checks.append({
                "label": f"Política firma ({politica_name})",
                "path": str(politica_file),
                "ok": politica_file.is_file(),
                "optional": True,
            })

    http_ok = False
    try:
        import requests

        r = requests.get(f"{settings.service_url}/docs", timeout=5)
        http_ok = r.status_code < 500
    except Exception:
        http_ok = False

    checks.append({
        "label": "Servicio motor HTTP :8001",
        "path": settings.service_url,
        "ok": http_ok,
    })
    if not http_ok and settings.engine in ("auto", "http"):
        blockers.append(
            f"Servicio DIAN no responde en {settings.service_url}. "
            "Inicie: uvicorn app:app --port 8001 en el motor de referencia."
        )

    expertak_env = dotenv_values(Path(__file__).resolve().parents[2] / ".env")
    for key in ("DIAN_REFERENCE_APP", "DIAN_SERVICE_URL"):
        value = expertak_env.get(key) or os.getenv(key)
        checks.append({
            "label": f"Expertak {key}",
            "path": value or "",
            "ok": bool(value),
        })
        if not value:
            blockers.append(f"{key} no configurado en backend/.env")

    db_url = expertak_env.get("DATABASE_URL") or os.getenv("DATABASE_URL")
    checks.append({
        "label": "Expertak DATABASE_URL (Supabase)",
        "path": "configurado" if db_url else "no configurado",
        "ok": bool(db_url),
        "optional": True,
    })

    payload_path = Path(__file__).resolve().parents[3] / "docs" / "fe_piloto.json"
    checks.append({
        "label": "Payload fe_piloto.json",
        "path": str(payload_path),
        "ok": payload_path.is_file(),
    })
    if not payload_path.is_file():
        blockers.append(
            "Falta docs/fe_piloto.json con datos reales de empresa, resolución y TestID."
        )

    ready = len(blockers) == 0
    return {
        "ready": ready,
        "engine": "http" if http_ok else ("inline" if ref_ok else "none"),
        "checks": checks,
        "blockers": blockers,
        "next_steps": _next_steps(blockers),
    }


def _next_steps(blockers: List[str]) -> List[str]:
    if not blockers:
        return [
            "Motor :8001 en marcha.",
            "Ejecute: python scripts/emitir_prueba.py",
            "Revise GET /api/v1/fe/emisiones para auditoría.",
        ]

    steps = [
        "Copie su certificado .pfx a facturacion/fe_data/certificados/.",
        "Actualice PATH_BASE en el .env del motor a facturacion/fe_data.",
        "Complete docs/fe_piloto.json (NIT, resolución, Software ID, Pin, TestID, clave técnica).",
        "Agregue DIAN_REFERENCE_APP y DIAN_SERVICE_URL en backend/.env.",
        "Inicie el motor: uvicorn app:app --reload --port 8001",
        "Ejecute: python scripts/emitir_prueba.py",
    ]
    return steps
