"""Persistent storage via Supabase (PostgreSQL + SQLAlchemy)."""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_engine
from .models import (
    ConsolidadoMovimiento,
    DocumentoDian,
    Empresa,
    FeEmision,
    FeEmpresaConfig,
    FeFactura,
    FeFacturaItem,
    FeLogTransmision,
    ResumenFila,
    Tercero,
)


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class SupabaseStore:
    @property
    def mode(self) -> str:
        return "supabase"

    def _session(self) -> Session:
        from .database import SessionLocal

        if SessionLocal is None:
            get_engine()
        return SessionLocal()

    def counts(self) -> Dict[str, int]:
        with self._session() as db:
            return {
                "documentos": db.query(DocumentoDian).count(),
                "resumen": db.query(ResumenFila).count(),
                "consolidado": db.query(ConsolidadoMovimiento).count(),
                "emisiones": db.query(FeEmision).count(),
            }

    def _get_or_create_empresa(self, db: Session, nombre: str, nit: Optional[str]) -> Empresa:
        n = nombre.strip()
        nit_val = nit.strip() if nit else None
        emp = (
            db.execute(
                select(Empresa).where(Empresa.nombre == n, Empresa.nit == nit_val)
            )
            .scalar_one_or_none()
        )
        if emp:
            return emp
        emp = Empresa(nombre=n, nit=nit_val)
        db.add(emp)
        db.flush()
        return emp

    def _get_or_create_tercero(self, db: Session, nombre: str, nit: Optional[str]) -> Tercero:
        n = nombre.strip()
        nit_val = nit.strip() if nit else None
        ter = (
            db.execute(
                select(Tercero).where(Tercero.nombre == n, Tercero.nit == nit_val)
            )
            .scalar_one_or_none()
        )
        if ter:
            return ter
        ter = Tercero(nombre=n, nit=nit_val)
        db.add(ter)
        db.flush()
        return ter

    def import_documentos(
        self, rows: List[Dict[str, Any]], file_name: Optional[str]
    ) -> Tuple[int, int]:
        inserted = 0
        duplicates = 0
        with self._session() as db:
            existing = {
                r[0]
                for r in db.execute(select(DocumentoDian.cufe_cude)).all()
                if r[0]
            }
            for row in rows:
                cufe = row.get("cufe_cude")
                if cufe and cufe in existing:
                    duplicates += 1
                    continue
                doc = DocumentoDian(
                    tipo_documento=row["tipo_documento"],
                    cufe_cude=cufe,
                    folio=row.get("folio"),
                    prefijo=row.get("prefijo"),
                    divisa=row.get("divisa"),
                    forma_pago=row.get("forma_pago"),
                    medio_pago=row.get("medio_pago"),
                    fecha_emision=row.get("fecha_emision"),
                    fecha_recepcion=row.get("fecha_recepcion"),
                    nit_emisor=row.get("nit_emisor"),
                    nombre_emisor=row.get("nombre_emisor"),
                    nit_receptor=row.get("nit_receptor"),
                    nombre_receptor=row.get("nombre_receptor"),
                    iva=_to_decimal(row.get("iva")),
                    ica=_to_decimal(row.get("ica")),
                    ic=_to_decimal(row.get("ic")),
                    inc=_to_decimal(row.get("inc")),
                    timbre=_to_decimal(row.get("timbre")),
                    inc_bolsas=_to_decimal(row.get("inc_bolsas")),
                    in_carbono=_to_decimal(row.get("in_carbono")),
                    in_combustibles=_to_decimal(row.get("in_combustibles")),
                    ic_datos=_to_decimal(row.get("ic_datos")),
                    icl=_to_decimal(row.get("icl")),
                    inpp=_to_decimal(row.get("inpp")),
                    ibua=_to_decimal(row.get("ibua")),
                    icui=_to_decimal(row.get("icui")),
                    rete_iva=_to_decimal(row.get("rete_iva")),
                    rete_renta=_to_decimal(row.get("rete_renta")),
                    rete_ica=_to_decimal(row.get("rete_ica")),
                    total=_to_decimal(row.get("total")),
                    estado=row.get("estado"),
                    grupo=row.get("grupo"),
                    empresa=row.get("empresa"),
                    archivo_origen=file_name,
                )
                db.add(doc)
                if cufe:
                    existing.add(cufe)
                inserted += 1
            db.commit()
        return inserted, duplicates

    def list_documentos(self) -> List[Dict[str, Any]]:
        with self._session() as db:
            docs = db.execute(select(DocumentoDian).order_by(DocumentoDian.id.desc())).scalars().all()
            result = []
            for d in docs:
                item = d.to_dict()
                item["_id"] = d.id
                result.append(item)
            return result

    def replace_resumen(self, rows: List[Dict[str, Any]], file_name: Optional[str] = None) -> None:
        with self._session() as db:
            db.query(ResumenFila).delete()
            for row in rows:
                db.add(
                    ResumenFila(
                        empresa=row["empresa"],
                        tipo_documento=row["tipo_documento"],
                        grupo=row.get("grupo"),
                        subtotal=_to_decimal(row.get("subtotal")),
                        iva=_to_decimal(row.get("iva")),
                        total_otros=_to_decimal(row.get("total_otros")),
                        total_renta=_to_decimal(row.get("total_renta")),
                        total=_to_decimal(row.get("total")),
                        archivo_origen=file_name,
                    )
                )
            db.commit()

    def get_resumen_rows(self) -> List[Dict[str, Any]]:
        with self._session() as db:
            filas = db.execute(select(ResumenFila)).scalars().all()
            return [
                {
                    "empresa": f.empresa,
                    "tipo_documento": f.tipo_documento,
                    "grupo": f.grupo,
                    "subtotal": f.subtotal,
                    "iva": f.iva,
                    "total_otros": f.total_otros,
                    "total_renta": f.total_renta,
                    "total": f.total,
                }
                for f in filas
            ]

    def import_consolidado_row(self, row: Dict[str, Any], file_name: Optional[str]) -> None:
        with self._session() as db:
            emp = self._get_or_create_empresa(db, row["empresa"], row.get("empresa_nit"))
            ter = self._get_or_create_tercero(db, row["tercero"], row.get("tercero_nit"))
            db.add(
                ConsolidadoMovimiento(
                    empresa_id=emp.id,
                    tercero_id=ter.id,
                    fecha=row["fecha"],
                    cuenta=row["cuenta"],
                    debito=_to_decimal(row.get("debito")),
                    credito=_to_decimal(row.get("credito")),
                    documento_origen=row.get("documento_origen"),
                    periodo=row.get("periodo"),
                    archivo_origen=file_name,
                )
            )
            db.commit()

    def get_consolidado_movimientos(self) -> List[Dict[str, Any]]:
        with self._session() as db:
            rows = (
                db.execute(
                    select(
                        ConsolidadoMovimiento,
                        Empresa.nombre.label("empresa_nombre"),
                        Tercero.nombre.label("tercero_nombre"),
                    )
                    .join(Empresa, ConsolidadoMovimiento.empresa_id == Empresa.id)
                    .join(Tercero, ConsolidadoMovimiento.tercero_id == Tercero.id)
                )
                .all()
            )
            out = []
            for mov, emp_nombre, ter_nombre in rows:
                out.append({
                    "empresa_id": mov.empresa_id,
                    "tercero_id": mov.tercero_id,
                    "fecha": mov.fecha,
                    "cuenta": mov.cuenta,
                    "debito": mov.debito,
                    "credito": mov.credito,
                    "documento_origen": mov.documento_origen,
                    "periodo": mov.periodo,
                    "archivo_origen": mov.archivo_origen,
                    "_empresa_nombre": emp_nombre,
                    "_tercero_nombre": ter_nombre,
                })
            return out

    def get_empresas_list(self) -> List[Dict[str, Any]]:
        with self._session() as db:
            return [
                {"id": e.id, "nombre": e.nombre, "nit": e.nit}
                for e in db.execute(select(Empresa)).scalars().all()
            ]

    def get_terceros_list(self) -> List[Dict[str, Any]]:
        with self._session() as db:
            return [
                {"id": t.id, "nombre": t.nombre, "nit": t.nit}
                for t in db.execute(select(Tercero)).scalars().all()
            ]

    def get_or_create_empresa(self, nombre: str, nit: Optional[str]) -> int:
        with self._session() as db:
            emp = self._get_or_create_empresa(db, nombre, nit)
            db.commit()
            return emp.id

    def get_or_create_tercero(self, nombre: str, nit: Optional[str]) -> int:
        with self._session() as db:
            ter = self._get_or_create_tercero(db, nombre, nit)
            db.commit()
            return ter.id

    def save_fe_emision(self, record: Dict[str, Any]) -> int:
        with self._session() as db:
            emision = FeEmision(
                modo=record["modo"],
                factura_numero=record.get("factura_numero"),
                estado=record["estado"],
                engine=record.get("engine"),
                dian_status_code=record.get("dian_status_code"),
                dian_response=record.get("dian_response"),
                invoice_payload=record.get("invoice_payload"),
                cufe=record.get("cufe"),
            )
            db.add(emision)
            db.commit()
            db.refresh(emision)
            return int(emision.id)

    def list_fe_emisiones(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._session() as db:
            rows = (
                db.execute(
                    select(FeEmision).order_by(FeEmision.id.desc()).limit(limit)
                )
                .scalars()
                .all()
            )
            return [
                {
                    "id": row.id,
                    "modo": row.modo,
                    "factura_numero": row.factura_numero,
                    "estado": row.estado,
                    "engine": row.engine,
                    "dian_status_code": row.dian_status_code,
                    "cufe": row.cufe,
                    "created_at": row.created_at.isoformat() if row.created_at else "",
                    "dian_response": row.dian_response,
                }
                for row in rows
            ]

    # ----- Facturas FEV (§13) -------------------------------------------------

    def save_fe_factura(
        self, factura: Dict[str, Any], items: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        with self._session() as db:
            row = FeFactura(
                empresa_nit=factura["empresa_nit"],
                cufe=factura.get("cufe"),
                prefijo=factura.get("prefijo"),
                numero=factura.get("numero"),
                factura_numero=factura.get("factura_numero"),
                fecha_emision=factura.get("fecha_emision"),
                hora_emision=factura.get("hora_emision"),
                estado=factura.get("estado", "BORRADOR"),
                adquirente_nit=factura.get("adquirente_nit"),
                adquirente_nombre=factura.get("adquirente_nombre"),
                subtotal=_to_decimal(factura.get("subtotal")),
                iva=_to_decimal(factura.get("iva")),
                total=_to_decimal(factura.get("total")),
                xml_generado=factura.get("xml_generado"),
                xml_firmado=factura.get("xml_firmado"),
                application_response=factura.get("application_response"),
                ambiente=factura.get("ambiente", "habilitacion"),
                intentos_transmision=factura.get("intentos_transmision", 0),
                fecha_transmision=factura.get("fecha_transmision"),
                es_offline=factura.get("es_offline", False),
                fecha_limite_transmision=factura.get("fecha_limite_transmision"),
                invoice_payload=factura.get("invoice_payload"),
                factura_origen_id=factura.get("factura_origen_id"),
            )
            db.add(row)
            db.flush()
            for it in items or []:
                db.add(
                    FeFacturaItem(
                        factura_id=row.id,
                        descripcion=it["descripcion"],
                        cantidad=_to_decimal(it.get("cantidad")),
                        precio_unitario=_to_decimal(it.get("precio_unitario")),
                        descuento=_to_decimal(it.get("descuento")),
                        iva_porcentaje=_to_decimal(it.get("iva_porcentaje")),
                        subtotal=_to_decimal(it.get("subtotal")),
                        codigo_producto=it.get("codigo_producto"),
                        unidad_medida=it.get("unidad_medida", "EA"),
                    )
                )
            db.commit()
            return int(row.id)

    def _factura_to_dict(self, row: FeFactura) -> Dict[str, Any]:
        return {
            "id": row.id,
            "empresa_nit": row.empresa_nit,
            "cufe": row.cufe,
            "prefijo": row.prefijo,
            "numero": row.numero,
            "factura_numero": row.factura_numero,
            "fecha_emision": row.fecha_emision.isoformat() if row.fecha_emision else None,
            "hora_emision": row.hora_emision,
            "estado": row.estado,
            "adquirente_nit": row.adquirente_nit,
            "adquirente_nombre": row.adquirente_nombre,
            "subtotal": str(row.subtotal) if row.subtotal is not None else None,
            "iva": str(row.iva) if row.iva is not None else None,
            "total": str(row.total) if row.total is not None else None,
            "ambiente": row.ambiente,
            "intentos_transmision": row.intentos_transmision,
            "es_offline": row.es_offline,
            "factura_origen_id": row.factura_origen_id,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }

    def list_fe_facturas(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._session() as db:
            rows = (
                db.execute(select(FeFactura).order_by(FeFactura.id.desc()).limit(limit))
                .scalars()
                .all()
            )
            return [self._factura_to_dict(r) for r in rows]

    def get_fe_factura(self, factura_id: int) -> Optional[Dict[str, Any]]:
        with self._session() as db:
            row = db.get(FeFactura, factura_id)
            if row is None:
                return None
            data = self._factura_to_dict(row)
            data["application_response"] = row.application_response
            data["invoice_payload"] = row.invoice_payload
            items = (
                db.execute(
                    select(FeFacturaItem).where(FeFacturaItem.factura_id == factura_id)
                )
                .scalars()
                .all()
            )
            data["items"] = [
                {
                    "id": it.id,
                    "descripcion": it.descripcion,
                    "cantidad": str(it.cantidad) if it.cantidad is not None else None,
                    "precio_unitario": str(it.precio_unitario) if it.precio_unitario is not None else None,
                    "descuento": str(it.descuento) if it.descuento is not None else None,
                    "iva_porcentaje": str(it.iva_porcentaje) if it.iva_porcentaje is not None else None,
                    "subtotal": str(it.subtotal) if it.subtotal is not None else None,
                    "codigo_producto": it.codigo_producto,
                    "unidad_medida": it.unidad_medida,
                }
                for it in items
            ]
            logs = (
                db.execute(
                    select(FeLogTransmision)
                    .where(FeLogTransmision.factura_id == factura_id)
                    .order_by(FeLogTransmision.id.desc())
                )
                .scalars()
                .all()
            )
            data["logs"] = [
                {
                    "id": lg.id,
                    "fecha_intento": lg.fecha_intento.isoformat() if lg.fecha_intento else "",
                    "servicio_ws": lg.servicio_ws,
                    "exitoso": lg.exitoso,
                    "codigo_respuesta": lg.codigo_respuesta,
                    "mensaje_dian": lg.mensaje_dian,
                }
                for lg in logs
            ]
            return data

    _ESTADO_CAMPOS_DECIMAL = ("subtotal", "iva", "total")

    def update_fe_factura_estado(
        self, factura_id: int, nuevo_estado: str, validar: bool = True, **campos: Any
    ) -> Optional[Dict[str, Any]]:
        """Cambia el estado validando la transición (fe_estados) y actualiza campos opcionales."""
        from .fe_estados import validar_transicion

        with self._session() as db:
            row = db.get(FeFactura, factura_id)
            if row is None:
                return None
            if validar:
                validar_transicion(row.estado, nuevo_estado)
            row.estado = nuevo_estado
            for key, value in campos.items():
                if value is None or not hasattr(row, key):
                    continue
                if key in self._ESTADO_CAMPOS_DECIMAL:
                    value = _to_decimal(value)
                setattr(row, key, value)
            db.commit()
            db.refresh(row)
            return self._factura_to_dict(row)

    def clonar_factura_borrador(self, factura_id: int) -> Optional[Dict[str, Any]]:
        """Crea un BORRADOR nuevo a partir de una factura RECHAZADA (corrección).

        La original NO cambia de estado: queda RECHAZADA permanentemente. La nueva
        apunta a ella vía factura_origen_id.
        """
        from .fe_estados import BORRADOR, RECHAZADA

        with self._session() as db:
            orig = db.get(FeFactura, factura_id)
            if orig is None:
                return None
            if orig.estado != RECHAZADA:
                raise ValueError(
                    f"Solo se puede corregir una factura en estado RECHAZADA (actual: {orig.estado})."
                )
            nueva = FeFactura(
                empresa_nit=orig.empresa_nit,
                cufe=None,
                prefijo=orig.prefijo,
                numero=None,
                factura_numero=None,
                estado=BORRADOR,
                adquirente_nit=orig.adquirente_nit,
                adquirente_nombre=orig.adquirente_nombre,
                subtotal=orig.subtotal,
                iva=orig.iva,
                total=orig.total,
                ambiente=orig.ambiente,
                intentos_transmision=0,
                invoice_payload=orig.invoice_payload,
                factura_origen_id=orig.id,
            )
            db.add(nueva)
            db.flush()
            items = (
                db.execute(
                    select(FeFacturaItem).where(FeFacturaItem.factura_id == orig.id)
                )
                .scalars()
                .all()
            )
            for it in items:
                db.add(
                    FeFacturaItem(
                        factura_id=nueva.id,
                        descripcion=it.descripcion,
                        cantidad=it.cantidad,
                        precio_unitario=it.precio_unitario,
                        descuento=it.descuento,
                        iva_porcentaje=it.iva_porcentaje,
                        subtotal=it.subtotal,
                        codigo_producto=it.codigo_producto,
                        unidad_medida=it.unidad_medida,
                    )
                )
            db.commit()
            return self._factura_to_dict(nueva)

    def save_fe_log(self, log: Dict[str, Any]) -> int:
        with self._session() as db:
            row = FeLogTransmision(
                factura_id=log.get("factura_id"),
                servicio_ws=log.get("servicio_ws"),
                exitoso=log.get("exitoso"),
                codigo_respuesta=log.get("codigo_respuesta"),
                mensaje_dian=log.get("mensaje_dian"),
                xml_enviado=log.get("xml_enviado"),
                xml_respuesta=log.get("xml_respuesta"),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return int(row.id)

    # ----- Configuración por empresa emisora (§13) ----------------------------

    _EMPRESA_CONFIG_FIELDS = (
        "razon_social", "prefijo", "rango_desde", "rango_hasta", "numero_actual",
        "resolucion_numero", "resolucion_fecha", "resolucion_fecha_desde",
        "resolucion_fecha_hasta", "clave_tecnica", "software_id", "software_pin",
        "test_id", "cert_firma_path", "ambiente", "digito_verificacion", "tipo_documento",
        "tax_level_code", "direccion", "departamento_code", "departamento",
        "municipio_code", "ciudad",
    )
    # Nunca exponer estos campos en respuestas de API.
    _EMPRESA_CONFIG_SECRETS = ("clave_tecnica", "software_pin")

    def upsert_empresa_config(self, cfg: Dict[str, Any]) -> str:
        with self._session() as db:
            row = db.get(FeEmpresaConfig, cfg["nit"])
            if row is None:
                row = FeEmpresaConfig(nit=cfg["nit"], razon_social=cfg.get("razon_social", ""))
                db.add(row)
            for field_name in self._EMPRESA_CONFIG_FIELDS:
                if field_name in cfg and cfg[field_name] is not None:
                    setattr(row, field_name, cfg[field_name])
            db.commit()
            return row.nit

    def _empresa_config_to_dict(
        self, row: FeEmpresaConfig, include_secrets: bool
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"nit": row.nit}
        for field_name in self._EMPRESA_CONFIG_FIELDS:
            if not include_secrets and field_name in self._EMPRESA_CONFIG_SECRETS:
                continue
            value = getattr(row, field_name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[field_name] = value
        return data

    def get_empresa_config(
        self, nit: str, include_secrets: bool = False
    ) -> Optional[Dict[str, Any]]:
        with self._session() as db:
            row = db.get(FeEmpresaConfig, nit)
            if row is None:
                return None
            return self._empresa_config_to_dict(row, include_secrets)

    def list_empresa_configs(self, include_secrets: bool = False) -> List[Dict[str, Any]]:
        with self._session() as db:
            rows = (
                db.execute(select(FeEmpresaConfig).order_by(FeEmpresaConfig.razon_social))
                .scalars()
                .all()
            )
            return [self._empresa_config_to_dict(r, include_secrets) for r in rows]

    def reserve_consecutivo(self, nit: str) -> Optional[int]:
        """Reserva el siguiente consecutivo de forma atómica (SELECT ... FOR UPDATE)."""
        with self._session() as db:
            row = (
                db.execute(
                    select(FeEmpresaConfig).where(FeEmpresaConfig.nit == nit).with_for_update()
                )
                .scalar_one_or_none()
            )
            if row is None:
                return None
            base = row.numero_actual if row.numero_actual is not None else (
                (row.rango_desde - 1) if row.rango_desde else 0
            )
            siguiente = base + 1
            if row.rango_hasta is not None and siguiente > row.rango_hasta:
                db.rollback()
                raise ValueError(
                    f"Consecutivo {siguiente} excede el rango autorizado ({row.rango_hasta})."
                )
            row.numero_actual = siguiente
            db.commit()
            return siguiente
