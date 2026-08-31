-- ============================================================
-- Migración: franja horaria preferida por cliente
-- Fecha: 2026-08-31
--
-- Agrega a clientes:
--   franja_desde TIME  → inicio de la franja horaria en que el cliente
--                        prefiere ser llamado (ej. 08:00).
--   franja_hasta TIME  → fin de esa franja (ej. 10:00).
--
-- Ambas NULL = sin preferencia registrada — es el estado de TODOS los
-- clientes existentes hoy, y sigue siendo válido indefinidamente si la
-- asesora nunca la registra. No es obligatorio.
--
-- IMPORTANTE: estas columnas NO vienen del Excel y NO deben agregarse a
-- `_to_row()` en supabase_cliente_repository.py. Esa función solo debe
-- listar las columnas que sí trae el Excel; si `franja_desde`/
-- `franja_hasta` faltan de esa lista, el upsert de cada carga no las
-- toca y la preferencia sobrevive intacta semana tras semana. Agregarlas
-- ahí las pisaría con NULL en la próxima carga porque el Excel no las
-- trae.
--
-- Es aditiva y re-ejecutable: solo agrega columnas NULL-ables, sin
-- backfill — el dato no existe hoy en ninguna parte.
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
  ADD COLUMN IF NOT EXISTS franja_desde TIME,
  ADD COLUMN IF NOT EXISTS franja_hasta TIME;

-- ------------------------------------------------------------
-- 2. Verificación posterior (solo lectura)
--    Justo después de ejecutar esto, debe salir en 0 — se llena
--    recién cuando una asesora registre una franja por primera vez.
-- ------------------------------------------------------------
SELECT
    count(*) FILTER (WHERE franja_desde IS NOT NULL OR franja_hasta IS NOT NULL) AS con_franja_registrada
FROM clientes;
