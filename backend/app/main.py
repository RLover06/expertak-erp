"""
Expertak FastAPI - Importación, consolidado y reportes.
Almacenamiento: Supabase (PostgreSQL) si DATABASE_URL está configurada; si no, en memoria.
"""
import os
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .database import check_database_connection, init_database, is_database_configured
from .routers.fe_facturas import router as fe_facturas_router
from .store import get_store
from .schemas import (
    ConsolidadoImportRequest,
    ConsolidadoImportResponse,
    DocumentosResponse,
    DocumentosResumenResponse,
    ImportResponse,
    ImportRowsRequest,
    InformeReporteResponse,
    InformeReporteRow,
    PivotOptionsResponse,
    PivotResponse,
    ResumenImportRequest,
    ResumenImportResponse,
)

load_dotenv()

API_V1_PREFIX = "/api/v1"
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "52428800"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))

# Resumen pre-agregado: se persiste en Supabase (resumen_filas) o en memoria según DATABASE_URL

app = FastAPI(title="Expertak API", version="2.2.0")

app.include_router(fe_facturas_router, prefix=API_V1_PREFIX)


@app.on_event("startup")
async def startup_init_database() -> None:
    if is_database_configured():
        init_database()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite acceso desde cualquier origen (localhost, 127.0.0.1, etc.)
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXPECTED_COLUMNS = [
    "tipo_documento",
    "cufe_cude",
    "folio",
    "prefijo",
    "divisa",
    "forma_pago",
    "medio_pago",
    "fecha_emision",
    "fecha_recepcion",
    "nit_emisor",
    "nombre_emisor",
    "nit_receptor",
    "nombre_receptor",
    "iva",
    "ica",
    "ic",
    "inc",
    "timbre",
    "inc_bolsas",
    "in_carbono",
    "in_combustibles",
    "ic_datos",
    "icl",
    "inpp",
    "ibua",
    "icui",
    "rete_iva",
    "rete_renta",
    "rete_ica",
    "total",
    "estado",
    "grupo",
    "empresa",  # Columna Empresa del Excel para Resumen
]

DECIMAL_FIELDS = {
    "iva", "ica", "ic", "inc", "timbre", "inc_bolsas", "in_carbono", "in_combustibles",
    "ic_datos", "icl", "inpp", "ibua", "icui", "rete_iva", "rete_renta", "rete_ica", "total",
}

INT_FIELDS = {"nit_emisor", "nit_receptor"}

CONSOLIDADO_COLUMNS = [
    "empresa", "empresa_nit", "tercero", "tercero_nit", "fecha", "cuenta",
    "debito", "credito", "documento_origen", "periodo",
]

CONSOLIDADO_DECIMAL_FIELDS = {"debito", "credito"}

# Nombres para mensajes de error (estilo PHP)
CONSOLIDADO_FIELD_LABELS = {
    "empresa": "Empresa",
    "empresa_nit": "NIT Empresa",
    "tercero": "Tercero",
    "tercero_nit": "NIT Tercero",
    "fecha": "Fecha",
    "cuenta": "Cuenta",
    "debito": "Débito",
    "credito": "Crédito",
    "documento_origen": "Documento origen",
    "periodo": "Periodo",
}

HEADER_MAP = {
    "tipo de documento": "tipo_documento", "tipo documento": "tipo_documento", "tipo_documento": "tipo_documento",
    "cufe/cude": "cufe_cude", "cufe cude": "cufe_cude", "cufe": "cufe_cude", "cude": "cufe_cude",
    "cufe_cude": "cufe_cude", "codigo cufe": "cufe_cude", "código cufe": "cufe_cude",
    "folio": "folio", "prefijo": "prefijo", "divisa": "divisa",
    "forma de pago": "forma_pago", "medio de pago": "medio_pago",
    "fecha emision": "fecha_emision", "fecha emisión": "fecha_emision",
    "fecha recepcion": "fecha_recepcion", "fecha recepción": "fecha_recepcion",
    "nit emisor": "nit_emisor", "nombre emisor": "nombre_emisor", "razon social": "nombre_emisor",
    "razón social": "nombre_emisor", "nombre emisor o razon social": "nombre_emisor",
    "nit receptor": "nit_receptor", "nombre receptor": "nombre_receptor",
    "iva": "iva", "ica": "ica", "ic": "ic", "inc": "inc", "timbre": "timbre",
    "inc bolsas": "inc_bolsas", "in carbono": "in_carbono", "in combustibles": "in_combustibles",
    "ic datos": "ic_datos", "icl": "icl", "inpp": "inpp", "ibua": "ibua", "icui": "icui",
    "rete iva": "rete_iva", "rete renta": "rete_renta", "rete ica": "rete_ica",
    "total": "total", "estado": "estado", "grupo": "grupo",
    "empresa": "empresa", "identificacion": "identificacion",
}

