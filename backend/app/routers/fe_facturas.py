"""Rutas API — emisión facturación electrónica DIAN."""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException

from .. import fe_estados
from ..dian import get_dian_emitter
from ..dian.cufe import compute_cufe, extract_cufe_from_response
from ..dian.dian_response import DianResult, interpret_response
from ..dian.factura_mapper import MapperError, build_invoice_dto
from ..dian.preflight import run_fe_preflight
from ..fe_estados import TransicionInvalidaError
from ..schemas_fe import (
    DianStatusResponse,
    EmitirFacturaRequest,
    EmitirFacturaResponse,
    EmpresaConfigDetalle,
    EmpresaConfigResumen,
    EmpresaCredenciales,
    FacturaSimpleRequest,
    FacturaSimpleResponse,
    FeEmisionRecord,
    FeFacturaDetalle,
    FeFacturaResumen,
    FePreflightCheck,
    FePreflightResponse,
)
from ..store import get_store

router = APIRouter(prefix="/fe", tags=["Facturación electrónica"])

_DIAN_RESPONSE_PREVIEW_LEN = 50000

# Colombia: UTC-05:00, sin horario de verano (§7 fechas/horas).
_BOGOTA_TZ = timezone(timedelta(hours=-5))


def _get(invoice: Dict[str, Any], *path: str) -> Optional[Any]:
    node: Any = invoice
    for key in path:
        if isinstance(node, dict):
            node = node.get(key)
        else:
            return None
    return node


def _extract_factura_numero(invoice: Dict[str, Any]) -> Optional[str]:
    value = invoice.get("ID")
    return str(value) if value else None


def _parse_numero(invoice: Dict[str, Any]) -> Optional[int]:
    factura_id = invoice.get("ID")
    if not factura_id:
        return None
    factura_id = str(factura_id)
    prefijo = _get(invoice, "Control", "Prefix") or ""
    candidate = factura_id[len(prefijo):] if prefijo and factura_id.startswith(prefijo) else factura_id
    digits = re.sub(r"\D", "", candidate)
    return int(digits) if digits else None


def _sum_iva(invoice: Dict[str, Any]) -> str:
    tax_totals = _get(invoice, "Amounts", "TaxTotals")
    if not isinstance(tax_totals, list):
        return "0"
    total = 0.0
    for t in tax_totals:
        if isinstance(t, dict) and t.get("TaxAmount") is not None:
            try:
                total += float(t["TaxAmount"])
            except (TypeError, ValueError):
                pass
    return f"{total:.2f}"


