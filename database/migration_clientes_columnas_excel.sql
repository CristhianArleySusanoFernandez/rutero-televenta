-- ============================================================
-- Migración: columnas del Excel que hoy se descartan al cargar el rutero
-- Fecha: 2026-08-30
--
-- Agrega a clientes:
--   novedad_excel  → texto libre de la columna "Novedades" del Excel, lo
--                    que anota el asesor de campo sobre el cliente.
--                    NO tiene relación con la tabla `novedades` del
--                    sistema (esa es el registro de resultados de llamada
--                    de televenta) — se nombra distinto a propósito para
--                    que nadie las confunda ni las mezcle en una consulta.
--   asesor_campo   → nombre de quien visita al cliente en campo, según la
--                    columna "ASESOR" del Excel. Es solo informativo: NO
--                    determina el dueño del rutero de televenta (BR-016),
--                    ese sigue siendo siempre quien tiene la sesión
--                    abierta al cargar el archivo.
--
-- Es aditiva y re-ejecutable: solo agrega columnas NULL-ables, sin
-- default ni backfill — el dato no existe hoy en ninguna parte, se
-- empieza a poblar recién en la próxima carga de Excel que traiga estas
-- columnas. No toca ninguna fila ni columna existente.
--
-- Ejecutar completa y en orden en el SQL Editor de Supabase.
-- ============================================================

-- ------------------------------------------------------------
-- 0. Conteo previo (solo lectura, no modifica nada)
-- ------------------------------------------------------------
SELECT count(*) AS total_clientes FROM clientes;

-- ------------------------------------------------------------
-- 1. Columnas nuevas (aditivas, sin backfill)
-- ------------------------------------------------------------
ALTER TABLE clientes
  ADD COLUMN IF NOT EXISTS novedad_excel TEXT,
  ADD COLUMN IF NOT EXISTS asesor_campo TEXT;

-- ------------------------------------------------------------
-- 2. Verificación posterior (solo lectura)
--    Justo después de ejecutar esto, ambas columnas deben salir en 0 —
--    se llenan recién con la próxima carga de un Excel que las traiga.
-- ------------------------------------------------------------
SELECT
    count(*) FILTER (WHERE novedad_excel IS NOT NULL) AS con_novedad_excel,
    count(*) FILTER (WHERE asesor_campo IS NOT NULL) AS con_asesor_campo
FROM clientes;
