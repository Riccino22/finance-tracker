from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


# ── Categories ──────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:  str
    color: str = "#00c795"

class CategoryUpdate(BaseModel):
    name:  Optional[str] = None
    color: Optional[str] = None

class CategoryOut(BaseModel):
    id:         int
    name:       str
    color:      str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── References ──────────────────────────────────────────────────────────────

class ReferenceOut(BaseModel):
    id:          int
    descripcion: str
    category_id: Optional[int]
    category:    Optional[CategoryOut]
    created_at:  datetime

    model_config = {"from_attributes": True}

class ReferenceAssign(BaseModel):
    category_id: Optional[int]


# ── Transactions ─────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id:             int
    statement_id:   int
    fecha:          str
    fecha_completa: Optional[date]
    tipo:           Optional[str]
    descripcion:    Optional[str]
    reference_id:   Optional[int]
    category:       Optional[CategoryOut]
    debito:         Optional[Decimal]
    credito:        Optional[Decimal]
    saldo:          Optional[Decimal]
    created_at:     datetime

    model_config = {"from_attributes": True}


# ── Statements ───────────────────────────────────────────────────────────────

class StatementOut(BaseModel):
    id:             int
    account_name:   Optional[str]
    year:           int
    month:          int
    fecha_estado:   Optional[str]
    saldo_apertura: Optional[Decimal]
    saldo_cierre:   Optional[Decimal]
    saldo_promedio: Optional[Decimal]
    filename:       Optional[str]
    uploaded_at:    datetime
    transaction_count: int = 0

    model_config = {"from_attributes": True}

class StatementDetail(StatementOut):
    transactions: list[TransactionOut] = []


# ── Analytics ────────────────────────────────────────────────────────────────

class BalancePoint(BaseModel):
    year:          int
    month:         int
    month_label:   str
    saldo_apertura: Optional[float]
    saldo_cierre:  Optional[float]
    saldo_promedio: Optional[float]

class YearlyCreditAvg(BaseModel):
    year:         int
    avg_credito:  float
    total_credito: float
    count:        int

class CategoryBreakdown(BaseModel):
    category:      str
    color:         str
    total_debito:  float
    total_credito: float

class AvgVsClosing(BaseModel):
    year:          int
    month:         int
    month_label:   str
    saldo_promedio: Optional[float]
    saldo_cierre:  Optional[float]

class HeatmapPoint(BaseModel):
    day_of_week: int
    category:    str
    total:       float

class ProjectionPoint(BaseModel):
    day:       int
    balance:   float
    is_actual: bool

class ProjectionResult(BaseModel):
    year:              int
    month:             int
    projected_closing: float
    days_remaining:    int
    daily_rate:        float
    data:              list[ProjectionPoint]
