-- =====================================================================
-- SEED — fe_empresas_config: 3 EMPRESAS PILOTO (DATOS FICTICIOS)
-- =====================================================================
-- Propósito: poblar fe_empresas_config con datos estructuralmente válidos
-- para probar el flujo completo (borrador → enviada → validada/rechazada)
-- ANTES de cargar los 32 clientes reales.
--
-- ADVERTENCIA: TODOS los secretos aquí (clave_tecnica, software_id,
-- software_pin, test_id) son FICTICIOS. NO sirven para emitir realmente
-- ante la DIAN. Reemplazar por los valores reales de cada empresa (de
-- preferencia vía variables de entorno / vault, no en Git).
--
-- Los NIT y dígitos de verificación SÍ son correctos según el algoritmo
-- DIAN (módulo 11), para que las validaciones de NIT/DV no fallen:
--   901111111-4   901222222-1   901333333-5
--
-- Ambiente: 'habilitacion'. Prefijo y rango imitan un set de pruebas DIAN.
-- numero_actual = rango_desde - 1  ⇒  el primer consecutivo emitido será
-- exactamente rango_desde (p. ej. 990000000).
--
-- Re-ejecutable: usa ON CONFLICT (nit) DO UPDATE (upsert idempotente).
-- Ejecutar después de sql/supabase_fe_schema.sql.
-- =====================================================================

INSERT INTO fe_empresas_config (
    nit, razon_social, prefijo, rango_desde, rango_hasta, numero_actual,
    resolucion_numero, resolucion_fecha, resolucion_fecha_desde, resolucion_fecha_hasta,
    clave_tecnica, software_id, software_pin, test_id, cert_firma_path, ambiente,
    digito_verificacion, tipo_documento, tax_level_code,
    direccion, departamento_code, departamento, municipio_code, ciudad
) VALUES
-- ── Empresa piloto 1 — Bogotá ────────────────────────────────────────
(
    '901111111', 'COMERCIALIZADORA PILOTO UNO S.A.S.', 'SETP', 990000000, 995000000, 989999999,
    '18760000001', DATE '2026-01-15', DATE '2026-01-15', DATE '2027-01-15',
    'fc8eac422eba16e22ffd8c6f94b3f40a6e38162c', '00000000-0000-0000-0000-000000000001', '12345', 'a1b2c3d4-0001-0001-0001-aaaaaaaaaaaa',
    'certs/piloto_uno.pfx', 'habilitacion',
    '4', '31', 'R-99-PN',
    'Calle 100 # 7-21 Oficina 301', '11', 'Bogotá', '11001', 'Bogotá, D.C.'
),
-- ── Empresa piloto 2 — Medellín ──────────────────────────────────────
(
    '901222222', 'SERVICIOS PILOTO DOS LTDA', 'SETP', 990000000, 995000000, 989999999,
    '18760000002', DATE '2026-02-01', DATE '2026-02-01', DATE '2027-02-01',
    'a7f5f35426b927411fc9231b56382173b3f80f3a', '00000000-0000-0000-0000-000000000002', '67890', 'a1b2c3d4-0002-0002-0002-bbbbbbbbbbbb',
    'certs/piloto_dos.pfx', 'habilitacion',
    '1', '31', 'R-99-PN',
    'Carrera 43A # 1-50 Torre Sur', '05', 'Antioquia', '05001', 'Medellín'
),
-- ── Empresa piloto 3 — Cali ──────────────────────────────────────────
(
    '901333333', 'DISTRIBUCIONES PILOTO TRES S.A.S.', 'SETP', 990000000, 995000000, 989999999,
    '18760000003', DATE '2026-03-10', DATE '2026-03-10', DATE '2027-03-10',
    '6b86b273ff34fce19d6b804eff5a3f5747ada4ea', '00000000-0000-0000-0000-000000000003', '24680', 'a1b2c3d4-0003-0003-0003-cccccccccccc',
    'certs/piloto_tres.pfx', 'habilitacion',
    '5', '31', 'R-99-PN',
    'Avenida 6N # 28-10 Local 4', '76', 'Valle del Cauca', '76001', 'Santiago de Cali'
)
ON CONFLICT (nit) DO UPDATE SET
    razon_social           = EXCLUDED.razon_social,
    prefijo                = EXCLUDED.prefijo,
    rango_desde            = EXCLUDED.rango_desde,
    rango_hasta            = EXCLUDED.rango_hasta,
    numero_actual          = EXCLUDED.numero_actual,
    resolucion_numero      = EXCLUDED.resolucion_numero,
    resolucion_fecha       = EXCLUDED.resolucion_fecha,
    resolucion_fecha_desde = EXCLUDED.resolucion_fecha_desde,
    resolucion_fecha_hasta = EXCLUDED.resolucion_fecha_hasta,
    clave_tecnica          = EXCLUDED.clave_tecnica,
    software_id            = EXCLUDED.software_id,
    software_pin           = EXCLUDED.software_pin,
    test_id                = EXCLUDED.test_id,
    cert_firma_path        = EXCLUDED.cert_firma_path,
    ambiente               = EXCLUDED.ambiente,
    digito_verificacion    = EXCLUDED.digito_verificacion,
    tipo_documento         = EXCLUDED.tipo_documento,
    tax_level_code         = EXCLUDED.tax_level_code,
    direccion              = EXCLUDED.direccion,
    departamento_code      = EXCLUDED.departamento_code,
    departamento           = EXCLUDED.departamento,
    municipio_code         = EXCLUDED.municipio_code,
    ciudad                 = EXCLUDED.ciudad;

-- Verificación rápida (no muestra secretos):
-- SELECT nit, razon_social, prefijo, rango_desde, rango_hasta, numero_actual, ambiente
-- FROM fe_empresas_config ORDER BY nit;
