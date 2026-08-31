-- ============================================================
-- Migración: registro de cambios de datos del cliente
-- Ejecutar completa y en orden en el SQL Editor de Supabase.
-- Idempotente: se puede volver a correr sin efecto si ya se aplicó.
-- ============================================================

-- Verificación previa (solo lectura)
SELECT count(*) AS clientes_antes FROM clientes;

-- Historial de correcciones hechas por las asesoras desde la aplicación
-- (vía EditarCliente / CAMPOS_EDITABLES), para poder generar después un
-- reporte que los jefes usen al solicitar los cambios en el ERP (ecom).
-- NO registra cambios de la franja horaria (preferencia interna, no
-- existe en ecom) ni sobrescrituras de la carga del Excel (no son una
-- corrección de la asesora).
CREATE TABLE IF NOT EXISTS cambios_cliente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    asesor TEXT,
    campo TEXT NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    fecha DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cambios_cliente_fecha ON cambios_cliente (fecha);
CREATE INDEX IF NOT EXISTS idx_cambios_cliente_cliente_created ON cambios_cliente (cliente_id, created_at DESC);

-- Verificación posterior (solo lectura)
SELECT column_name FROM information_schema.columns WHERE table_name = 'cambios_cliente';
SELECT count(*) AS filas_cambios_cliente FROM cambios_cliente;
