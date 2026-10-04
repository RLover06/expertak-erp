"""
Cálculo del CUFE — Código Único de Factura Electrónica (§11.2 Suplemento B, Anexo v1.9).

El CUFE es determinista: depende solo de campos del payload de la factura. Se calcula
exactamente igual que el motor de referencia (mismo orden de campos, mismo SHA-384), de
modo que Expertak puede capturar el CUFE *real* sin depender de la respuesta de la DIAN.

Fórmula (§11.2):
    SHA-384( NumFac + FecFac + HorFac + ValFac
             + CodImp1 + ValImp1 + CodImp2 + ValImp2 + CodImp3 + ValImp3
             + ValTot + NitOFE + NumAdq + ClTec + TipoAmbiente )

Códigos de impuesto fijos (igual que el motor): 01=IVA, 04=INC, 03=ICA.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Optional

# CUFE/CUDE = SHA-384 → 96 caracteres hexadecimales.
_CUFE_PATTERN = re.compile(r"\b[0-9a-fA-F]{96}\b")


def _get(payload: Dict[str, Any], *path: str) -> Optional[Any]:
    node: Any = payload
    for key in path:
        if isinstance(node, dict):
            node = node.get(key)
        else:
            return None
    return node


def compute_cufe(invoice: Dict[str, Any]) -> Optional[str]:
    """
    Calcula el CUFE desde el payload tipo InvoiceDto. Devuelve ``None`` si falta algún
    campo obligatorio (no se inventan valores que cambiarían el hash).
    """
    num_fac = _get(invoice, "ID")
    fec_fac = _get(invoice, "IssueDate")
    hor_fac = _get(invoice, "IssueTime")
    val_fac = _get(invoice, "Amounts", "LineExtensionAmount")
    val_tot = _get(invoice, "Amounts", "TaxInclusiveAmount")
    nit_ofe = _get(invoice, "Company", "CompanyID")
    num_adq = _get(invoice, "Customer", "ID")
    cl_tec = _get(invoice, "Control", "TechnicalKey")
    tipo_ambiente = _get(invoice, "Control", "ProfileExecutionID")

    tax_totals = _get(invoice, "Amounts", "TaxTotals")
    val_imp1 = None
    if isinstance(tax_totals, list) and tax_totals:
        val_imp1 = tax_totals[0].get("TaxAmount") if isinstance(tax_totals[0], dict) else None

    campos = [num_fac, fec_fac, hor_fac, val_fac, val_imp1, val_tot, nit_ofe, num_adq, cl_tec, tipo_ambiente]
    if any(c is None for c in campos):
        return None

    cufe_string = (
        f"{num_fac}{fec_fac}{hor_fac}{val_fac}"
        f"01{val_imp1}04{'0.00'}03{'0.00'}"
        f"{val_tot}{nit_ofe}{num_adq}{cl_tec}{tipo_ambiente}"
    )
    return hashlib.sha384(cufe_string.encode("utf-8")).hexdigest()


def extract_cufe_from_response(text: Optional[str]) -> Optional[str]:
    """Busca un CUFE/CUDE (96 hex) en la respuesta de la DIAN, como respaldo."""
    if not text:
        return None
    match = _CUFE_PATTERN.search(text)
    return match.group(0).lower() if match else None
