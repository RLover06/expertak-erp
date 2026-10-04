"""
Mapper de la API simple (§15): JSON amigable → InvoiceDto del motor DIAN.

El formulario web / la API simple NO envían XML. Envían un JSON sencillo (cliente, ítems,
formas de pago) y este mapper construye el InvoiceDto completo usando la configuración de la
empresa emisora (fe_empresas_config). El backend calcula subtotales, IVA y total con
redondeo round-half-to-even (§8 del Anexo v1.9).

────────────────────────────────────────────────────────────────────────────────────────
NOTA PARA FASE FUTURA — XML firmado real (no implementar ahora):

Hoy, el log de transmisión guarda en `xml_enviado` el JSON que Expertak envía al motor, NO
el XML UBL firmado (XAdES-EPES) que realmente se transmite a la DIAN. El XML firmado solo
existe dentro del motor de referencia.

Para capturarlo en el futuro hay que exponerlo desde el motor:

  Archivo del motor:
    application/use_cases/invoice/create_invoice_case.py

  El método `_create()` (≈ línea 48-62) YA produce la variable `signed_invoice`
  (el XML UBL firmado como string), pero `send()` y `send_test()` la descartan:
    - `send()`      retorna solo `messages`            (≈ línea 90)
    - `send_test()` retorna solo `{ "status", "text" }` (≈ línea 106)

  Cambio futuro en el motor (cuando se controle ese repo):
    1) En `send()` / `send_test()`, incluir `signed_invoice` en el retorno, p. ej.:
         return { "status": ..., "text": ..., "signed_xml": signed_invoice }
    2) Exponerlo en las rutas HTTP de
         interfaces/api/routes/invoice_routes.py
       (`/api/invoice/create_invoice` y `/api/invoice/send_test`).

  Luego, en Expertak:
    - leer `signed_xml` de la respuesta del motor en dian/emitter.py, y
    - guardarlo en `fe_facturas.xml_firmado` y `fe_log_transmision.xml_enviado`.

  Campo exacto a exponer: la variable `signed_invoice` retornada por `_create()`.
────────────────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Dict, List

# Colombia: UTC-05:00, sin horario de verano (§7 fechas/horas).
_BOGOTA_TZ = timezone(timedelta(hours=-5))

# Campos mínimos de configuración para construir un InvoiceDto emisible.
_CONFIG_REQUERIDOS = (
    "prefijo",
    "software_id",
    "software_pin",
    "clave_tecnica",
    "resolucion_numero",
)

_IVA_SCHEME_ID = "01"
_IVA_SCHEME_NAME = "IVA"


class MapperError(ValueError):
    """Datos insuficientes/ inválidos para construir el InvoiceDto."""


def _money(value: Decimal) -> str:
    """Redondeo round-half-to-even a 2 decimales (NTC 3711 / §8)."""
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))


def _validate_config(empresa: Dict[str, Any]) -> None:
    faltantes = [c for c in _CONFIG_REQUERIDOS if not empresa.get(c)]
    if faltantes:
        raise MapperError(
            "Configuración de empresa incompleta en fe_empresas_config para "
            f"NIT {empresa.get('nit')}: faltan {', '.join(faltantes)}."
        )


def _now_bogota() -> datetime:
    return datetime.now(_BOGOTA_TZ)


def build_invoice_dto(
    req: Dict[str, Any],
    empresa: Dict[str, Any],
    consecutivo: int,
    validar: bool = True,
) -> Dict[str, Any]:
    """
    Construye el InvoiceDto (mismo formato que docs/fe_piloto.json).

    `req`      : FacturaSimpleRequest serializado (model_dump).
    `empresa`  : fe_empresas_config con secretos (include_secrets=True).
    `consecutivo`: número ya reservado para esta factura.
    `validar`  : si es True, exige credenciales completas (emisión real). Si es False
                 (modo BORRADOR), tolera config incompleta y rellena con vacíos, de modo
                 que se pueda crear/revisar un borrador SIN credenciales DIAN cargadas.
    """
    if validar:
        _validate_config(empresa)

    modo = req.get("modo", "habilitacion")
    profile = "2" if modo == "habilitacion" else "1"
    prefijo = str(empresa.get("prefijo") or "")

    ahora = _now_bogota()
    issue_date = ahora.strftime("%Y-%m-%d")
    issue_time = ahora.strftime("%H:%M:%S") + "-05:00"

    # --- Líneas + acumulados por tarifa ---------------------------------------
    lines: List[Dict[str, Any]] = []
    total_base = Decimal("0")
    total_iva = Decimal("0")
    subtot_por_tarifa: Dict[str, Dict[str, Decimal]] = {}

    for idx, item in enumerate(req["items"], start=1):
        cantidad = Decimal(str(item["cantidad"]))
        precio = Decimal(str(item["precio_unitario"]))
        descuento = Decimal(str(item.get("descuento", 0) or 0))
        pct = Decimal(str(item.get("iva_porcentaje", 0) or 0))

        base = (cantidad * precio) - descuento
        iva_amount = (base * pct / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_EVEN
        )
        base_2 = base.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

        total_base += base_2
        total_iva += iva_amount

        pct_key = _money(pct)
        agg = subtot_por_tarifa.setdefault(pct_key, {"base": Decimal("0"), "iva": Decimal("0")})
        agg["base"] += base_2
        agg["iva"] += iva_amount

        lines.append({
            "ID": str(idx),
            "Quantity": _money(cantidad),
            "LineExtensionAmount": _money(base_2),
            "TaxAmount": _money(iva_amount),
            "TaxableAmount": _money(base_2),
            "TaxSubtotalAmount": _money(iva_amount),
            "TaxPercent": _money(pct),
            "TaxSchemeID": _IVA_SCHEME_ID,
            "TaxSchemeName": _IVA_SCHEME_NAME,
            "Description": item["descripcion"],
            "SellersItemID": item.get("codigo_producto") or str(idx).zfill(3),
            "AdditionalItemID": item.get("codigo_producto") or str(idx).zfill(3),
            "PriceAmount": _money(precio),
            "BaseQuantity": _money(cantidad),
        })

    tax_inclusive = total_base + total_iva

    tax_subtotals = [
        {
            "TaxAmount": _money(v["iva"]),
            "TaxableAmount": _money(v["base"]),
            "TaxPercent": pct_key,
            "TaxSchemeID": _IVA_SCHEME_ID,
            "TaxSchemeName": _IVA_SCHEME_NAME,
        }
        for pct_key, v in subtot_por_tarifa.items()
    ]

    amounts = {
        "LineExtensionAmount": _money(total_base),
        "TaxExclusiveAmount": _money(total_base),
        "TaxInclusiveAmount": _money(tax_inclusive),
        "PrepaidAmount": "0.00",
        "PayableAmount": _money(tax_inclusive),
        "TaxTotals": [{"TaxAmount": _money(total_iva), "TaxSubtotal": tax_subtotals}],
    }

    adq = req["adquirente"]
    control = {
        "StartDate": empresa.get("resolucion_fecha_desde") or "",
        "EndDate": empresa.get("resolucion_fecha_hasta") or "",
        "InvoiceAuthorization": str(empresa.get("resolucion_numero") or ""),
        "Pin": str(empresa.get("software_pin") or ""),
        "Prefix": prefijo,
        "From": str(empresa.get("rango_desde") or ""),
        "To": str(empresa.get("rango_hasta") or ""),
        "TestID": empresa.get("test_id") or "",
        "ProviderID": str(empresa.get("nit") or ""),
        "SoftwareID": str(empresa.get("software_id") or ""),
        "ProfileExecutionID": profile,
        "TechnicalKey": str(empresa.get("clave_tecnica") or ""),
    }

    company = {
        "AdditionalAccountID": "1",
        "PartyName": empresa.get("razon_social") or "",
        "CompanyID": str(empresa.get("nit") or ""),
        "DocumentType": empresa.get("tipo_documento") or "31",
        "VerificationDigit": str(empresa.get("digito_verificacion") or ""),
        "TaxLevelCode": empresa.get("tax_level_code") or "R-99-PN",
        "Address": {
            "AddressID": empresa.get("municipio_code") or "",
            "CountrySubentityCode": empresa.get("departamento_code") or "",
            "CityName": empresa.get("ciudad") or "",
            "CountrySubentity": empresa.get("departamento") or "",
            "AddressLine": empresa.get("direccion") or "",
        },
    }

    customer = {
        "ID": str(adq["nit"]),
        "DocumentType": adq.get("tipo_documento") or "31",
        "AdditionalAccountID": "1",
        "PartyName": adq["nombre"],
        "Telephone": adq.get("telefono") or "",
        "Email": adq.get("email") or "",
        "TaxLevelCode": adq.get("tax_level_code") or "R-99-PN",
        "Address": {
            "AddressID": adq.get("municipio_code") or "",
            "CountrySubentityCode": adq.get("departamento_code") or "",
            "CityName": adq.get("municipio") or "",
            "CountrySubentity": adq.get("departamento") or "",
            "AddressLine": adq.get("direccion") or "",
        },
    }

    invoice: Dict[str, Any] = {
        "Control": control,
        "ID": f"{prefijo}{consecutivo}",
        "IssueDate": issue_date,
        "IssueTime": issue_time,
        "Payment": {
            "PaymentID": str(req.get("forma_pago") or "1"),
            "PaymentCode": str(req.get("medio_pago") or "10"),
        },
        "Amounts": amounts,
        "Lines": lines,
        "Company": company,
        "Customer": customer,
    }
    if req.get("notas"):
        invoice["Note"] = req["notas"]

    return invoice
