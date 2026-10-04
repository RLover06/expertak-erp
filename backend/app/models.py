from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)

from .database import Base


class DocumentoDian(Base):
    __tablename__ = "documentos_dian"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tipo_documento = Column(String(100), nullable=False)
    cufe_cude = Column(String(255), nullable=False, unique=True)
    folio = Column(String(50))
    prefijo = Column(String(20))
    divisa = Column(String(10))
    forma_pago = Column(String(50))
    medio_pago = Column(String(50))
    fecha_emision = Column(Date)
    fecha_recepcion = Column(DateTime)
    nit_emisor = Column(BigInteger)
    nombre_emisor = Column(String(255))
    nit_receptor = Column(BigInteger)
    nombre_receptor = Column(String(255))
    iva = Column(DECIMAL(18, 2), default=0)
    ica = Column(DECIMAL(18, 2), default=0)
    ic = Column(DECIMAL(18, 2), default=0)
    inc = Column(DECIMAL(18, 2), default=0)
    timbre = Column(DECIMAL(18, 2), default=0)
    inc_bolsas = Column(DECIMAL(18, 2), default=0)
    in_carbono = Column(DECIMAL(18, 2), default=0)
    in_combustibles = Column(DECIMAL(18, 2), default=0)
    ic_datos = Column(DECIMAL(18, 2), default=0)
    icl = Column(DECIMAL(18, 2), default=0)
    inpp = Column(DECIMAL(18, 2), default=0)
    ibua = Column(DECIMAL(18, 2), default=0)
    icui = Column(DECIMAL(18, 2), default=0)
    rete_iva = Column(DECIMAL(18, 2), default=0)
    rete_renta = Column(DECIMAL(18, 2), default=0)
    rete_ica = Column(DECIMAL(18, 2), default=0)
    total = Column(DECIMAL(18, 2), nullable=False)
    estado = Column(String(50))
    grupo = Column(String(50))
    empresa = Column(String(255))
    archivo_origen = Column(String(255))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo_documento": self.tipo_documento,
            "cufe_cude": self.cufe_cude,
            "folio": self.folio,
            "prefijo": self.prefijo,
            "divisa": self.divisa,
            "forma_pago": self.forma_pago,
            "medio_pago": self.medio_pago,
            "fecha_emision": self.fecha_emision.isoformat() if self.fecha_emision else None,
            "fecha_recepcion": self.fecha_recepcion.isoformat() if self.fecha_recepcion else None,
            "nit_emisor": self.nit_emisor,
            "nombre_emisor": self.nombre_emisor,
            "nit_receptor": self.nit_receptor,
            "nombre_receptor": self.nombre_receptor,
            "iva": str(self.iva) if self.iva is not None else None,
            "ica": str(self.ica) if self.ica is not None else None,
            "ic": str(self.ic) if self.ic is not None else None,
            "inc": str(self.inc) if self.inc is not None else None,
            "timbre": str(self.timbre) if self.timbre is not None else None,
            "inc_bolsas": str(self.inc_bolsas) if self.inc_bolsas is not None else None,
            "in_carbono": str(self.in_carbono) if self.in_carbono is not None else None,
            "in_combustibles": str(self.in_combustibles) if self.in_combustibles is not None else None,
            "ic_datos": str(self.ic_datos) if self.ic_datos is not None else None,
            "icl": str(self.icl) if self.icl is not None else None,
            "inpp": str(self.inpp) if self.inpp is not None else None,
            "ibua": str(self.ibua) if self.ibua is not None else None,
            "icui": str(self.icui) if self.icui is not None else None,
            "rete_iva": str(self.rete_iva) if self.rete_iva is not None else None,
            "rete_renta": str(self.rete_renta) if self.rete_renta is not None else None,
            "rete_ica": str(self.rete_ica) if self.rete_ica is not None else None,
            "total": str(self.total) if self.total is not None else None,
            "estado": self.estado,
            "grupo": self.grupo,
            "empresa": self.empresa,
        }


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    nit = Column(String(50))

    __table_args__ = (UniqueConstraint("nombre", "nit", name="uk_empresa_nombre_nit"),)


class Tercero(Base):
    __tablename__ = "terceros"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    nit = Column(String(50))

    __table_args__ = (UniqueConstraint("nombre", "nit", name="uk_tercero_nombre_nit"),)