for key in EXPECTED_COLUMNS:
    HEADER_MAP[key.replace("_", " ")] = key
    HEADER_MAP[key] = key

CONSOLIDADO_HEADER_MAP = {
    "empresa": "empresa", "nit empresa": "empresa_nit", "nit_empresa": "empresa_nit", "empresa nit": "empresa_nit",
    "tercero": "tercero", "nit tercero": "tercero_nit", "nit_tercero": "tercero_nit", "tercero nit": "tercero_nit",
    "fecha": "fecha", "fecha movimiento": "fecha", "fecha contabilizacion": "fecha",
    "cuenta": "cuenta", "cuenta contable": "cuenta", "codigo cuenta": "cuenta",
    "debito": "debito", "débito": "debito", "debitos": "debito",
    "credito": "credito", "crédito": "credito", "creditos": "credito",
    "documento origen": "documento_origen", "documento_origen": "documento_origen",
    "periodo": "periodo", "período": "periodo", "periodo contable": "periodo",
}

for key in CONSOLIDADO_COLUMNS:
    CONSOLIDADO_HEADER_MAP[key.replace("_", " ")] = key
    CONSOLIDADO_HEADER_MAP[key] = key

# Resumen pre-agregado (INFORME RELACION_FE)
RESUMEN_COLUMNS = ["empresa", "tipo_documento", "grupo", "subtotal", "iva", "total_otros", "total_renta", "total"]
RESUMEN_HEADER_MAP = {
    "empresa": "empresa",
    "razon social": "empresa",
    "razon_social": "empresa",
    "nombre": "empresa",
    "tipo de documento": "tipo_documento",
    "tipo_de_documento": "tipo_documento",
    "tipo documento": "tipo_documento",
    "tipo": "tipo_documento",
    "documento": "tipo_documento",
    "grupo": "grupo",
    "clase": "grupo",
    "estado": "grupo",
    "emitido recibido": "grupo",
    "subtotal": "subtotal",
    "iva": "iva",
    "impuesto": "iva",
    "impuestos": "iva",
    "total otros": "total_otros",
    "total_otros": "total_otros",
    "otros": "total_otros",
    "total renta": "total_renta",
    "total_renta": "total_renta",
    "retenciones": "total_renta",
    "total": "total",
    "total general": "total",
}
for key in RESUMEN_COLUMNS:
    RESUMEN_HEADER_MAP[key.replace("_", " ")] = key
    RESUMEN_HEADER_MAP[key] = key


def normalize_header(value: Any) -> str:
    raw = str(value or "").strip()
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join([c for c in raw if not unicodedata.combining(c)])
    raw = raw.replace("/", " ")
    raw = re.sub(r"\s+", " ", raw)
    return raw.lower()


def coerce_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = value.replace("$", "").replace(",", "").strip()
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
    return None


