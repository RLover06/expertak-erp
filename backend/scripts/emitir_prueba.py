#!/usr/bin/env python3
"""Primera emisión de prueba (habilitación) vía Expertak API."""

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))

from app.dian.preflight import run_fe_preflight

API_BASE = "http://localhost:8000/api/v1/fe"
PAYLOAD_PATH = PROJECT / "docs" / "fe_piloto.json"


def _payload_has_placeholders(payload: dict) -> list[str]:
    text = json.dumps(payload)
    missing = []
    if "REEMPLAZAR_" in text:
        missing.append("docs/fe_piloto.json contiene valores REEMPLAZAR_* sin completar")
    return missing


def main() -> int:
    preflight = run_fe_preflight()
    if not preflight["ready"]:
        print("Preflight falló. Ejecute: python scripts/fe_preflight.py")
        for item in preflight["blockers"]:
            print(f"  - {item}")
        return 1

    if not PAYLOAD_PATH.is_file():
        print(f"No existe {PAYLOAD_PATH}")
        return 1

    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    payload.pop("_comment", None)
    issues = _payload_has_placeholders(payload)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1

    body = {"modo": "habilitacion", "invoice": payload}
    print(f"POST {API_BASE}/emitir ...")
    try:
        response = requests.post(f"{API_BASE}/emitir", json=body, timeout=180)
    except requests.RequestException as exc:
        print(f"ERROR: no se pudo conectar a Expertak (:8000): {exc}")
        print("Inicie: cd backend && uvicorn app.main:app --reload --port 8000")
        return 1

    print(f"HTTP {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(response.text[:2000])
        return 1 if response.status_code >= 400 else 0

    if response.status_code >= 400:
        return 1

    print("\nRevise historial: GET /api/v1/fe/emisiones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