def _build_items(invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    lines = invoice.get("Lines")
    if not isinstance(lines, list):
        return []
    items: List[Dict[str, Any]] = []
    for line in lines:
        if not isinstance(line, dict):
            continue
        items.append({
            "descripcion": line.get("Description") or "",
            "cantidad": line.get("Quantity") or "0",
            "precio_unitario": line.get("PriceAmount") or "0",
            "descuento": "0",
            "iva_porcentaje": line.get("TaxPercent") or "0",
            "subtotal": line.get("LineExtensionAmount") or "0",
            "codigo_producto": line.get("SellersItemID") or line.get("AdditionalItemID"),
            "unidad_medida": "EA",
        })
    return items


def _build_factura_record(
    invoice: Dict[str, Any], modo: str, cufe: Optional[str], estado: str, full_response: Optional[str]
) -> Dict[str, Any]:
    return {
        "empresa_nit": str(_get(invoice, "Company", "CompanyID") or ""),
        "cufe": cufe,
        "prefijo": _get(invoice, "Control", "Prefix"),
        "numero": _parse_numero(invoice),
        "factura_numero": _extract_factura_numero(invoice),
        "fecha_emision": invoice.get("IssueDate"),
        "hora_emision": invoice.get("IssueTime"),
        "estado": estado,
        "adquirente_nit": str(_get(invoice, "Customer", "ID") or "") or None,
        "adquirente_nombre": _get(invoice, "Customer", "PartyName"),
        "subtotal": _get(invoice, "Amounts", "LineExtensionAmount"),
        "iva": _sum_iva(invoice),
        "total": _get(invoice, "Amounts", "PayableAmount")
        or _get(invoice, "Amounts", "TaxInclusiveAmount"),
        "application_response": full_response,
        "ambiente": modo,
        "intentos_transmision": 1,
    }


@router.get("/dian-status", response_model=DianStatusResponse)
async def dian_status() -> DianStatusResponse:
    """Verifica si el motor DIAN (referencia) está listo para emitir."""
    st = get_dian_emitter().status()
    return DianStatusResponse(**st)


# Campos de fe_empresas_config requeridos para poder transmitir a la DIAN.
# (etiqueta legible para el aviso del formulario).
_EMISION_REQUERIDOS = (
    ("prefijo", "Prefijo de numeración"),
    ("resolucion_numero", "Número de resolución DIAN"),
    ("rango_desde", "Rango autorizado (desde)"),
    ("rango_hasta", "Rango autorizado (hasta)"),
    ("software_id", "Software ID"),
    ("software_pin", "PIN del software"),
    ("clave_tecnica", "Clave técnica"),
    ("cert_firma_path", "Certificado de firma (.pfx)"),
)


def _empresa_credenciales(cfg_with_secrets: Dict[str, Any]) -> EmpresaCredenciales:
    """Deriva el estado de credenciales sin exponer NUNCA los valores secretos."""
    faltantes = [label for field, label in _EMISION_REQUERIDOS if not cfg_with_secrets.get(field)]
    return EmpresaCredenciales(
        listo_para_emitir=len(faltantes) == 0,
        faltantes=faltantes,
        tiene_clave_tecnica=bool(cfg_with_secrets.get("clave_tecnica")),
        tiene_software_id=bool(cfg_with_secrets.get("software_id")),
        tiene_software_pin=bool(cfg_with_secrets.get("software_pin")),
        tiene_certificado=bool(cfg_with_secrets.get("cert_firma_path")),
        tiene_resolucion=bool(cfg_with_secrets.get("resolucion_numero")),
        tiene_rango=bool(cfg_with_secrets.get("rango_desde") and cfg_with_secrets.get("rango_hasta")),
    )


@router.get("/empresas", response_model=List[EmpresaConfigResumen])
async def listar_empresas() -> List[EmpresaConfigResumen]:
    """Empresas configuradas (fe_empresas_config) para el selector del formulario.

    Incluye `listo_para_emitir` para que el formulario muestre el aviso de credenciales,
    pero NO devuelve secretos.
    """
    store = get_store()
    out: List[EmpresaConfigResumen] = []
    for cfg in store.list_empresa_configs(include_secrets=True):
        cred = _empresa_credenciales(cfg)
        out.append(
            EmpresaConfigResumen(
                nit=cfg["nit"],
                razon_social=cfg.get("razon_social"),
                prefijo=cfg.get("prefijo"),
                ambiente=cfg.get("ambiente"),
                listo_para_emitir=cred.listo_para_emitir,
            )
        )
    return out


@router.get("/empresas/{nit}", response_model=EmpresaConfigDetalle)
async def obtener_empresa(nit: str) -> EmpresaConfigDetalle:
    """Configuración no secreta de una empresa + estado de credenciales para emitir."""
    store = get_store()
    cfg = store.get_empresa_config(nit, include_secrets=True)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"No existe configuración para el NIT {nit}.")
    cred = _empresa_credenciales(cfg)
    publico = {k: v for k, v in cfg.items() if k not in ("clave_tecnica", "software_pin", "software_id", "test_id", "cert_firma_path")}
    return EmpresaConfigDetalle(**publico, credenciales=cred)


