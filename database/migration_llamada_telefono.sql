-- ============================================================
-- Migración: correlación llamada WebSocket ⇄ cola
-- Fecha: 2026-07-14
--
-- Agrega a rutero_clientes:
--   llamada_id   → UUID de la ÚLTIMA llamada ordenada al teléfono
--                  (generado por el servidor al enviar 'llamar')
--   duracion_seg → duración reportada por el teléfono en el IDLE
--
-- Limitación aceptada: en reintentos se sobrescribe con la última
-- llamada; no se guarda historial de todos los intentos.
--
-- Es seguro ejecutarla sobre datos existentes: solo agrega columnas
-- NULL-ables, no modifica ninguna fila.
-- ============================================================

ALTER TABLE rutero_clientes
  ADD COLUMN IF NOT EXISTS llamada_id uuid,
  ADD COLUMN IF NOT EXISTS duracion_seg integer;

-- Índice para el UPDATE por llamada_id cuando llega el IDLE
CREATE INDEX IF NOT EXISTS idx_rutero_clientes_llamada_id
  ON rutero_clientes (llamada_id);

-- Verificación (debe mostrar las 2 columnas nuevas):
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'rutero_clientes'
--   AND column_name IN ('llamada_id', 'duracion_seg');
