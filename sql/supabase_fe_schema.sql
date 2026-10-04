-- Facturación electrónica — emisiones (Supabase / PostgreSQL)
-- Ejecutar después de supabase_schema.sql

CREATE TABLE IF NOT EXISTS fe_emisiones (
  id BIGSERIAL PRIMARY KEY,
  modo VARCHAR(20) NOT NULL,
  factura_numero VARCHAR(50),
  estado VARCHAR(30) NOT NULL DEFAULT 'pendiente',
  engine VARCHAR(20),
  dian_status_code INT,
  dian_response TEXT,
  invoice_payload JSONB,
  cufe VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fe_emisiones_factura ON fe_emisiones (factura_numero);
CREATE INDEX IF NOT EXISTS idx_fe_emisiones_estado ON fe_emisiones (estado);

-- =====================================================================
-- Modelo de datos FEV alineado al §13 del Anexo Técnico v1.9.
-- PKs en BIGSERIAL para mantener consistencia con el esquema existente
-- (documentos_dian, empresas, fe_emisiones).
-- =====================================================================

-- Factura electrónica de venta (cabecera). Persiste borradores y emisiones.
CREATE TABLE IF NOT EXISTS fe_facturas (
  id                       BIGSERIAL PRIMARY KEY,
  empresa_nit              VARCHAR(20) NOT NULL,            -- NIT del emisor
  cufe                     VARCHAR(255) UNIQUE,             -- CUFE (NULL si aún es borrador)
  prefijo                  VARCHAR(20),
  numero                   INTEGER,
  factura_numero           VARCHAR(50),                     -- ID completo del documento
  fecha_emision            DATE,
  hora_emision             VARCHAR(20),                     -- "hh:mm:ss-05:00" (preserva UTC-05)
  estado                   VARCHAR(30) NOT NULL DEFAULT 'BORRADOR',
                                                            -- BORRADOR|PENDIENTE|ENVIADA|VALIDADA|RECHAZADA|OFFLINE|ERROR
  adquirente_nit           VARCHAR(20),
  adquirente_nombre        VARCHAR(255),
  subtotal                 NUMERIC(18,2) DEFAULT 0,
  iva                      NUMERIC(18,2) DEFAULT 0,
  total                    NUMERIC(18,2) DEFAULT 0,
  xml_generado             TEXT,                            -- XML antes de firmar (si disponible)
  xml_firmado              TEXT,                            -- XML con firma XAdES-EPES (si disponible)
  application_response     TEXT,                            -- Respuesta XML completa de la DIAN (sin truncar)
  ambiente                 VARCHAR(20) NOT NULL DEFAULT 'habilitacion',
  intentos_transmision     INTEGER DEFAULT 0,
  fecha_transmision        TIMESTAMPTZ,
  es_offline               BOOLEAN DEFAULT FALSE,
  fecha_limite_transmision TIMESTAMPTZ,                     -- +48h desde expedición offline
  invoice_payload          JSONB,                           -- InvoiceDto del borrador (consecutivo tentativo)
  factura_origen_id        BIGINT REFERENCES fe_facturas(id),  -- factura RECHAZADA que esta corrige
  created_at               TIMESTAMPTZ DEFAULT NOW(),
  updated_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fe_facturas_empresa ON fe_facturas (empresa_nit);
CREATE INDEX IF NOT EXISTS idx_fe_facturas_estado ON fe_facturas (estado);
CREATE INDEX IF NOT EXISTS idx_fe_facturas_origen ON fe_facturas (factura_origen_id);

-- Ítems/líneas de cada factura.
CREATE TABLE IF NOT EXISTS fe_factura_items (
  id              BIGSERIAL PRIMARY KEY,
  factura_id      BIGINT NOT NULL REFERENCES fe_facturas(id),
  descripcion     TEXT NOT NULL,
  cantidad        NUMERIC(15,6) NOT NULL,                   -- siempre > 0
  precio_unitario NUMERIC(18,6) NOT NULL,
  descuento       NUMERIC(18,2) DEFAULT 0,
  iva_porcentaje  NUMERIC(5,2) DEFAULT 19,
  subtotal        NUMERIC(18,2) NOT NULL,
  codigo_producto VARCHAR(100),                             -- CCE, GTIN o libre
  unidad_medida   VARCHAR(20) DEFAULT 'EA'                  -- @unitCode §13.2.8.6
);

CREATE INDEX IF NOT EXISTS idx_fe_factura_items_factura ON fe_factura_items (factura_id);

-- Log completo de cada intento de transmisión a la DIAN (XML sin truncar).
CREATE TABLE IF NOT EXISTS fe_log_transmision (
  id               BIGSERIAL PRIMARY KEY,
  factura_id       BIGINT REFERENCES fe_facturas(id),
  fecha_intento    TIMESTAMPTZ DEFAULT NOW(),
  servicio_ws      VARCHAR(40),                             -- SendBillSync|SendTestSetAsync|inline...
  exitoso          BOOLEAN,
  codigo_respuesta VARCHAR(50),
  mensaje_dian     TEXT,
  xml_enviado      TEXT,
  xml_respuesta    TEXT
);

CREATE INDEX IF NOT EXISTS idx_fe_log_transmision_factura ON fe_log_transmision (factura_id);

-- Configuración por empresa emisora (una fila por NIT).
-- ADVERTENCIA: software_pin / clave_tecnica son secretos. Preferir variables de
-- entorno o vault; estas columnas existen por compatibilidad con el §13.
CREATE TABLE IF NOT EXISTS fe_empresas_config (
  nit                    VARCHAR(20) PRIMARY KEY,
  razon_social           VARCHAR(255) NOT NULL,
  prefijo                VARCHAR(20),
  rango_desde            INTEGER,
  rango_hasta            INTEGER,
  numero_actual          INTEGER,                       -- último consecutivo usado
  resolucion_numero      VARCHAR(50),
  resolucion_fecha       DATE,
  resolucion_fecha_desde DATE,                          -- Control.StartDate
  resolucion_fecha_hasta DATE,                          -- Control.EndDate
  clave_tecnica          VARCHAR(255),                  -- secreto
  software_id            VARCHAR(100),
  software_pin           VARCHAR(100),                  -- secreto
  test_id                VARCHAR(100),                  -- TestID set de habilitación
  cert_firma_path        VARCHAR(500),
  ambiente               VARCHAR(20) DEFAULT 'habilitacion',
  -- Datos fiscales/dirección del emisor para el nodo UBL Company (§6.1).
  digito_verificacion    VARCHAR(2),
  tipo_documento         VARCHAR(5) DEFAULT '31',       -- 31 = NIT
  tax_level_code         VARCHAR(20) DEFAULT 'R-99-PN',
  direccion              VARCHAR(255),
  departamento_code      VARCHAR(5),                    -- CountrySubentityCode
  departamento           VARCHAR(100),                  -- CountrySubentity
  municipio_code         VARCHAR(10),                   -- AddressID
  ciudad                 VARCHAR(100)                   -- CityName
);
