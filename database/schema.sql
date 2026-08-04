-- ============================================================
-- Esquema de base de datos - Rutero Televenta Nutresa
-- Ejecutar en el SQL Editor de Supabase (idempotente — se puede volver a correr)
-- ============================================================

-- Clientes del sistema
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cod_cliente TEXT UNIQUE NOT NULL,
    documento TEXT,
    nombre TEXT NOT NULL,
    razon_social TEXT,
    direccion TEXT,
    barrio TEXT,
    ciudad TEXT,
    dias_visita TEXT,
    telefono TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Rutero diario
CREATE TABLE IF NOT EXISTS rutero_dias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha DATE NOT NULL UNIQUE,
    usuario_id TEXT,
    asesor TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Clientes en el rutero de un día
-- estados: pendiente | reintento_pendiente | reagendado | contesto | no_contesto | novedad
CREATE TABLE IF NOT EXISTS rutero_clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rutero_dia_id UUID REFERENCES rutero_dias(id) ON DELETE CASCADE,
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    estado TEXT DEFAULT 'pendiente' CHECK (estado IN (
        'pendiente', 'reintento_pendiente', 'reagendado',
        'contesto', 'no_contesto', 'novedad'
    )),
    posicion_cola     INTEGER,           -- orden en la cola del día
    contador_intentos INTEGER DEFAULT 0, -- 0=sin intentos, 1=primer no-contesta, 2=final
    reagendado_para   TIMESTAMPTZ,       -- cuándo reincorporar al reagendado
    nota_llamada      TEXT,              -- nota libre al registrar resultado
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Novedades registradas
CREATE TABLE IF NOT EXISTS novedades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rutero_cliente_id UUID REFERENCES rutero_clientes(id) ON DELETE CASCADE,
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    tipo TEXT NOT NULL,
    observacion TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Notas permanentes del cliente (preferencias, advertencias entre semanas)
CREATE TABLE IF NOT EXISTS notas_cliente (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
    nota TEXT NOT NULL,
    autor TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE notas_cliente DISABLE ROW LEVEL SECURITY;

-- ============================================================
-- Migraciones para bases existentes (sin efecto si ya existe)
-- ============================================================
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS posicion_cola INTEGER;
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS contador_intentos INTEGER DEFAULT 0;
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS reagendado_para TIMESTAMPTZ;
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS nota_llamada TEXT;

-- Ampliar el CHECK de estado en rutero_clientes existente
-- (Supabase no permite ALTER CHECK directamente; se recrea la constraint)
ALTER TABLE rutero_clientes DROP CONSTRAINT IF EXISTS rutero_clientes_estado_check;
ALTER TABLE rutero_clientes ADD CONSTRAINT rutero_clientes_estado_check
    CHECK (estado IN ('pendiente', 'reintento_pendiente', 'reagendado',
                      'contesto', 'no_contesto', 'novedad'));

-- ============================================================
-- Índices
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_rutero_dias_fecha        ON rutero_dias(fecha);
CREATE INDEX IF NOT EXISTS idx_rutero_clientes_rutero_dia ON rutero_clientes(rutero_dia_id);
CREATE INDEX IF NOT EXISTS idx_rutero_clientes_cliente  ON rutero_clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_rutero_clientes_cola     ON rutero_clientes(rutero_dia_id, posicion_cola);
CREATE INDEX IF NOT EXISTS idx_novedades_cliente        ON novedades(cliente_id);
CREATE INDEX IF NOT EXISTS idx_novedades_fecha          ON novedades(fecha);
CREATE INDEX IF NOT EXISTS idx_novedades_rutero_cliente ON novedades(rutero_cliente_id);
CREATE INDEX IF NOT EXISTS idx_notas_cliente            ON notas_cliente(cliente_id);

-- ============================================================
-- Trigger updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_rutero_clientes_updated_at ON rutero_clientes;
CREATE TRIGGER trigger_rutero_clientes_updated_at
    BEFORE UPDATE ON rutero_clientes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- Multi-asesor: un rutero por (fecha, asesor) en vez de por fecha global
-- ============================================================

-- Asesores conocidos y su teléfono asignado (Opción A ya no aplica: el
-- teléfono se resuelve por asesor, no por PC/servidor).
CREATE TABLE IF NOT EXISTS asesores (
    nombre TEXT PRIMARY KEY,
    telefono_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- rutero_dias pasa de "una fila por fecha" a "una fila por (fecha, asesor)"
ALTER TABLE rutero_dias DROP CONSTRAINT IF EXISTS rutero_dias_fecha_key;
ALTER TABLE rutero_dias ADD CONSTRAINT rutero_dias_fecha_asesor_key UNIQUE (fecha, asesor);

CREATE INDEX IF NOT EXISTS idx_rutero_dias_fecha_asesor ON rutero_dias(fecha, asesor);
