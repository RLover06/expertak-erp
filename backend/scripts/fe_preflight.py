#!/usr/bin/env python3
"""Checklist previo a la primera emisión DIAN."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.dian.preflight import run_fe_preflight


def main() -> int:
    data = run_fe_preflight()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if data["ready"]:
        print("\nOK: listo para emitir. Ejecute: python scripts/emitir_prueba.py")
        return 0
    print("\nBLOQUEADO. Corrija:")
    for item in data["blockers"]:
        print(f"  - {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
