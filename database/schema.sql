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

-- Pedidos registrados por cliente (texto libre, NO catálogo de productos).
-- cliente_id CASCADE (sin cliente el pedido no tiene sentido);
-- rutero_cliente_id SET NULL (mismo criterio que novedades, BR-014: el
-- historial de compras sobrevive a la eliminación de un rutero).
CREATE TABLE IF NOT EXISTS pedidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    rutero_cliente_id UUID REFERENCES rutero_clientes(id) ON DELETE SET NULL,
    asesor TEXT,
    fecha DATE NOT NULL,
    detalle TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pedidos_cliente_fecha ON pedidos (cliente_id, fecha DESC);
CREATE INDEX IF NOT EXISTS idx_pedidos_asesor_created ON pedidos (asesor, created_at DESC);

-- Historial de correcciones de datos de cliente hechas por las asesoras
-- (vía EditarCliente), para un futuro reporte de solicitudes de cambio
-- al ERP (ecom). NO registra franja horaria ni sobrescrituras del Excel.
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

-- ============================================================
-- Migraciones para bases existentes (sin efecto si ya existe)
-- ============================================================
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS posicion_cola INTEGER;
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS contador_intentos INTEGER DEFAULT 0;
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS reagendado_para TIMESTAMPTZ;
ALTER TABLE rutero_clientes ADD COLUMN IF NOT EXISTS nota_llamada TEXT;

-- Dashboard de novedades: asesor (denormalizado para no depender del join
-- rutero_cliente_id -> rutero_dias, que se rompe si el rutero fue borrado)
-- y anulación lógica sin borrar el registro.
ALTER TABLE novedades ADD COLUMN IF NOT EXISTS asesor TEXT;
ALTER TABLE novedades ADD COLUMN IF NOT EXISTS anulada BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE novedades ADD COLUMN IF NOT EXISTS anulada_motivo TEXT;

-- Columnas del Excel que antes se descartaban al cargar el rutero.
-- novedad_excel: texto libre de la columna "Novedades" del Excel (lo que
-- anota el asesor de campo) — sin relación con la tabla `novedades` de
-- arriba, nombrada distinto a propósito para no confundirlas.
-- asesor_campo: quien visita al cliente en campo según la columna
-- "ASESOR" del Excel — solo informativo, no determina el dueño del
-- rutero de televenta (BR-016).
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS novedad_excel TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS asesor_campo TEXT;

-- Franja horaria preferida del cliente para ser llamado (permanente, NO
-- viene del Excel — por eso NO debe agregarse a _to_row() en
-- supabase_cliente_repository.py, o el upsert la perdería en cada carga).
-- Ambas NULL = sin preferencia (estado por defecto).
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS franja_desde TIME;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS franja_hasta TIME;

-- Columnas del formato nuevo de rutero (ACTUALIZACION_DATOS_TV_*.xlsx).
-- Vienen del Excel: se sobrescriben en cada carga (opción A), igual que
-- el resto de _to_row(). telefono2 solo se guarda y se muestra, NO se
-- integra con la marcación.
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS segmento TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS telefono2 TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS observacion_excel TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS dato_a_corregir TEXT;

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
CREATE INDEX IF NOT EXISTS idx_novedades_asesor_fecha    ON novedades(asesor, fecha);
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

-- Código de asesora (puesto, no persona): las televendedoras rotan de
-- puesto pero el código (ej. 10964, 10991) se mantiene. Se usa para
-- filtrar, al cargar el formato nuevo de rutero, solo las filas que
-- correspondan a la asesora que lo sube.
ALTER TABLE asesores ADD COLUMN IF NOT EXISTS codigo_asesor TEXT;

-- rutero_dias pasa de "una fila por fecha" a "una fila por (fecha, asesor)"
ALTER TABLE rutero_dias DROP CONSTRAINT IF EXISTS rutero_dias_fecha_key;
ALTER TABLE rutero_dias ADD CONSTRAINT rutero_dias_fecha_asesor_key UNIQUE (fecha, asesor);

CREATE INDEX IF NOT EXISTS idx_rutero_dias_fecha_asesor ON rutero_dias(fecha, asesor);

-- Falta desde siempre: crear_llamada() hace upsert con
-- on_conflict="rutero_dia_id,cliente_id" pero nunca existió el constraint
-- que ese ON CONFLICT necesita (42P10: "no unique or exclusion constraint
-- matching the ON CONFLICT specification").
ALTER TABLE rutero_clientes DROP CONSTRAINT IF EXISTS rutero_clientes_rutero_dia_id_cliente_id_key;
ALTER TABLE rutero_clientes ADD CONSTRAINT rutero_clientes_rutero_dia_id_cliente_id_key
    UNIQUE (rutero_dia_id, cliente_id);

-- ============================================================
-- Eliminar rutero cargado: al borrar un rutero_dia (y en cascada sus
-- rutero_clientes), las novedades de esos clientes NO deben perderse —
-- son historial del cliente, no del rutero. CASCADE las borraría; con
-- SET NULL la novedad sobrevive (queda sin rutero_cliente_id, pero
-- conserva cliente_id, que es lo que usa el historial para listarlas).
-- ============================================================
ALTER TABLE novedades DROP CONSTRAINT IF EXISTS novedades_rutero_cliente_id_fkey;
ALTER TABLE novedades ADD CONSTRAINT novedades_rutero_cliente_id_fkey
    FOREIGN KEY (rutero_cliente_id) REFERENCES rutero_clientes(id) ON DELETE SET NULL;