class ConsolidadoMovimiento(Base):
    __tablename__ = "consolidado_movimientos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_id = Column(BigInteger, ForeignKey("empresas.id"), nullable=False)
    tercero_id = Column(BigInteger, ForeignKey("terceros.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    cuenta = Column(String(100), nullable=False)
    debito = Column(DECIMAL(18, 2), default=0)
    credito = Column(DECIMAL(18, 2), default=0)
    documento_origen = Column(String(255))
    periodo = Column(String(50))
    archivo_origen = Column(String(255))
    fecha_importacion = Column(DateTime, server_default=func.now())


class FeEmision(Base):
    """Log de intentos de emisión de factura electrónica ante la DIAN."""

    __tablename__ = "fe_emisiones"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    modo = Column(String(20), nullable=False)
    factura_numero = Column(String(50))
    estado = Column(String(30), nullable=False, default="pendiente")
    engine = Column(String(20))
    dian_status_code = Column(Integer)
    dian_response = Column(String)
    invoice_payload = Column(JSON)
    cufe = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ResumenFila(Base):
    """Resumen pre-agregado (INFORME RELACION_FE)."""

    __tablename__ = "resumen_filas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa = Column(String(255), nullable=False)
    tipo_documento = Column(String(100), nullable=False)
    grupo = Column(String(50))
    subtotal = Column(DECIMAL(18, 2), default=0)
    iva = Column(DECIMAL(18, 2), default=0)
    total_otros = Column(DECIMAL(18, 2), default=0)
    total_renta = Column(DECIMAL(18, 2), default=0)
    total = Column(DECIMAL(18, 2), default=0)
    archivo_origen = Column(String(255))
    fecha_importacion = Column(DateTime, server_default=func.now())


class FeFactura(Base):
    """Factura electrónica de venta (§13 Anexo v1.9). Persiste borradores y emisiones."""

    __tablename__ = "fe_facturas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    empresa_nit = Column(String(20), nullable=False)
    cufe = Column(String(255), unique=True)
    prefijo = Column(String(20))
    numero = Column(Integer)
    factura_numero = Column(String(50))
    fecha_emision = Column(Date)
    hora_emision = Column(String(20))  # "hh:mm:ss-05:00" — se preserva el huso (UTC-05).
    estado = Column(String(30), nullable=False, default="BORRADOR")
    adquirente_nit = Column(String(20))
    adquirente_nombre = Column(String(255))
    subtotal = Column(Numeric(18, 2), default=0)
    iva = Column(Numeric(18, 2), default=0)
    total = Column(Numeric(18, 2), default=0)
    xml_generado = Column(Text)
    xml_firmado = Column(Text)
    application_response = Column(Text)
    ambiente = Column(String(20), nullable=False, default="habilitacion")
    intentos_transmision = Column(Integer, default=0)
    fecha_transmision = Column(DateTime(timezone=True))
    es_offline = Column(Boolean, default=False)
    fecha_limite_transmision = Column(DateTime(timezone=True))
    invoice_payload = Column(JSON)  # InvoiceDto del borrador (consecutivo tentativo) para re-emisión.
    factura_origen_id = Column(BigInteger, ForeignKey("fe_facturas.id"))  # factura RECHAZADA que esta corrige.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class FeFacturaItem(Base):
    """Líneas/ítems de una factura electrónica (§13)."""

    __tablename__ = "fe_factura_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    factura_id = Column(BigInteger, ForeignKey("fe_facturas.id"), nullable=False)
    descripcion = Column(Text, nullable=False)
    cantidad = Column(Numeric(15, 6), nullable=False)
    precio_unitario = Column(Numeric(18, 6), nullable=False)
    descuento = Column(Numeric(18, 2), default=0)
    iva_porcentaje = Column(Numeric(5, 2), default=19)
    subtotal = Column(Numeric(18, 2), nullable=False)
    codigo_producto = Column(String(100))
    unidad_medida = Column(String(20), default="EA")


class FeLogTransmision(Base):
    """Log completo de cada intento de transmisión a la DIAN (§13). XML sin truncar."""

    __tablename__ = "fe_log_transmision"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    factura_id = Column(BigInteger, ForeignKey("fe_facturas.id"))
    fecha_intento = Column(DateTime(timezone=True), server_default=func.now())
    servicio_ws = Column(String(40))
    exitoso = Column(Boolean)
    codigo_respuesta = Column(String(50))
    mensaje_dian = Column(Text)
    xml_enviado = Column(Text)
    xml_respuesta = Column(Text)


class FeEmpresaConfig(Base):
    """Configuración por empresa emisora (§13). Una fila por cada NIT que emite.

    Nota: PIN, clave técnica y certificados son secretos; idealmente provienen de
    variables de entorno/vault. Las columnas existen por compatibilidad con el §13.
    """

    __tablename__ = "fe_empresas_config"

    nit = Column(String(20), primary_key=True)
    razon_social = Column(String(255), nullable=False)
    prefijo = Column(String(20))
    rango_desde = Column(Integer)
    rango_hasta = Column(Integer)
    numero_actual = Column(Integer)  # último consecutivo usado
    resolucion_numero = Column(String(50))
    resolucion_fecha = Column(Date)
    resolucion_fecha_desde = Column(Date)  # Control.StartDate (vigencia resolución)
    resolucion_fecha_hasta = Column(Date)  # Control.EndDate
    clave_tecnica = Column(String(255))  # secreto
    software_id = Column(String(100))
    software_pin = Column(String(100))  # secreto
    test_id = Column(String(100))  # TestID del set de habilitación
    cert_firma_path = Column(String(500))
    ambiente = Column(String(20), default="habilitacion")
    # Datos fiscales/dirección del emisor para construir el nodo UBL Company (§6.1).
    digito_verificacion = Column(String(2))
    tipo_documento = Column(String(5), default="31")  # 31 = NIT
    tax_level_code = Column(String(20), default="R-99-PN")  # responsabilidad fiscal
    direccion = Column(String(255))
    departamento_code = Column(String(5))  # CountrySubentityCode (p. ej. "11")
    departamento = Column(String(100))  # CountrySubentity (p. ej. "Bogotá D.C.")
    municipio_code = Column(String(10))  # AddressID (p. ej. "11001")
    ciudad = Column(String(100))  # CityName