def coerce_decimal_colombian(value: Any) -> Optional[Decimal]:
    """Parsea formato colombiano: 714.263.500,00 (punto miles, coma decimal) o 1.000.065. Tambien numeros ya parseados."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = str(value).replace("$", "").strip()
        if not cleaned:
            return None
        # Formato colombiano: 714.263.500,00 -> quitar puntos (miles), coma -> punto (decimal)
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "." in cleaned:
            parts = cleaned.split(".")
            if len(parts) == 2 and len(parts[1]) <= 2 and parts[1].isdigit():
                pass  # 1.5 o 10.25 - decimal
            else:
                cleaned = cleaned.replace(".", "")  # miles: 1.000.065
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return coerce_decimal(value)  # fallback formato US
    return None


def _parse_resumen_number(value: Any) -> Decimal:
    """Parsea cualquier valor numerico para Resumen. Nunca retorna None."""
    d = coerce_decimal_colombian(value) or coerce_decimal(value)
    return d if d is not None else Decimal("0")


def format_decimal_colombian(value: Any) -> str:
    """Formatea número al estilo colombiano: 714.263.500,00"""
    if value is None:
        return "0,00"
    d = coerce_decimal_colombian(value) or coerce_decimal(value) or Decimal("0")
    # f"{d:,.2f}" -> "714,263,500.00" (US) -> swap to "714.263.500,00" (CO)
    s = f"{d:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d]", "", value)
        return int(cleaned) if cleaned else None
    return None


def coerce_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(trimmed, fmt).date()
            except ValueError:
                continue
    return None


def coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
            try:
                return datetime.strptime(trimmed, fmt)
            except ValueError:
                continue
    return None


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {HEADER_MAP.get(normalize_header(k)): v for k, v in row.items() if HEADER_MAP.get(normalize_header(k))}


def normalize_consolidado_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {CONSOLIDADO_HEADER_MAP.get(normalize_header(k)): v for k, v in row.items() if CONSOLIDADO_HEADER_MAP.get(normalize_header(k))}


def normalize_resumen_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {RESUMEN_HEADER_MAP.get(normalize_header(k)): v for k, v in row.items() if RESUMEN_HEADER_MAP.get(normalize_header(k))}


def _col_index_to_letter(idx: int) -> str:
    """Convierte índice de columna (0-based) a letra Excel: 0->A, 1->B, ... 26->AA."""
    result = ""
    idx += 1
    while idx > 0:
        idx -= 1
        result = chr(65 + (idx % 26)) + result
        idx //= 26
    return result


def _get_header_col_for_field(headers: List[str], field_key: str) -> Optional[int]:
    """Retorna el índice de columna del header que mapea al campo dado."""
    for i, h in enumerate(headers):
        if CONSOLIDADO_HEADER_MAP.get(normalize_header(str(h))) == field_key:
            return i
    return None


def row_is_empty(row: Dict[str, Any]) -> bool:
    return all(
        value is None or (isinstance(value, float) and pd.isna(value)) or (isinstance(value, str) and not value.strip())
        for value in row.values()
    )


def build_insert_payload(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    valid_rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for index, row in enumerate(rows):
        row_number = index + 2
        normalized = normalize_row(row)
        if row_is_empty(normalized):
            continue

        def _is_empty(val, allow_zero: bool = False) -> bool:
            if val is None:
                return True
            if isinstance(val, float) and pd.isna(val):
                return True
            if allow_zero and (val == 0 or val == Decimal("0")):
                return False
            if isinstance(val, str) and not str(val).strip():
                return True
            return False

        missing_required = []
        for r in ("tipo_documento", "cufe_cude", "total"):
            val = normalized.get(r)
            if r == "total":
                if _is_empty(val, allow_zero=True):
                    missing_required.append(r)
            elif _is_empty(val):
                missing_required.append(r)
        if missing_required:
            errors.append({"row_number": row_number, "errors": [f"Campo requerido vacío: {f}" for f in missing_required]})
            continue

        payload: Dict[str, Any] = {}
        for column in EXPECTED_COLUMNS:
            value = normalized.get(column)
            if column in DECIMAL_FIELDS:
                # Usar coerce_decimal_colombian para soportar formato 1.234,56 y coerce_decimal como fallback
                payload[column] = coerce_decimal_colombian(value) or coerce_decimal(value) or Decimal("0.00")
            elif column in INT_FIELDS:
                payload[column] = coerce_int(value)
            elif column == "fecha_emision":
                payload[column] = coerce_date(value)
            elif column == "fecha_recepcion":
                payload[column] = coerce_datetime(value)
            else:
                payload[column] = str(value).strip() if value is not None and not (isinstance(value, float) and pd.isna(value)) else None
        valid_rows.append(payload)

    return valid_rows, errors


def build_consolidado_payload(
    rows: List[Dict[str, Any]],
    headers: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Valida y construye payload de consolidado.
    Mensajes de error estilo PHP: "El campo X está vacío en la celda: B5. Se debe corregir la celda indicada."
    """
    valid_rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not headers and rows:
        headers = list(rows[0].keys()) if rows else []

    for index, row in enumerate(rows):
        row_number = index + 2  # Fila 1 = encabezados, fila 2 = primer dato
        normalized = normalize_consolidado_row(row)
        if row_is_empty(normalized):
            continue

        missing_required: List[str] = []
        for field in ("empresa", "tercero", "fecha", "cuenta"):
            val = normalized.get(field)
            if val is None or (isinstance(val, str) and not str(val).strip()):
                missing_required.append(field)

        parsed_date = coerce_date(normalized.get("fecha"))
        if not parsed_date and "fecha" not in missing_required:
            missing_required.append("fecha")

        if missing_required:
            error_msgs: List[str] = []
            for field in missing_required:
                label = CONSOLIDADO_FIELD_LABELS.get(field, field)
                col_idx = _get_header_col_for_field(headers or [], field) if headers else None
                if col_idx is not None:
                    col_letter = _col_index_to_letter(col_idx)
                    cell_ref = f"{col_letter}{row_number}"
                    error_msgs.append(
                        f"El campo {label} está vacío en la celda: {cell_ref}. Se debe corregir la celda indicada."
                    )
                else:
                    error_msgs.append(
                        f"El campo {label} está vacío en la fila {row_number}. Se debe corregir la celda indicada."
                    )
            errors.append({"row_number": row_number, "errors": error_msgs})
            continue

        payload: Dict[str, Any] = {
            "empresa": str(normalized.get("empresa")).strip(),
            "empresa_nit": str(normalized.get("empresa_nit")).strip() if normalized.get("empresa_nit") else None,
            "tercero": str(normalized.get("tercero")).strip(),
            "tercero_nit": str(normalized.get("tercero_nit")).strip() if normalized.get("tercero_nit") else None,
            "fecha": parsed_date,
            "cuenta": str(normalized.get("cuenta")).strip(),
            "documento_origen": str(normalized.get("documento_origen")).strip() if normalized.get("documento_origen") else None,
            "periodo": str(normalized.get("periodo")).strip() if normalized.get("periodo") else None,
        }
        for col in CONSOLIDADO_DECIMAL_FIELDS:
            payload[col] = coerce_decimal(normalized.get(col)) or Decimal("0.00")
        valid_rows.append(payload)

    return valid_rows, errors


