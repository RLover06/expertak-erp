-- Expertak schema for Supabase (PostgreSQL)
-- Run in: Supabase Dashboard → SQL Editor → New query

-- Documentos electrónicos DIAN (importación Excel)
CREATE TABLE IF NOT EXISTS documentos_dian (
  id BIGSERIAL PRIMARY KEY,
  tipo_documento VARCHAR(100) NOT NULL,
  cufe_cude VARCHAR(255) NOT NULL UNIQUE,
  folio VARCHAR(50),
  prefijo VARCHAR(20),
  divisa VARCHAR(10),
  forma_pago VARCHAR(50),
  medio_pago VARCHAR(50),
  fecha_emision DATE,
  fecha_recepcion TIMESTAMPTZ,
  nit_emisor BIGINT,
  nombre_emisor VARCHAR(255),
  nit_receptor BIGINT,
  nombre_receptor VARCHAR(255),
  iva NUMERIC(18, 2) DEFAULT 0,
  ica NUMERIC(18, 2) DEFAULT 0,
  ic NUMERIC(18, 2) DEFAULT 0,
  inc NUMERIC(18, 2) DEFAULT 0,
  timbre NUMERIC(18, 2) DEFAULT 0,
  inc_bolsas NUMERIC(18, 2) DEFAULT 0,
  in_carbono NUMERIC(18, 2) DEFAULT 0,
  in_combustibles NUMERIC(18, 2) DEFAULT 0,
  ic_datos NUMERIC(18, 2) DEFAULT 0,
  icl NUMERIC(18, 2) DEFAULT 0,
  inpp NUMERIC(18, 2) DEFAULT 0,
  ibua NUMERIC(18, 2) DEFAULT 0,
  icui NUMERIC(18, 2) DEFAULT 0,
  rete_iva NUMERIC(18, 2) DEFAULT 0,
  rete_renta NUMERIC(18, 2) DEFAULT 0,
  rete_ica NUMERIC(18, 2) DEFAULT 0,
  total NUMERIC(18, 2) NOT NULL,
  estado VARCHAR(50),
  grupo VARCHAR(50),
  empresa VARCHAR(255),
  archivo_origen VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_documentos_dian_cufe ON documentos_dian (cufe_cude);
CREATE INDEX IF NOT EXISTS idx_documentos_dian_fecha ON documentos_dian (fecha_emision);

-- Contabilidad: empresas, terceros, movimientos consolidado
CREATE TABLE IF NOT EXISTS empresas (
  id BIGSERIAL PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL,
  nit VARCHAR(50),
  UNIQUE (nombre, nit)
);

CREATE TABLE IF NOT EXISTS terceros (
  id BIGSERIAL PRIMARY KEY,
  nombre VARCHAR(255) NOT NULL,
  nit VARCHAR(50),
  UNIQUE (nombre, nit)
);

CREATE TABLE IF NOT EXISTS consolidado_movimientos (
  id BIGSERIAL PRIMARY KEY,
  empresa_id BIGINT NOT NULL REFERENCES empresas (id),
  tercero_id BIGINT NOT NULL REFERENCES terceros (id),
  fecha DATE NOT NULL,
  cuenta VARCHAR(100) NOT NULL,
  debito NUMERIC(18, 2) DEFAULT 0,
  credito NUMERIC(18, 2) DEFAULT 0,
  documento_origen VARCHAR(255),
  periodo VARCHAR(50),
  archivo_origen VARCHAR(255),
  fecha_importacion TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_consolidado_empresa ON consolidado_movimientos (empresa_id);
CREATE INDEX IF NOT EXISTS idx_consolidado_tercero ON consolidado_movimientos (tercero_id);
CREATE INDEX IF NOT EXISTS idx_consolidado_fecha ON consolidado_movimientos (fecha);
CREATE INDEX IF NOT EXISTS idx_consolidado_cuenta ON consolidado_movimientos (cuenta);

-- Resumen pre-agregado (INFORME RELACION_FE)
CREATE TABLE IF NOT EXISTS resumen_filas (
  id BIGSERIAL PRIMARY KEY,
  empresa VARCHAR(255) NOT NULL,
  tipo_documento VARCHAR(100) NOT NULL,
  grupo VARCHAR(50),
  subtotal NUMERIC(18, 2) DEFAULT 0,
  iva NUMERIC(18, 2) DEFAULT 0,
  total_otros NUMERIC(18, 2) DEFAULT 0,
  total_renta NUMERIC(18, 2) DEFAULT 0,
  total NUMERIC(18, 2) DEFAULT 0,
  archivo_origen VARCHAR(255),
  fecha_importacion TIMESTAMPTZ DEFAULT NOW()
);
