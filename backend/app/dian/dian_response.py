"""
Interpretación de la respuesta de la DIAN / motor de referencia.

El estado de una factura NO debe inferirse del éxito del transporte (HTTP < 400), sino de
la validación real de la DIAN (elemento ``IsValid`` del ApplicationResponse). Este módulo
normaliza las distintas formas de respuesta posibles:

- Habilitación HTTP: el motor devuelve JSON ``{"status": <code>, "text": "<SOAP XML>"}``.
- Habilitación inline: ``text`` con el SOAP XML de SendTestSetAsync.
- Producción: el motor devuelve los mensajes de ``extract_errors_invoice`` (lanza excepción
  si ``IsValid == 'false'``), por lo que un transporte exitoso implica validación.

Estados resultantes (alineados con fe_facturas.estado):
    VALIDADA | RECHAZADA | ENVIADA | ERROR
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

try:
    from lxml import etree  # type: ignore

    _HAS_LXML = True
except Exception:  # pragma: no cover - lxml siempre presente vía motor
    _HAS_LXML = False

_DIAN_NS = {
    "b": "http://schemas.datacontract.org/2004/07/DianResponse",
    "c": "http://schemas.microsoft.com/2003/10/Serialization/Arrays",
}

# Fallbacks por regex (cuando el XML no es parseable o viene anidado en texto).
_IS_VALID_RE = re.compile(r"<\s*(?:\w+:)?IsValid\s*>\s*(true|false)\s*<", re.IGNORECASE)
_STATUS_CODE_RE = re.compile(r"<\s*(?:\w+:)?StatusCode\s*>\s*([^<]+?)\s*<", re.IGNORECASE)
_STATUS_DESC_RE = re.compile(r"<\s*(?:\w+:)?StatusDescription\s*>\s*([^<]+?)\s*<", re.IGNORECASE)
_TRACK_ID_RE = re.compile(r"<\s*(?:\w+:)?(?:ZipKey|TrackId)\s*>\s*([^<]+?)\s*<", re.IGNORECASE)


@dataclass
class DianResult:
    estado: str
    is_valid: Optional[bool] = None
    status_code: Optional[str] = None
    status_description: Optional[str] = None
    track_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)


def _unwrap_text(response_text: Optional[str]) -> str:
    """Si la respuesta es JSON ``{"status", "text"}`` (modo habilitación), devuelve ``text``."""
    if not response_text:
        return ""
    stripped = response_text.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict) and "text" in data:
                return str(data.get("text") or "")
        except (ValueError, TypeError):
            pass
    return response_text


def _parse_xml(xml_text: str) -> DianResult:
    is_valid: Optional[bool] = None
    status_code: Optional[str] = None
    status_desc: Optional[str] = None
    track_id: Optional[str] = None
    errors: List[str] = []

    if _HAS_LXML and "<" in xml_text:
        try:
            tree = etree.fromstring(xml_text.encode("utf-8"))
            node = tree.find(".//b:IsValid", _DIAN_NS)
            if node is not None and node.text is not None:
                is_valid = node.text.strip().lower() == "true"
            sc = tree.find(".//b:StatusCode", _DIAN_NS)
            if sc is not None and sc.text:
                status_code = sc.text.strip()
            sd = tree.find(".//b:StatusDescription", _DIAN_NS)
            if sd is not None and sd.text:
                status_desc = sd.text.strip()
            errors = [e.text for e in tree.findall(".//c:string", _DIAN_NS) if e.text]
        except Exception:
            pass

    # Respaldos por regex si el parseo estructurado no encontró nada.
    if is_valid is None:
        m = _IS_VALID_RE.search(xml_text)
        if m:
            is_valid = m.group(1).lower() == "true"
    if status_code is None:
        m = _STATUS_CODE_RE.search(xml_text)
        if m:
            status_code = m.group(1)
    if status_desc is None:
        m = _STATUS_DESC_RE.search(xml_text)
        if m:
            status_desc = m.group(1)
    if track_id is None:
        m = _TRACK_ID_RE.search(xml_text)
        if m:
            track_id = m.group(1)

    return DianResult(
        estado="",
        is_valid=is_valid,
        status_code=status_code,
        status_description=status_desc,
        track_id=track_id,
        errors=errors,
    )


def interpret_response(
    response_text: Optional[str],
    transport_ok: bool,
    modo: str,
) -> DianResult:
    """
    Determina el estado real a partir de la respuesta de la DIAN.

    - ``transport_ok=False`` → ERROR (no llegó a validar).
    - ``IsValid=true``       → VALIDADA.
    - ``IsValid=false``      → RECHAZADA.
    - Sin veredicto pero transporte OK:
        * producción  → VALIDADA (el motor lanza excepción si fue rechazada).
        * habilitación → ENVIADA (validación asíncrona de set de prueba).
    """
    xml_text = _unwrap_text(response_text)
    result = _parse_xml(xml_text)

    if not transport_ok:
        result.estado = "ERROR"
    elif result.is_valid is True:
        result.estado = "VALIDADA"
    elif result.is_valid is False:
        result.estado = "RECHAZADA"
    elif modo == "produccion":
        result.estado = "VALIDADA"
    else:
        result.estado = "ENVIADA"

    return result