# Orden estandar de columnas Resumen (fallback por posicion)
RESUMEN_COLUMN_ORDER = ["empresa", "tipo_documento", "grupo", "subtotal", "iva", "total_otros", "total_renta", "total"]


def _row_from_position(row: Dict[str, Any], headers: List[str]) -> Dict[str, Any]:
    """Construye fila normalizada por posicion cuando el mapeo por nombre falla."""
    out: Dict[str, Any] = {}
    for i, field in enumerate(RESUMEN_COLUMN_ORDER):
        if i < len(headers):
            val = row.get(headers[i], row.get(headers[i]) if isinstance(row, dict) else None)
            if field in ("subtotal", "iva", "total_otros", "total_renta", "total"):
                out[field] = _parse_resumen_number(val)
            else:
                out[field] = str(val or "").strip()
    return out


def build_resumen_payload(rows: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Valida y normaliza filas del Resumen pre-agregado (INFORME RELACION_FE). Fallback por posicion de columnas."""
    valid_rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not rows:
        return valid_rows, errors

    _headers = headers or list(rows[0].keys())

    for index, row in enumerate(rows):
        row_number = index + 2
        normalized = normalize_resumen_row(row)

        # Fallback: si faltan campos criticos, intentar por posicion
        if not normalized.get("empresa") or not normalized.get("tipo_documento") or not normalized.get("grupo"):
            if len(_headers) >= 8:
                by_pos = _row_from_position(row, _headers)
                if by_pos.get("empresa") or by_pos.get("tipo_documento") or by_pos.get("grupo"):
                    normalized = by_pos

        if row_is_empty(normalized):
            continue

        emp = str(normalized.get("empresa") or "").strip()
        if emp.lower().startswith("total acumulado") or emp.lower().startswith("total acu"):
            continue

        missing = [f for f in ("empresa", "tipo_documento", "grupo") if not normalized.get(f) or not str(normalized.get(f)).strip()]
        if missing:
            labels = {"empresa": "Empresa", "tipo_documento": "Tipo De Documento", "grupo": "Grupo"}
            errors.append({
                "row_number": row_number,
                "errors": [f"El campo {labels.get(f, f)} está vacío en la fila {row_number}." for f in missing]
            })
            continue

        payload: Dict[str, Any] = {
            "empresa": emp,
            "tipo_documento": str(normalized.get("tipo_documento") or "").strip(),
            "grupo": str(normalized.get("grupo") or "").strip(),
            "subtotal": _parse_resumen_number(normalized.get("subtotal")),
            "iva": _parse_resumen_number(normalized.get("iva")),
            "total_otros": _parse_resumen_number(normalized.get("total_otros")),
            "total_renta": _parse_resumen_number(normalized.get("total_renta")),
            "total": _parse_resumen_number(normalized.get("total")),
        }
        valid_rows.append(payload)

    return valid_rows, errors


def iter_batches(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def serialize_preview_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for row in rows:
        clean = {}
        for k, v in row.items():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                clean[k] = None
            elif isinstance(v, (datetime, date)):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        out.append(clean)
    return out


def _doc_to_dict(doc: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Convierte documento en memoria a formato API."""
    d = dict(doc)
    d["id"] = idx
    for k in DECIMAL_FIELDS:
        if k in d and d[k] is not None:
            d[k] = str(d[k])
    if d.get("fecha_emision") and hasattr(d["fecha_emision"], "isoformat"):
        d["fecha_emision"] = d["fecha_emision"].isoformat()
    if d.get("fecha_recepcion") and hasattr(d["fecha_recepcion"], "isoformat"):
        d["fecha_recepcion"] = d["fecha_recepcion"].isoformat()
    return d


def _filter_text(value: Any, filter_val: Optional[str]) -> bool:
    """Filtro de texto: contiene (case-insensitive) o coincide exacto si está vacío."""
    if not filter_val or not str(filter_val).strip():
        return True
    s = str(value or "").lower().strip()
    f = str(filter_val).lower().strip()
    return f in s or s == f


def _filter_date(value: Any, desde: Optional[date], hasta: Optional[date]) -> bool:
    if value is None:
        return True
    d = value if isinstance(value, date) else coerce_date(value)
    if not d:
        return True
    if desde and d < desde:
        return False
    if hasta and d > hasta:
        return False
    return True


# ==================== ENDPOINTS ====================

@app.post(f"{API_V1_PREFIX}/import/preview")
async def preview_import(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file:
        raise HTTPException(status_code=400, detail="Archivo requerido")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Archivo excede el tamaño permitido")
    try:
        df = pd.read_excel(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error al leer Excel: {exc}") from exc
    headers = [str(col) for col in df.columns]
    df = df.where(pd.notna(df), None)
    rows = df.to_dict(orient="records")
    return {"headers": headers, "rows": serialize_preview_rows(rows)}


@app.post(f"{API_V1_PREFIX}/import", response_model=ImportResponse)
async def import_rows(payload: ImportRowsRequest) -> ImportResponse:
    start_time = datetime.utcnow()
    store = get_store()

    raw_rows = payload.rows or []
    if not raw_rows:
        raise HTTPException(status_code=400, detail="No se recibieron filas para importar")

    cleaned_rows, row_errors = build_insert_payload(raw_rows)
    total_rows = len(raw_rows)
    file_name = payload.file_name or None

    inserted, duplicates = store.import_documentos(cleaned_rows, file_name)

    processing_time = (datetime.utcnow() - start_time).total_seconds()
    return ImportResponse(
        success=True,
        message="Importación completada correctamente",
        file_name=payload.file_name,
        file_size=None,
        total_rows=total_rows,
        inserted=inserted,
        duplicates=duplicates,
        rejected=len(row_errors),
        errors=row_errors,
        processing_time_seconds=round(processing_time, 2),
    )


@app.get(f"{API_V1_PREFIX}/documentos", response_model=DocumentosResponse)
async def list_documentos(
    skip: int = 0,
    limit: int = 20,
    cufe_cude: Optional[str] = None,
    nit_emisor: Optional[int] = None,
    nit_receptor: Optional[int] = None,
    estado: Optional[str] = None,
) -> DocumentosResponse:
    items = get_store().list_documentos()

    if cufe_cude:
        items = [d for d in items if _filter_text(d.get("cufe_cude"), cufe_cude)]
    if nit_emisor is not None:
        items = [d for d in items if coerce_int(d.get("nit_emisor")) == nit_emisor]
    if nit_receptor is not None:
        items = [d for d in items if coerce_int(d.get("nit_receptor")) == nit_receptor]
    if estado:
        items = [d for d in items if _filter_text(d.get("estado"), estado)]

    total = len(items)
    items = items[skip : skip + limit]
    return DocumentosResponse(
        items=[_doc_to_dict(d, d.get("_id", i)) for i, d in enumerate(items)],
        total=total,
        skip=skip,
        limit=limit,
    )


def _compute_resumen_items(
    empresa: Optional[str],
    grupo: Optional[str],
    tipo_documento: Optional[str],
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str],
) -> List[Dict[str, Any]]:
    items = get_store().list_documentos()

    if empresa:
        items = [d for d in items if _filter_text(d.get("empresa") or d.get("nombre_emisor"), empresa)]
    if grupo:
        items = [d for d in items if _filter_text(d.get("grupo"), grupo)]
    if tipo_documento:
        items = [d for d in items if _filter_text(d.get("tipo_documento"), tipo_documento)]

    fd = coerce_date(fecha_desde) if fecha_desde else None
    fh = coerce_date(fecha_hasta) if fecha_hasta else None
    if fd or fh:
        items = [d for d in items if _filter_date(d.get("fecha_emision"), fd, fh)]

    groups: Dict[Tuple[Optional[str], Optional[str], Optional[str]], Dict[str, Decimal]] = defaultdict(
        lambda: {
            "iva": Decimal("0"), "ica": Decimal("0"), "ic": Decimal("0"), "inc": Decimal("0"),
            "timbre": Decimal("0"), "inc_bolsas": Decimal("0"), "in_carbono": Decimal("0"),
            "in_combustibles": Decimal("0"), "ic_datos": Decimal("0"), "icl": Decimal("0"),
            "inpp": Decimal("0"), "ibua": Decimal("0"), "icui": Decimal("0"),
            "rete_iva": Decimal("0"), "rete_renta": Decimal("0"), "rete_ica": Decimal("0"),
            "total": Decimal("0"),
        }
    )

    for d in items:
        emp = d.get("empresa") or d.get("nombre_emisor") or ""
        grp = d.get("grupo") or ""
        tip = d.get("tipo_documento") or ""
        key = (emp, grp, tip)
        g = groups[key]
        for field in DECIMAL_FIELDS:
            raw = d.get(field)
            v = coerce_decimal_colombian(raw) or coerce_decimal(raw) or Decimal("0")
            g[field] = g.get(field, Decimal("0")) + v

    out = []
    for (emp, grp, tip), g in sorted(groups.items()):
        total_val = g.get("total", Decimal("0"))
        total_otros = (
            g.get("ica", Decimal("0")) + g.get("ic", Decimal("0")) + g.get("timbre", Decimal("0"))
            + g.get("inc", Decimal("0")) + g.get("inc_bolsas", Decimal("0")) + g.get("in_carbono", Decimal("0"))
            + g.get("in_combustibles", Decimal("0")) + g.get("ic_datos", Decimal("0")) + g.get("icl", Decimal("0"))
            + g.get("inpp", Decimal("0")) + g.get("ibua", Decimal("0")) + g.get("icui", Decimal("0"))
        )
        total_renta = g.get("rete_iva", Decimal("0")) + g.get("rete_renta", Decimal("0")) + g.get("rete_ica", Decimal("0"))
        subtotal = total_val - total_renta - total_otros - g.get("iva", Decimal("0"))

        out.append({
            "empresa": emp,
            "tipo_documento": tip,
            "grupo": grp,
            "subtotal": str(subtotal),
            "iva": str(g.get("iva", Decimal("0"))),
            "otros": str(total_otros),
            "retenciones": str(total_renta),
            "total": str(total_val),
        })
    return out


@app.get(f"{API_V1_PREFIX}/documentos/resumen", response_model=DocumentosResumenResponse)
async def resumen_documentos(
    empresa: Optional[str] = None,
    grupo: Optional[str] = None,
    tipo_documento: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
) -> DocumentosResumenResponse:
    items = _compute_resumen_items(empresa, grupo, tipo_documento, fecha_desde, fecha_hasta)
    return DocumentosResumenResponse(items=items)


@app.post(f"{API_V1_PREFIX}/resumen/import", response_model=ResumenImportResponse)
async def import_resumen(payload: ResumenImportRequest) -> ResumenImportResponse:
    """Importa Resumen pre-agregado (INFORME RELACION_FE): Empresa, Tipo De Documento, Grupo, Subtotal, IVA, Total_otros, Total_renta, Total"""
    start_time = datetime.utcnow()
    store = get_store()

    raw_rows = payload.rows or []
    if not raw_rows:
        raise HTTPException(status_code=400, detail="No se recibieron filas para importar")

    headers = payload.headers or (list(raw_rows[0].keys()) if raw_rows else [])
    cleaned_rows, row_errors = build_resumen_payload(raw_rows, headers)
    total_rows = len(raw_rows)
    inserted = len(cleaned_rows)

    store.replace_resumen(cleaned_rows, payload.file_name)

    processing_time = (datetime.utcnow() - start_time).total_seconds()
    msg = "Resumen importado correctamente"
    if inserted == 0 and total_rows > 0:
        msg = f"Ninguna fila importada. Verifique columnas: Empresa, Tipo De Documento, Grupo, Subtotal, IVA, Total_otros, Total_renta, Total. Detectadas: {list(headers)[:10]}"
    return ResumenImportResponse(
        success=True,
        message=msg,
        file_name=payload.file_name,
        total_rows=total_rows,
        inserted=inserted,
        rejected=len(row_errors),
        errors=row_errors,
        processing_time_seconds=round(processing_time, 2),
    )


def _get_resumen_report(
    empresa: Optional[str],
    grupo: Optional[str],
    tipo_documento: Optional[str],
) -> List[InformeReporteRow]:
    """Obtiene reporte desde resumen importado con filtros y formato colombiano."""
    items = get_store().get_resumen_rows()
    if empresa:
        items = [r for r in items if _filter_text(r.get("empresa"), empresa)]
    if grupo:
        items = [r for r in items if _filter_text(r.get("grupo"), grupo)]
    if tipo_documento:
        items = [r for r in items if _filter_text(r.get("tipo_documento"), tipo_documento)]

    rows: List[InformeReporteRow] = []
    sum_subtotal = Decimal("0.00")
    sum_iva = Decimal("0.00")
    sum_total_otros = Decimal("0.00")
    sum_total_renta = Decimal("0.00")
    sum_total = Decimal("0.00")

    for row in items:
        subtotal = row.get("subtotal", Decimal("0"))
        iva = row.get("iva", Decimal("0"))
        otros = row.get("total_otros", Decimal("0"))
        renta = row.get("total_renta", Decimal("0"))
        total_val = row.get("total", Decimal("0"))

        sum_subtotal += subtotal
        sum_iva += iva
        sum_total_otros += otros
        sum_total_renta += renta
        sum_total += total_val

        rows.append(InformeReporteRow(
            Empresa=str(row.get("empresa", "")),
            Tipo_de_documento=str(row.get("tipo_documento", "")),
            Grupo=str(row.get("grupo", "")),
            Subtotal=format_decimal_colombian(subtotal),
            IVA=format_decimal_colombian(iva),
            Total_otros=format_decimal_colombian(otros),
            Total_renta=format_decimal_colombian(renta),
            Total=format_decimal_colombian(total_val),
        ))

    rows.append(InformeReporteRow(
        Empresa=f"Total Acumulado ({len(rows)}) - Suma",
        Tipo_de_documento="",
        Grupo="",
        Subtotal=format_decimal_colombian(sum_subtotal),
        IVA=format_decimal_colombian(sum_iva),
        Total_otros=format_decimal_colombian(sum_total_otros),
        Total_renta=format_decimal_colombian(sum_total_renta),
        Total=format_decimal_colombian(sum_total),
    ))
    return rows


@app.get(f"{API_V1_PREFIX}/consolidado/reporte-fe", response_model=InformeReporteResponse)
async def get_reporte_informe(
    empresa: Optional[str] = None,
    grupo: Optional[str] = None,
    tipo_documento: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
) -> InformeReporteResponse:
    if get_store().get_resumen_rows():
        rows = _get_resumen_report(empresa, grupo, tipo_documento)
        return InformeReporteResponse(rows=rows)

    items = _compute_resumen_items(empresa, grupo, tipo_documento, fecha_desde, fecha_hasta)
    rows: List[InformeReporteRow] = []
    sum_subtotal = Decimal("0.00")
    sum_iva = Decimal("0.00")
    sum_total_otros = Decimal("0.00")
    sum_total_renta = Decimal("0.00")
    sum_total = Decimal("0.00")

    for row in items:
        subtotal = Decimal(row.get("subtotal", "0"))
        iva = Decimal(row.get("iva", "0"))
        otros = Decimal(row.get("otros", "0"))
        renta = Decimal(row.get("retenciones", "0"))
        total_val = Decimal(row.get("total", "0"))

        sum_subtotal += subtotal
        sum_iva += iva
        sum_total_otros += otros
        sum_total_renta += renta
        sum_total += total_val

        rows.append(InformeReporteRow(
            Empresa=str(row.get("empresa", "")),
            Tipo_de_documento=str(row.get("tipo_documento", "")),
            Grupo=str(row.get("grupo", "")),
            Subtotal=format_decimal_colombian(subtotal),
            IVA=format_decimal_colombian(iva),
            Total_otros=format_decimal_colombian(otros),
            Total_renta=format_decimal_colombian(renta),
            Total=format_decimal_colombian(total_val),
        ))

    rows.append(InformeReporteRow(
        Empresa=f"Total Acumulado ({len(rows)}) - Suma",
        Tipo_de_documento="",
        Grupo="",
        Subtotal=format_decimal_colombian(sum_subtotal),
        IVA=format_decimal_colombian(sum_iva),
        Total_otros=format_decimal_colombian(sum_total_otros),
        Total_renta=format_decimal_colombian(sum_total_renta),
        Total=format_decimal_colombian(sum_total),
    ))

    return InformeReporteResponse(rows=rows)


@app.post(f"{API_V1_PREFIX}/consolidado/import", response_model=ConsolidadoImportResponse)
async def import_consolidado(payload: ConsolidadoImportRequest) -> ConsolidadoImportResponse:
    start_time = datetime.utcnow()
    store = get_store()

    raw_rows = payload.rows or []
    if not raw_rows:
        raise HTTPException(status_code=400, detail="No se recibieron filas para importar")

    headers = payload.headers or (list(raw_rows[0].keys()) if raw_rows else None)
    cleaned_rows, row_errors = build_consolidado_payload(raw_rows, headers)
    total_rows = len(raw_rows)
    inserted = 0

    for batch in iter_batches(cleaned_rows, BATCH_SIZE):
        for row in batch:
            store.import_consolidado_row(row, payload.file_name)
            inserted += 1

    processing_time = (datetime.utcnow() - start_time).total_seconds()
    return ConsolidadoImportResponse(
        success=True,
        message="Consolidado importado correctamente",
        file_name=payload.file_name,
        total_rows=total_rows,
        inserted=inserted,
        rejected=len(row_errors),
        errors=row_errors,
        processing_time_seconds=round(processing_time, 2),
    )


@app.get(f"{API_V1_PREFIX}/consolidado/options", response_model=PivotOptionsResponse)
async def get_consolidado_options() -> PivotOptionsResponse:
    store = get_store()
    empresas = store.get_empresas_list()
    terceros = store.get_terceros_list()
    movimientos = store.get_consolidado_movimientos()
    cuentas = sorted(set(m.get("cuenta") for m in movimientos if m.get("cuenta")))
    periodos = sorted(set(m.get("periodo") for m in movimientos if m.get("periodo")))

    return PivotOptionsResponse(
        empresas=empresas,
        terceros=terceros,
        cuentas=cuentas,
        periodos=periodos,
    )


@app.get(f"{API_V1_PREFIX}/consolidado/pivot", response_model=PivotResponse)
async def get_pivot(
    empresa_id: Optional[int] = None,
    tercero_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    cuenta: Optional[str] = None,
    periodo: Optional[str] = None,
    group_by: Optional[str] = None,
) -> PivotResponse:
    group_keys = [k.strip() for k in (group_by or "empresa,tercero,cuenta,periodo").split(",") if k.strip()]
    allowed = {"empresa", "tercero", "cuenta", "periodo", "fecha"}
    group_keys = [k for k in group_keys if k in allowed]
    if not group_keys:
        group_keys = ["empresa", "tercero", "cuenta", "periodo"]

    items = get_store().get_consolidado_movimientos()

    if empresa_id:
        items = [m for m in items if m.get("empresa_id") == empresa_id]
    if tercero_id:
        items = [m for m in items if m.get("tercero_id") == tercero_id]
    if cuenta:
        items = [m for m in items if m.get("cuenta") == cuenta]
    if periodo:
        items = [m for m in items if m.get("periodo") == periodo]

    fd = coerce_date(fecha_desde) if fecha_desde else None
    fh = coerce_date(fecha_hasta) if fecha_hasta else None
    if fd or fh:
        items = [m for m in items if _filter_date(m.get("fecha"), fd, fh)]

    agg: Dict[Tuple, Dict[str, Any]] = defaultdict(lambda: {"debito": Decimal("0"), "credito": Decimal("0"), "movimientos": 0})
    for m in items:
        key_parts = []
        if "empresa" in group_keys:
            key_parts.append(m.get("_empresa_nombre", ""))
        if "tercero" in group_keys:
            key_parts.append(m.get("_tercero_nombre", ""))
        if "cuenta" in group_keys:
            key_parts.append(m.get("cuenta", ""))
        if "periodo" in group_keys:
            key_parts.append(m.get("periodo", ""))
        if "fecha" in group_keys:
            key_parts.append(m.get("fecha"))
        key = tuple(key_parts)

        agg[key]["debito"] += coerce_decimal(m.get("debito")) or Decimal("0")
        agg[key]["credito"] += coerce_decimal(m.get("credito")) or Decimal("0")
        agg[key]["movimientos"] += 1

    result_items = []
    for key, data in sorted(agg.items()):
        rec = {}
        for i, k in enumerate(group_keys):
            rec[k] = key[i] if i < len(key) else ""
        rec["debito"] = str(data["debito"])
        rec["credito"] = str(data["credito"])
        rec["movimientos"] = data["movimientos"]
        result_items.append(rec)

    return PivotResponse(items=result_items, group_by=group_keys)


@app.get(f"{API_V1_PREFIX}/health")
async def health_check() -> Dict[str, str]:
    store = get_store()
    counts = store.counts()
    db_ok = check_database_connection() if is_database_configured() else None
    return {
        "status": "ok" if db_ok is not False else "degraded",
        "mode": store.mode,
        "database": "connected" if db_ok else ("not_configured" if db_ok is None else "error"),
        "documentos": str(counts["documentos"]),
        "resumen": str(counts["resumen"]),
        "consolidado": str(counts["consolidado"]),
        "emisiones": str(counts.get("emisiones", 0)),
    }
