-- =====================================================================
-- MIGRACIÓN — Gestión de estados y borradores re-emisibles
-- =====================================================================
-- Aplica a bases ya creadas con supabase_fe_schema.sql (donde CREATE TABLE
-- IF NOT EXISTS no agregaría columnas nuevas). Idempotente.
--
-- 1) invoice_payload: guarda el InvoiceDto del BORRADOR para poder
--    re-emitirlo después sin reconstruirlo desde cero. En un borrador, el
--    consecutivo del payload es TENTATIVO; el definitivo se estampa al enviar.
-- 2) factura_origen_id: trazabilidad de corrección. Cuando una factura
--    RECHAZADA se corrige, se crea una factura NUEVA que apunta aquí a la
--    original. La original permanece RECHAZADA de forma permanente.
-- =====================================================================

ALTER TABLE fe_facturas
    ADD COLUMN IF NOT EXISTS invoice_payload   JSONB;

ALTER TABLE fe_facturas
    ADD COLUMN IF NOT EXISTS factura_origen_id BIGINT REFERENCES fe_facturas(id);

CREATE INDEX IF NOT EXISTS idx_fe_facturas_origen ON fe_facturas (factura_origen_id);