@router.get("/preflight", response_model=FePreflightResponse)
async def fe_preflight() -> FePreflightResponse:
    """Checklist completo antes de la primera emisión de habilitación."""
    data = run_fe_preflight()
    return FePreflightResponse(
        ready=data["ready"],
        engine=data["engine"],
        checks=[FePreflightCheck(**c) for c in data["checks"]],
        blockers=data["blockers"],
        next_steps=data["next_steps"],
    )


class _EmitResult:
    """Resultado de emitir + persistir, compartido por /emitir y /emitir-simple."""

    def __init__(
        self,
        ok: bool,
        message: str,
        status_code: Optional[int],
        engine: str,
        dian: DianResult,
        cufe: Optional[str],
        factura_id: int,
        emision_id: int,
        response_text: Optional[str],
    ) -> None:
        self.ok = ok
        self.message = message
        self.status_code = status_code
        self.engine = engine
        self.dian = dian
        self.cufe = cufe
        self.factura_id = factura_id
        self.emision_id = emision_id
        self.response_text = response_text


def _transmit(
    invoice: Dict[str, Any], modo: str
) -> Tuple[bool, str, Optional[int], Optional[str], str, DianResult, Optional[str]]:
    """Transmite al motor, deriva el estado real DIAN y calcula el CUFE (sin persistir)."""
    emitter = get_dian_emitter()
    ok, message, status_code, response_text, engine = emitter.emit(invoice, modo)
    # Estado real según la DIAN (no por éxito de transporte).
    dian = interpret_response(response_text, transport_ok=ok, modo=modo)
    # CUFE real: determinista desde el payload (§11.2); respaldo desde la respuesta.
    cufe = compute_cufe(invoice) or extract_cufe_from_response(response_text)
    return ok, message, status_code, response_text, engine, dian, cufe


def _log_and_emision(
    store: Any,
    factura_id: int,
    invoice: Dict[str, Any],
    modo: str,
    ok: bool,
    message: str,
    status_code: Optional[int],
    response_text: Optional[str],
    engine: str,
    dian: DianResult,
    cufe: Optional[str],
) -> int:
    """Persiste el log de transmisión (XML completo) y el historial de emisión."""
    servicio_ws = "SendTestSetAsync" if modo == "habilitacion" else "SendBillSync"
    store.save_fe_log({
        "factura_id": factura_id,
        "servicio_ws": servicio_ws,
        "exitoso": ok,
        "codigo_respuesta": dian.status_code or (str(status_code) if status_code else None),
        "mensaje_dian": "\n".join(dian.errors) if dian.errors else message,
        "xml_enviado": json.dumps(invoice, ensure_ascii=False),
        "xml_respuesta": response_text or "",
    })
    return store.save_fe_emision({
        "modo": modo,
        "factura_numero": _extract_factura_numero(invoice),
        "estado": dian.estado,
        "engine": engine,
        "dian_status_code": status_code,
        "dian_response": (response_text or "")[:_DIAN_RESPONSE_PREVIEW_LEN] or None,
        "invoice_payload": invoice,
        "cufe": cufe,
    })


def _emit_and_persist(
    invoice: Dict[str, Any], modo: str, store: Any, req_payload: Optional[Dict[str, Any]] = None
) -> _EmitResult:
    """Emite vía motor, deriva el estado real DIAN, calcula CUFE y persiste todo (crea fila)."""
    ok, message, status_code, response_text, engine, dian, cufe = _transmit(invoice, modo)

    record = _build_factura_record(invoice, modo, cufe, dian.estado, response_text)
    if req_payload is not None:
        # Guardar el request permite re-emitir una corrección (corregir → /enviar).
        record["invoice_payload"] = req_payload
    factura_id = store.save_fe_factura(record, _build_items(invoice))
    emision_id = _log_and_emision(
        store, factura_id, invoice, modo, ok, message, status_code, response_text, engine, dian, cufe
    )

    return _EmitResult(
        ok, message, status_code, engine, dian, cufe, factura_id, emision_id, response_text
    )


