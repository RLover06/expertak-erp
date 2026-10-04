"""In-memory storage (fallback when DATABASE_URL is not set)."""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


class MemoryStore:
    def __init__(self) -> None:
        self.documentos_dian: List[Dict[str, Any]] = []
        self.documentos_counter = 0
        self.consolidado_movimientos: List[Dict[str, Any]] = []
        self.empresas_map: Dict[Tuple[str, Optional[str]], Dict[str, Any]] = {}
        self.terceros_map: Dict[Tuple[str, Optional[str]], Dict[str, Any]] = {}
        self.empresa_id_counter = 0
        self.tercero_id_counter = 0
        self.resumen_rows: List[Dict[str, Any]] = []
        self.fe_emisiones: List[Dict[str, Any]] = []
        self.fe_emision_counter = 0
        self.fe_facturas: List[Dict[str, Any]] = []
        self.fe_factura_counter = 0
        self.fe_factura_items: List[Dict[str, Any]] = []
        self.fe_logs: List[Dict[str, Any]] = []
        self.fe_log_counter = 0
        self.fe_empresas_config: Dict[str, Dict[str, Any]] = {}

    @property
    def mode(self) -> str:
        return "memory"

    def counts(self) -> Dict[str, int]:
        return {
            "documentos": len(self.documentos_dian),
            "resumen": len(self.resumen_rows),
            "consolidado": len(self.consolidado_movimientos),
            "emisiones": len(self.fe_emisiones),
        }

    def get_or_create_empresa(self, nombre: str, nit: Optional[str]) -> int:
        key = (nombre.strip().upper(), nit.strip() if nit else None)
        if key in self.empresas_map:
            return self.empresas_map[key]["id"]
        self.empresa_id_counter += 1
        self.empresas_map[key] = {
            "id": self.empresa_id_counter,
            "nombre": nombre.strip(),
            "nit": nit,
        }
        return self.empresa_id_counter

    def get_or_create_tercero(self, nombre: str, nit: Optional[str]) -> int:
        key = (nombre.strip().upper(), nit.strip() if nit else None)
        if key in self.terceros_map:
            return self.terceros_map[key]["id"]
        self.tercero_id_counter += 1
        self.terceros_map[key] = {
            "id": self.tercero_id_counter,
            "nombre": nombre.strip(),
            "nit": nit,
        }
        return self.tercero_id_counter

    def import_documentos(
        self, rows: List[Dict[str, Any]], file_name: Optional[str]
    ) -> Tuple[int, int]:
        inserted = 0
        duplicates = 0
        cufes = {d.get("cufe_cude") for d in self.documentos_dian if d.get("cufe_cude")}

        for row in rows:
            row["archivo_origen"] = file_name
            cufe = row.get("cufe_cude")
            if cufe and cufe in cufes:
                duplicates += 1
                continue
            self.documentos_counter += 1
            row["_id"] = self.documentos_counter
            self.documentos_dian.append(row)
            if cufe:
                cufes.add(cufe)
            inserted += 1
        return inserted, duplicates

    def list_documentos(self) -> List[Dict[str, Any]]:
        return self.documentos_dian.copy()

    def replace_resumen(
        self, rows: List[Dict[str, Any]], file_name: Optional[str] = None
    ) -> None:
        self.resumen_rows = rows

    def get_resumen_rows(self) -> List[Dict[str, Any]]:
        return self.resumen_rows.copy()

    def import_consolidado_row(self, row: Dict[str, Any], file_name: Optional[str]) -> None:
        emp_id = self.get_or_create_empresa(row["empresa"], row.get("empresa_nit"))
        terc_id = self.get_or_create_tercero(row["tercero"], row.get("tercero_nit"))
        self.consolidado_movimientos.append({
            "empresa_id": emp_id,
            "tercero_id": terc_id,
            "fecha": row["fecha"],
            "cuenta": row["cuenta"],
            "debito": row.get("debito", Decimal("0.00")),
            "credito": row.get("credito", Decimal("0.00")),
            "documento_origen": row.get("documento_origen"),
            "periodo": row.get("periodo"),
            "archivo_origen": file_name,
            "_empresa_nombre": row["empresa"],
            "_tercero_nombre": row["tercero"],
        })

    def get_consolidado_movimientos(self) -> List[Dict[str, Any]]:
        return self.consolidado_movimientos.copy()

    def get_empresas_list(self) -> List[Dict[str, Any]]:
        return [
            {"id": e["id"], "nombre": e["nombre"], "nit": e["nit"]}
            for e in self.empresas_map.values()
        ]

    def get_terceros_list(self) -> List[Dict[str, Any]]:
        return [
            {"id": t["id"], "nombre": t["nombre"], "nit": t["nit"]}
            for t in self.terceros_map.values()
        ]

    def save_fe_emision(self, record: Dict[str, Any]) -> int:
        from datetime import datetime

        self.fe_emision_counter += 1
        row = {
            "id": self.fe_emision_counter,
            "modo": record["modo"],
            "factura_numero": record.get("factura_numero"),
            "estado": record["estado"],
            "engine": record.get("engine"),
            "dian_status_code": record.get("dian_status_code"),
            "dian_response": record.get("dian_response"),
            "invoice_payload": record.get("invoice_payload"),
            "cufe": record.get("cufe"),
            "created_at": datetime.utcnow().isoformat(),
        }
        self.fe_emisiones.append(row)
        return row["id"]

    def list_fe_emisiones(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.fe_emisiones[-limit:][::-1]

    # ----- Facturas FEV (§13) -------------------------------------------------

    def save_fe_factura(
        self, factura: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        from datetime import datetime

        self.fe_factura_counter += 1
        fid = self.fe_factura_counter
        row = {
            "id": fid,
            "empresa_nit": factura["empresa_nit"],
            "cufe": factura.get("cufe"),
            "prefijo": factura.get("prefijo"),
            "numero": factura.get("numero"),
            "factura_numero": factura.get("factura_numero"),
            "fecha_emision": factura.get("fecha_emision"),
            "hora_emision": factura.get("hora_emision"),
            "estado": factura.get("estado", "BORRADOR"),
            "adquirente_nit": factura.get("adquirente_nit"),
            "adquirente_nombre": factura.get("adquirente_nombre"),
            "subtotal": factura.get("subtotal"),
            "iva": factura.get("iva"),
            "total": factura.get("total"),
            "application_response": factura.get("application_response"),
            "ambiente": factura.get("ambiente", "habilitacion"),
            "intentos_transmision": factura.get("intentos_transmision", 0),
            "es_offline": factura.get("es_offline", False),
            "invoice_payload": factura.get("invoice_payload"),
            "factura_origen_id": factura.get("factura_origen_id"),
            "created_at": datetime.utcnow().isoformat(),
        }
        self.fe_facturas.append(row)
        for it in items or []:
            self.fe_factura_items.append({**it, "factura_id": fid})
        return fid

    def list_fe_facturas(self, limit: int = 50) -> List[Dict[str, Any]]:
        _omit = ("application_response", "invoice_payload")
        return [
            {k: v for k, v in f.items() if k not in _omit}
            for f in self.fe_facturas[-limit:][::-1]
        ]

    def get_fe_factura(self, factura_id: int) -> Optional[Dict[str, Any]]:
        row = next((f for f in self.fe_facturas if f["id"] == factura_id), None)
        if row is None:
            return None
        data = dict(row)
        data["items"] = [
            {k: v for k, v in it.items() if k != "factura_id"}
            for it in self.fe_factura_items
            if it.get("factura_id") == factura_id
        ]
        data["logs"] = [
            {k: v for k, v in lg.items() if k not in ("xml_enviado", "xml_respuesta")}
            for lg in self.fe_logs
            if lg.get("factura_id") == factura_id
        ][::-1]
        return data

    def update_fe_factura_estado(
        self, factura_id: int, nuevo_estado: str, validar: bool = True, **campos: Any
    ) -> Optional[Dict[str, Any]]:
        from .fe_estados import validar_transicion

        row = next((f for f in self.fe_facturas if f["id"] == factura_id), None)
        if row is None:
            return None
        if validar:
            validar_transicion(row["estado"], nuevo_estado)
        row["estado"] = nuevo_estado
        for key, value in campos.items():
            if value is not None:
                row[key] = value
        return {k: v for k, v in row.items() if k not in ("application_response", "invoice_payload")}

    def clonar_factura_borrador(self, factura_id: int) -> Optional[Dict[str, Any]]:
        from datetime import datetime

        from .fe_estados import BORRADOR, RECHAZADA

        orig = next((f for f in self.fe_facturas if f["id"] == factura_id), None)
        if orig is None:
            return None
        if orig["estado"] != RECHAZADA:
            raise ValueError(
                f"Solo se puede corregir una factura en estado RECHAZADA (actual: {orig['estado']})."
            )
        self.fe_factura_counter += 1
        nid = self.fe_factura_counter
        nueva = {
            **orig,
            "id": nid,
            "cufe": None,
            "numero": None,
            "factura_numero": None,
            "estado": BORRADOR,
            "application_response": None,
            "intentos_transmision": 0,
            "factura_origen_id": orig["id"],
            "created_at": datetime.utcnow().isoformat(),
        }
        self.fe_facturas.append(nueva)
        items_orig = [it for it in self.fe_factura_items if it.get("factura_id") == factura_id]
        for it in items_orig:
            self.fe_factura_items.append({**it, "factura_id": nid})
        return {k: v for k, v in nueva.items() if k not in ("application_response", "invoice_payload")}

    def save_fe_log(self, log: Dict[str, Any]) -> int:
        from datetime import datetime

        self.fe_log_counter += 1
        row = {
            "id": self.fe_log_counter,
            "factura_id": log.get("factura_id"),
            "fecha_intento": datetime.utcnow().isoformat(),
            "servicio_ws": log.get("servicio_ws"),
            "exitoso": log.get("exitoso"),
            "codigo_respuesta": log.get("codigo_respuesta"),
            "mensaje_dian": log.get("mensaje_dian"),
            "xml_enviado": log.get("xml_enviado"),
            "xml_respuesta": log.get("xml_respuesta"),
        }
        self.fe_logs.append(row)
        return row["id"]

    # ----- Configuración por empresa emisora (§13) ----------------------------

    def upsert_empresa_config(self, cfg: Dict[str, Any]) -> str:
        nit = cfg["nit"]
        existing = self.fe_empresas_config.get(nit, {"nit": nit})
        existing.update({k: v for k, v in cfg.items() if v is not None})
        self.fe_empresas_config[nit] = existing
        return nit

    def get_empresa_config(
        self, nit: str, include_secrets: bool = False
    ) -> Optional[Dict[str, Any]]:
        cfg = self.fe_empresas_config.get(nit)
        if cfg is None:
            return None
        if include_secrets:
            return dict(cfg)
        return {k: v for k, v in cfg.items() if k not in ("clave_tecnica", "software_pin")}

    def list_empresa_configs(self, include_secrets: bool = False) -> List[Dict[str, Any]]:
        return [
            self.get_empresa_config(nit, include_secrets)
            for nit in sorted(
                self.fe_empresas_config,
                key=lambda n: (self.fe_empresas_config[n].get("razon_social") or ""),
            )
        ]

    def reserve_consecutivo(self, nit: str) -> Optional[int]:
        cfg = self.fe_empresas_config.get(nit)
        if cfg is None:
            return None
        base = cfg.get("numero_actual")
        if base is None:
            rango_desde = cfg.get("rango_desde")
            base = (rango_desde - 1) if rango_desde else 0
        siguiente = base + 1
        rango_hasta = cfg.get("rango_hasta")
        if rango_hasta is not None and siguiente > rango_hasta:
            raise ValueError(
                f"Consecutivo {siguiente} excede el rango autorizado ({rango_hasta})."
            )
        cfg["numero_actual"] = siguiente
        return siguiente
