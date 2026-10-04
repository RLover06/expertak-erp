"""Esquemas API — Facturación electrónica (emisión DIAN)."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ModoEmision = Literal["habilitacion", "produccion"]


class EmitirFacturaRequest(BaseModel):
    """
    Emite factura ante DIAN.
    `invoice` debe cumplir estructura InvoiceDto del motor DIAN (UBL + control).
    Ver docs/fe_invoice_ejemplo.json
    """

    modo: ModoEmision = Field(
        default="habilitacion",
        description="habilitacion → send_test (sets DIAN); produccion → send",
    )
    invoice: Dict[str, Any] = Field(..., description="Payload completo tipo InvoiceDto")


class AdquirenteSimple(BaseModel):
    """Datos del adquirente para la API simple (§15)."""

    nit: str
    nombre: str
    email: Optional[str] = None
    direccion: Optional[str] = None
    municipio: Optional[str] = None
    departamento: Optional[str] = None
    tipo_documento: str = Field(default="31", description="§13.2.7.1 (31=NIT, 13=CC, ...)")
    municipio_code: Optional[str] = Field(default=None, description="AddressID (DANE), p. ej. 11001")
    departamento_code: Optional[str] = Field(default=None, description="CountrySubentityCode, p. ej. 11")
    tax_level_code: str = Field(default="R-99-PN", description="Responsabilidad fiscal")
    telefono: Optional[str] = None


class ItemSimple(BaseModel):
    """Línea de factura para la API simple (§15)."""

    descripcion: str
    cantidad: float = Field(..., gt=0, description="Debe ser > 0 (§8)")
    precio_unitario: float = Field(..., ge=0)
    iva_porcentaje: float = Field(default=19, ge=0)
    descuento: float = Field(default=0, ge=0)
    codigo_producto: Optional[str] = None
    unidad_medida: str = "EA"


class FacturaSimpleRequest(BaseModel):
    """
    Entrada amigable de facturación (§15). El backend calcula subtotales, IVA, total,
    consecutivo, fechas y CUFE, y arma el InvoiceDto completo a partir de la
    configuración de la empresa emisora (fe_empresas_config).
    """

    empresa_nit: str = Field(..., description="NIT del emisor; debe existir en fe_empresas_config")
    adquirente: AdquirenteSimple
    items: List[ItemSimple] = Field(..., min_length=1)
    forma_pago: str = Field(default="1", description="§13.2.8.4 (1=contado, 2=crédito)")
    medio_pago: str = Field(default="10", description="§13.2.8.4 (10=efectivo, ...)")
    fecha_vencimiento: Optional[str] = None
    notas: Optional[str] = None
    modo: ModoEmision = "habilitacion"
    enviar: bool = Field(
        default=True,
        description="True → transmite a DIAN; False → guarda como BORRADOR y devuelve el DTO armado",
    )


class FacturaSimpleResponse(BaseModel):
    success: bool
    estado: str
    cufe: Optional[str] = None
    factura_id: Optional[str] = None
    emision_id: Optional[str] = None
    factura_numero: Optional[str] = None
    subtotal: str
    iva: str
    total: str
    enviado: bool
    modo: str
    message: str
    errores: List[str] = Field(default_factory=list)
    invoice: Optional[Dict[str, Any]] = Field(
        default=None, description="InvoiceDto armado (útil para revisar antes de transmitir)"
    )


class EmitirFacturaResponse(BaseModel):
    success: bool
    modo: str
    message: str
    estado: str = "PENDIENTE"
    cufe: Optional[str] = None
    dian_status_code: Optional[int] = None
    dian_status_description: Optional[str] = None
    dian_response: Optional[str] = None
    errores: List[str] = Field(default_factory=list)
    factura_id: Optional[str] = None
    emision_id: Optional[str] = None
    engine: Optional[str] = None


class EmpresaCredenciales(BaseModel):
    """Estado de credenciales/habilitación de una empresa, SIN exponer secretos."""

    listo_para_emitir: bool
    faltantes: List[str] = Field(default_factory=list, description="Campos requeridos ausentes")
    tiene_clave_tecnica: bool = False
    tiene_software_id: bool = False
    tiene_software_pin: bool = False
    tiene_certificado: bool = False
    tiene_resolucion: bool = False
    tiene_rango: bool = False


class EmpresaConfigResumen(BaseModel):
    """Fila para el selector de empresas del formulario (sin secretos)."""

    nit: str
    razon_social: Optional[str] = None
    prefijo: Optional[str] = None
    ambiente: Optional[str] = None
    listo_para_emitir: bool = False


class EmpresaConfigDetalle(BaseModel):
    """Configuración no secreta de una empresa + estado de credenciales."""

    nit: str
    razon_social: Optional[str] = None
    prefijo: Optional[str] = None
    rango_desde: Optional[int] = None
    rango_hasta: Optional[int] = None
    numero_actual: Optional[int] = None
    resolucion_numero: Optional[str] = None
    resolucion_fecha_desde: Optional[str] = None
    resolucion_fecha_hasta: Optional[str] = None
    ambiente: Optional[str] = None
    tipo_documento: Optional[str] = None
    tax_level_code: Optional[str] = None
    direccion: Optional[str] = None
    departamento: Optional[str] = None
    departamento_code: Optional[str] = None
    municipio_code: Optional[str] = None
    ciudad: Optional[str] = None
    credenciales: EmpresaCredenciales


class FePreflightCheck(BaseModel):
    label: str
    path: str
    ok: bool
    optional: bool = False


class DianStatusResponse(BaseModel):
    ready: bool
    engine: str
    reference_app_path: Optional[str] = None
    reference_app_exists: bool = False
    http_service_url: Optional[str] = None
    http_service_reachable: bool = False
    certificate_configured: bool = False
    detail: Optional[str] = None
    blockers: List[str] = Field(default_factory=list)


class FePreflightResponse(BaseModel):
    ready: bool
    engine: str
    checks: List[FePreflightCheck]
    blockers: List[str]
    next_steps: List[str]


class FeEmisionRecord(BaseModel):
    id: int
    modo: str
    factura_numero: Optional[str] = None
    estado: str
    created_at: str
    engine: Optional[str] = None
    dian_status_code: Optional[int] = None
    cufe: Optional[str] = None
    dian_response_preview: Optional[str] = None


class FeFacturaResumen(BaseModel):
    id: int
    empresa_nit: str
    cufe: Optional[str] = None
    factura_numero: Optional[str] = None
    estado: str
    adquirente_nit: Optional[str] = None
    adquirente_nombre: Optional[str] = None
    subtotal: Optional[str] = None
    iva: Optional[str] = None
    total: Optional[str] = None
    ambiente: str
    created_at: str


class FeFacturaDetalle(FeFacturaResumen):
    prefijo: Optional[str] = None
    numero: Optional[int] = None
    fecha_emision: Optional[str] = None
    hora_emision: Optional[str] = None
    application_response: Optional[str] = None
    items: List[Dict[str, Any]] = Field(default_factory=list)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