@router.post("/emitir", response_model=EmitirFacturaResponse)
async def emitir_factura(payload: EmitirFacturaRequest) -> EmitirFacturaResponse:
    """
    Genera XML UBL, firma y envía a DIAN (vía motor de referencia).

    - **habilitacion**: ambiente de pruebas / sets DIAN (`SendTestSetAsync`)
    - **produccion**: envío producción (`SendBillSync`)

    El estado se deriva de la validación real de la DIAN (`IsValid`), no del transporte.
    El CUFE se calcula de forma determinista (§11.2) y se contrasta con la respuesta.
    """
    res = _emit_and_persist(payload.invoice, payload.modo, get_store())
    preview = (res.response_text or "")[:500] if res.response_text else None

    if not res.ok or res.dian.estado == "RECHAZADA":
        raise HTTPException(
            status_code=502,
            detail={
                "message": res.message,
                "estado": res.dian.estado,
                "cufe": res.cufe,
                "dian_status_code": res.status_code,
                "dian_status_description": res.dian.status_description,
                "errores": res.dian.errors,
                "dian_response_preview": preview,
                "engine": res.engine,
                "factura_id": str(res.factura_id),
                "emision_id": str(res.emision_id),
            },
        )

    return EmitirFacturaResponse(
        success=True,
        modo=payload.modo,
        message=res.message,
        estado=res.dian.estado,
        cufe=res.cufe,
        dian_status_code=res.status_code,
        dian_status_description=res.dian.status_description,
        dian_response=preview,
        errores=res.dian.errors,
        factura_id=str(res.factura_id),
        emision_id=str(res.emision_id),
        engine=res.engine,
    )


def _preview_consecutivo(empresa: Dict[str, Any]) -> int:
    """Número tentativo para un borrador (no consume el consecutivo)."""
    base = empresa.get("numero_actual")
    if base is None:
        rango_desde = empresa.get("rango_desde")
        base = (rango_desde - 1) if rango_desde else 0
    return base + 1


@router.post("/emitir-simple", response_model=FacturaSimpleResponse)
async def emitir_simple(payload: FacturaSimpleRequest) -> FacturaSimpleResponse:
    """
    API simple de facturación (§15). Recibe un JSON amigable (cliente + ítems), arma el
    InvoiceDto a partir de fe_empresas_config, calcula totales (round-half-to-even, §8),
    consecutivo, fechas y CUFE.

    - `enviar=true`  → transmite a DIAN y devuelve el estado real.
    - `enviar=false` → guarda como BORRADOR (consecutivo *tentativo*, no consumido) y
      devuelve el InvoiceDto armado para revisión.
    """
    store = get_store()
    empresa = store.get_empresa_config(payload.empresa_nit, include_secrets=True)
    if empresa is None:
        raise HTTPException(
            status_code=400,
            detail=f"No existe configuración para el NIT {payload.empresa_nit} en fe_empresas_config.",
        )

    req = payload.model_dump()

    if not payload.enviar:
        # BORRADOR: tolera configuración incompleta (validar=False) → se puede crear y
        # revisar SIN credenciales DIAN. No consume consecutivo ni fija CUFE. Guarda el
        # REQUEST en invoice_payload para reconstruir al enviar con la config vigente.
        consecutivo = _preview_consecutivo(empresa)
        invoice = build_invoice_dto(req, empresa, consecutivo, validar=False)
        amounts = invoice["Amounts"]
        record = _build_factura_record(invoice, payload.modo, None, fe_estados.BORRADOR, None)
        record["numero"] = None
        record["intentos_transmision"] = 0
        record["invoice_payload"] = req
        factura_id = store.save_fe_factura(record, _build_items(invoice))
        return FacturaSimpleResponse(
            success=True,
            estado=fe_estados.BORRADOR,
            cufe=None,
            factura_id=str(factura_id),
            factura_numero=invoice["ID"],
            subtotal=amounts["LineExtensionAmount"],
            iva=amounts["TaxTotals"][0]["TaxAmount"],
            total=amounts["PayableAmount"],
            enviado=False,
            modo=payload.modo,
            message=(
                "Borrador creado (no transmitido). Consecutivo y CUFE tentativos "
                "(no consumidos): se asignan en firme solo al enviar."
            ),
            invoice=invoice,
        )

    # enviar=true → emisión directa: exige credenciales completas ANTES de consumir folio.
    faltantes = _empresa_credenciales(empresa).faltantes
    if faltantes:
        raise HTTPException(
            status_code=409,
            detail=(
                f"La empresa {payload.empresa_nit} no puede emitir todavía. "
                f"Faltan en fe_empresas_config: {', '.join(faltantes)}."
            ),
        )
    try:
        consecutivo = store.reserve_consecutivo(payload.empresa_nit)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    try:
        invoice = build_invoice_dto(req, empresa, consecutivo, validar=True)
    except MapperError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    amounts = invoice["Amounts"]
    subtotal = amounts["LineExtensionAmount"]
    iva = amounts["TaxTotals"][0]["TaxAmount"]
    total = amounts["PayableAmount"]

    res = _emit_and_persist(invoice, payload.modo, store, req_payload=req)
    success = res.ok and res.dian.estado != "RECHAZADA"
    return FacturaSimpleResponse(
        success=success,
        estado=res.dian.estado,
        cufe=res.cufe,
        factura_id=str(res.factura_id),
        emision_id=str(res.emision_id),
        factura_numero=invoice["ID"],
        subtotal=subtotal,
        iva=iva,
        total=total,
        enviado=True,
        modo=payload.modo,
        message=res.message,
        errores=res.dian.errors,
        invoice=invoice,
    )


