-- ============================================================
-- Migración: soporte del nuevo formato de rutero
-- (ACTUALIZACION_DATOS_TV_*.xlsx, hoja "Informe")
-- Ejecutar completa y en orden en el SQL Editor de Supabase.
-- Idempotente: se puede volver a correr sin efecto si ya se aplicó.
-- ============================================================

-- Verificación previa (solo lectura)
SELECT count(*) AS clientes_antes FROM clientes;
SELECT count(*) AS asesores_antes FROM asesores;

-- Columnas nuevas del archivo nuevo que no existían en el antiguo.
-- Todas nullable, sin backfill: los clientes cargados con el formato
-- viejo simplemente quedan con estos campos en NULL.
-- email / segmento / telefono2: informativos, tal como vienen del Excel.
-- telefono2 NO se integra con la marcación (solo se guarda y se muestra).
-- observacion_excel: categoría del problema (NO CONTESTA, ACTUALIZAR
-- DATOS, CERRO NEGOCIO, DATOS CORRECTOS) — columna "OBSERVACION".
-- dato_a_corregir: el dato puntual que debe corregirse, columna
-- "DATO A CORREGIR". Ninguna de las dos genera todavía un reporte para
-- los jefes (fase posterior); aquí solo se guardan.
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS segmento TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS telefono2 TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS observacion_excel TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS dato_a_corregir TEXT;

-- Código de asesora (puesto, no persona): las televendedoras rotan de
-- puesto pero el código (ej. 10964, 10991) se mantiene. Se usa para
-- filtrar, al cargar el archivo nuevo, solo las filas que correspondan
-- a la asesora que lo sube — cargar el rutero completo de otra asesora
-- sería un daño difícil de deshacer a mano.
ALTER TABLE asesores ADD COLUMN IF NOT EXISTS codigo_asesor TEXT;

-- Verificación posterior (solo lectura)
SELECT column_name FROM information_schema.columns
    WHERE table_name = 'clientes'
    AND column_name IN ('email', 'segmento', 'telefono2', 'observacion_excel', 'dato_a_corregir');
SELECT column_name FROM information_schema.columns
    WHERE table_name = 'asesores' AND column_name = 'codigo_asesor';
