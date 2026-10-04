from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ImportRowsRequest(BaseModel):
    rows: List[Dict[str, Any]]
    file_name: Optional[str] = None


class ConsolidadoImportRequest(BaseModel):
    rows: List[Dict[str, Any]]
    file_name: Optional[str] = None
    headers: Optional[List[str]] = None  # Encabezados del Excel para referencias de celda


class ResumenImportRequest(BaseModel):
    """Importación de Resumen pre-agregado (INFORME RELACION_FE): Empresa, Tipo De Documento, Grupo, Subtotal, IVA, Total_otros, Total_renta, Total"""
    rows: List[Dict[str, Any]]
    file_name: Optional[str] = None
    headers: Optional[List[str]] = None  # Orden de columnas para fallback por posicion


class ImportError(BaseModel):
    row_number: int
    errors: List[str]


class ImportResponse(BaseModel):
    success: bool
    message: str
    file_name: Optional[str]
    file_size: Optional[int]
    total_rows: int
    inserted: int
    duplicates: int
    rejected: int
    errors: List[ImportError]
    processing_time_seconds: float


class DocumentosResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int


class ConsolidadoImportResponse(BaseModel):
    success: bool
    message: str
    file_name: Optional[str]
    total_rows: int
    inserted: int
    rejected: int
    errors: List[ImportError]
    processing_time_seconds: float


class ResumenImportResponse(BaseModel):
    success: bool
    message: str
    file_name: Optional[str]
    total_rows: int
    inserted: int
    rejected: int
    errors: List[ImportError]
    processing_time_seconds: float


class PivotOptionsResponse(BaseModel):
    empresas: List[Dict[str, Any]]
    terceros: List[Dict[str, Any]]
    cuentas: List[str]
    periodos: List[str]


class PivotResponse(BaseModel):
    items: List[Dict[str, Any]]
    group_by: List[str]


class DocumentosResumenResponse(BaseModel):
    items: List[Dict[str, Any]]


class InformeReporteRow(BaseModel):
    Empresa: str
    Tipo_de_documento: str
    Grupo: str
    Subtotal: str
    IVA: str
    Total_otros: str
    Total_renta: str
    Total: str


class InformeReporteResponse(BaseModel):
    rows: List[InformeReporteRow]
