-- ============================================================
-- Itaú Dashboard · Database Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    color       VARCHAR(7)   NOT NULL DEFAULT '#00c795',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS statements (
    id             SERIAL PRIMARY KEY,
    account_name   VARCHAR(255),
    year           INTEGER     NOT NULL,
    month          INTEGER     NOT NULL,
    fecha_estado   VARCHAR(20),
    saldo_apertura NUMERIC(15, 2),
    saldo_cierre   NUMERIC(15, 2),
    saldo_promedio NUMERIC(15, 2),
    filename       VARCHAR(255),
    uploaded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (year, month)
);

CREATE TABLE IF NOT EXISTS references_catalog (
    id          SERIAL PRIMARY KEY,
    descripcion VARCHAR(255) NOT NULL UNIQUE,
    category_id INTEGER REFERENCES categories (id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id             SERIAL PRIMARY KEY,
    statement_id   INTEGER     NOT NULL REFERENCES statements (id) ON DELETE CASCADE,
    position       INTEGER     NOT NULL,   -- índice 0-based en el archivo fuente
    fecha          VARCHAR(10) NOT NULL,
    fecha_completa DATE,
    tipo           VARCHAR(100),
    descripcion    VARCHAR(255),
    reference_id   INTEGER REFERENCES references_catalog (id) ON DELETE SET NULL,
    debito         NUMERIC(15, 2),
    credito        NUMERIC(15, 2),
    saldo          NUMERIC(15, 2),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (statement_id, position)
);

CREATE INDEX IF NOT EXISTS idx_transactions_statement ON transactions (statement_id);
CREATE INDEX IF NOT EXISTS idx_transactions_fecha_completa ON transactions (fecha_completa);
CREATE INDEX IF NOT EXISTS idx_transactions_reference ON transactions (reference_id);
CREATE INDEX IF NOT EXISTS idx_references_category ON references_catalog (category_id);

-- Categorías por defecto
INSERT INTO categories (name, color) VALUES
    ('Supermercados',  '#00c795'),
    ('Restaurantes',   '#f59e0b'),
    ('Transporte',     '#3b82f6'),
    ('Salud',          '#ec4899'),
    ('Tecnología',     '#8b5cf6'),
    ('Transferencias', '#64748b'),
    ('Ingresos',       '#22c55e'),
    ('Servicios',      '#06b6d4'),
    ('Otros',          '#94a3b8')
ON CONFLICT (name) DO NOTHING;
