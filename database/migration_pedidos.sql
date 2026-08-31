-- ============================================================
-- Migración: registro de pedidos por cliente
-- Fecha: 2026-08-31
--
-- Tabla nueva `pedidos`: texto libre de lo vendido en cada llamada, para
-- que la asesora vea el historial reciente del cliente y una señal de
-- cuánto lleva sin comprar. NO es un catálogo de productos (el ERP de
-- la empresa no tiene una base de productos actualizada) — es texto
-- libre, sin intención de parsear ni analizar por producto.
--
-- cliente_id  → ON DELETE CASCADE: sin cliente, el pedido no tiene
--               sentido (a diferencia de novedades, que sobreviven
--               porque documentan la gestión, no una venta).
-- rutero_cliente_id → NULLABLE, ON DELETE SET NULL: mismo criterio que
--               `novedades.rutero_cliente_id` (ver BR-014) — el
--               historial de compras del cliente sobrevive a que se
--               elimine el rutero donde se registró.
-- asesor      → quién lo registró (para las sugerencias por asesor).
-- fecha       → la del rutero trabajado, mismo criterio que `novedades`
--               (no necesariamente la fecha calendario real del server).
-- detalle     → texto libre, obligatorio.
--
-- Es aditiva y re-ejecutable (`CREATE TABLE IF NOT EXISTS`, índices
-- `IF NOT EXISTS`). Sin backfill: la tabla no existía, no hay datos que
-- migrar.
--
-- Ejecutar completa y en orden en el SQL Editor de Supabase.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Tabla nueva
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pedidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    rutero_cliente_id UUID REFERENCES rutero_clientes(id) ON DELETE SET NULL,
    asesor TEXT,
    fecha DATE NOT NULL,
    detalle TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ------------------------------------------------------------
-- 2. Índices
--    (cliente_id, fecha DESC) → historial del cliente (últimos N).
--    (asesor, created_at DESC) → sugerencias de texto por asesor.
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_fecha ON pedidos (cliente_id, fecha DESC);
CREATE INDEX IF NOT EXISTS idx_pedidos_asesor_created ON pedidos (asesor, created_at DESC);

-- ------------------------------------------------------------
-- 3. Verificación posterior (solo lectura)
-- ------------------------------------------------------------
SELECT count(*) AS total_pedidos FROM pedidos;