@router.get("/emisiones", response_model=List[FeEmisionRecord])
async def listar_emisiones(limit: int = 50) -> List[FeEmisionRecord]:
    """Historial de intentos de emisión (Supabase o memoria según DATABASE_URL)."""
    items = get_store().list_fe_emisiones(limit=limit)
    return [
        FeEmisionRecord(
            id=r["id"],
            modo=r["modo"],
            factura_numero=r.get("factura_numero"),
            estado=r["estado"],
            created_at=r["created_at"],
            engine=r.get("engine"),
            dian_status_code=r.get("dian_status_code"),
            cufe=r.get("cufe"),
            dian_response_preview=(r.get("dian_response") or "")[:300] or None,
        )
        for r in items
    ]


@router.get("/facturas", response_model=List[FeFacturaResumen])
async def listar_facturas(limit: int = 50) -> List[FeFacturaResumen]:
    """Facturas persistidas (fe_facturas) con su estado real DIAN."""
    return [FeFacturaResumen(**r) for r in get_store().list_fe_facturas(limit=limit)]


@router.get("/facturas/{factura_id}", response_model=FeFacturaDetalle)
async def obtener_factura(factura_id: int) -> FeFacturaDetalle:
    """Detalle de una factura: cabecera, ítems y log de transmisión."""
    data = get_store().get_fe_factura(factura_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    data.pop("invoice_payload", None)
    return FeFacturaDetalle(**data)


@router.post("/facturas/{factura_id}/enviar", response_model=FacturaSimpleResponse)
async def enviar_borrador(
    factura_id: int, modo: ModoEmision = "habilitacion"
) -> FacturaSimpleResponse:
    """
    Transmite a la DIAN un BORRADOR ya persistido (flujo BORRADOR → PENDIENTE →
    VALIDADA/RECHAZADA).

    Recién aquí se **consume el consecutivo** (reserva atómica) y se estampa el CUFE
    definitivo. La máquina de estados (fe_estados) bloquea enviar una factura que no
    esté en BORRADOR/ERROR/OFFLINE (p. ej. una VALIDADA o RECHAZADA).
    """
    store = get_store()
    factura = store.get_fe_factura(factura_id)
    if factura is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    req = factura.get("invoice_payload")
    if not req:
        raise HTTPException(
            status_code=400,
            detail="El borrador no tiene datos para emitir; recréalo vía /emitir-simple.",
        )

    # 1) Validar que el estado actual admite pasar a PENDIENTE (bloquea terminales).
    try:
        fe_estados.validar_transicion(factura["estado"], fe_estados.PENDIENTE)
    except TransicionInvalidaError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # 2) Credenciales completas ANTES de consumir folio (config vigente, ya cargada).
    empresa = store.get_empresa_config(factura["empresa_nit"], include_secrets=True)
    if empresa is None:
        raise HTTPException(
            status_code=400,
            detail=f"No existe configuración para el NIT {factura['empresa_nit']} en fe_empresas_config.",
        )
    faltantes = _empresa_credenciales(empresa).faltantes
    if faltantes:
        raise HTTPException(
            status_code=409,
            detail=(
                f"La empresa {factura['empresa_nit']} no puede emitir todavía. "
                f"Faltan en fe_empresas_config: {', '.join(faltantes)}."
            ),
        )

    # 3) Consumir el consecutivo ahora (no antes): así no quedan huecos por borradores.
    try:
        consecutivo = store.reserve_consecutivo(factura["empresa_nit"])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # 4) Reconstruir el InvoiceDto definitivo con la configuración vigente y el folio real.
    req = {**req, "modo": modo}
    try:
        invoice = build_invoice_dto(req, empresa, consecutivo, validar=True)
    except MapperError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    prefijo = str((invoice.get("Control") or {}).get("Prefix") or "")

    # 5) BORRADOR → PENDIENTE (en transmisión), con el número definitivo.
    store.update_fe_factura_estado(
        factura_id,
        fe_estados.PENDIENTE,
        numero=consecutivo,
        prefijo=prefijo,
        factura_numero=invoice["ID"],
        ambiente=modo,
    )

    # 6) Transmitir y derivar el estado real DIAN.
    ok, message, status_code, response_text, engine, dian, cufe = _transmit(invoice, modo)
    emision_id = _log_and_emision(
        store, factura_id, invoice, modo, ok, message, status_code, response_text, engine, dian, cufe
    )

    # 7) PENDIENTE → VALIDADA | RECHAZADA | ENVIADA | ERROR.
    store.update_fe_factura_estado(
        factura_id,
        dian.estado,
        cufe=cufe,
        fecha_emision=invoice.get("IssueDate"),
        hora_emision=invoice.get("IssueTime"),
        application_response=response_text,
        intentos_transmision=(factura.get("intentos_transmision") or 0) + 1,
        fecha_transmision=datetime.now(_BOGOTA_TZ),
    )

    amounts = invoice["Amounts"]
    success = ok and dian.estado != fe_estados.RECHAZADA
    return FacturaSimpleResponse(
        success=success,
        estado=dian.estado,
        cufe=cufe,
        factura_id=str(factura_id),
        emision_id=str(emision_id),
        factura_numero=invoice["ID"],
        subtotal=amounts["LineExtensionAmount"],
        iva=amounts["TaxTotals"][0]["TaxAmount"],
        total=amounts["PayableAmount"],
        enviado=True,
        modo=modo,
        message=message,
        errores=dian.errors,
        invoice=invoice,
    )


@router.post("/facturas/{factura_id}/corregir", response_model=FeFacturaResumen)
async def corregir_factura(factura_id: int) -> FeFacturaResumen:
    """
    Corrige una factura RECHAZADA generando un BORRADOR NUEVO (clona cabecera e ítems).

    La factura original permanece RECHAZADA de forma permanente; la nueva queda
    enlazada vía ``factura_origen_id``. Este es el único camino para "reabrir" una
    rechazada: no se edita la original (la máquina de estados lo prohíbe).
    """
    store = get_store()
    try:
        nueva = store.clonar_factura_borrador(factura_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if nueva is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return FeFacturaResumen(**nueva)
