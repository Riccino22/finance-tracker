from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from database import Base, engine
from routers import statements, transactions, categories, analytics

# Create all tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

# ── Migración incremental: agrega `position` si no existe ─────────────────────
# Seguro de correr múltiples veces (IF NOT EXISTS / DO $$ ... END).
_MIGRATION = """
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS position INTEGER NOT NULL DEFAULT 0;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS nota TEXT;

-- Asigna posiciones secuenciales a filas existentes que quedaron en 0
UPDATE transactions t
SET    position = sub.rn - 1
FROM  (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY statement_id ORDER BY id) AS rn
    FROM   transactions
    WHERE  position = 0
) sub
WHERE  t.id = sub.id;

-- Agrega la restricción única solo si no existe todavía
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_transaction_stmt_pos'
    ) THEN
        ALTER TABLE transactions
            ADD CONSTRAINT uq_transaction_stmt_pos UNIQUE (statement_id, position);
    END IF;
END $$;
"""

with engine.begin() as conn:
    conn.execute(text(_MIGRATION))

app = FastAPI(
    title="Banco Dashboard API",
    description="REST API para el dashboard de movimientos bancarios",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(statements.router,   prefix="/statements",   tags=["Statements"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(categories.router,   prefix="/categories",   tags=["Categories"])
app.include_router(analytics.router,    prefix="/analytics",    tags=["Analytics"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
