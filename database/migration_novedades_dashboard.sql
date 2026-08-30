-- ============================================================
-- Migración: columnas de soporte para dashboard de novedades
-- Fecha: 2026-08-25
--
-- Agrega a novedades:
--   asesor          → nombre del asesor que generó la novedad, retrocalculado
--                      (backfill) para las filas existentes vía
--                      novedades.rutero_cliente_id -> rutero_clientes.rutero_dia_id
--                      -> rutero_dias.asesor. Las novedades cuyo
--                      rutero_cliente_id ya es NULL (rutero eliminado, ver
--                      migración de FK ON DELETE SET NULL) no se pueden
--                      backfillear y quedan con asesor = NULL.
--   anulada         → booleano para marcar una novedad como anulada sin
--                      borrarla. Default false: todas las filas existentes
--                      quedan activas (comportamiento actual sin cambios).
--   anulada_motivo  → texto libre opcional con el motivo de la anulación.
--
-- Es aditiva y re-ejecutable: solo agrega columnas NULL-ables o con
-- default, y el UPDATE de backfill solo toca la columna `asesor` en filas
-- donde `asesor IS NULL` y `rutero_cliente_id IS NOT NULL` — no borra, no
-- vacía ni sobrescribe ninguna fila ni columna existente.
--
-- Ejecutar completa y en orden en el SQL Editor de Supabase.
-- ============================================================

-- ------------------------------------------------------------
-- 0. Conteo previo (solo lectura, no modifica nada)
-- ------------------------------------------------------------
SELECT
    count(*) AS total_novedades,
    count(*) FILTER (WHERE rutero_cliente_id IS NOT NULL) AS backfillables_con_rutero_cliente_id,
    count(*) FILTER (WHERE rutero_cliente_id IS NULL) AS quedaran_sin_asesor
FROM novedades;

-- ------------------------------------------------------------
-- 1. Columnas nuevas (aditivas)
-- ------------------------------------------------------------
ALTER TABLE novedades
  ADD COLUMN IF NOT EXISTS asesor TEXT,
  ADD COLUMN IF NOT EXISTS anulada BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS anulada_motivo TEXT;

-- ------------------------------------------------------------
-- 2. Backfill de `asesor` para filas existentes
--    Solo toca `asesor`, solo donde está NULL y hay rutero_cliente_id.
-- ------------------------------------------------------------
UPDATE novedades AS n
SET asesor = rd.asesor
FROM rutero_clientes AS rc
JOIN rutero_dias AS rd ON rd.id = rc.rutero_dia_id
WHERE rc.id = n.rutero_cliente_id
  AND n.asesor IS NULL
  AND n.rutero_cliente_id IS NOT NULL;

-- ------------------------------------------------------------
-- 3. Índice para las consultas del dashboard
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_novedades_asesor_fecha
  ON novedades (asesor, fecha);

-- ------------------------------------------------------------
-- 4. Verificación posterior (solo lectura)
-- ------------------------------------------------------------
SELECT
    count(*) FILTER (WHERE asesor IS NOT NULL) AS con_asesor,
    count(*) FILTER (WHERE asesor IS NULL) AS sin_asesor
FROM novedades;
