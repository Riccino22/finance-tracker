from __future__ import annotations
from calendar import monthrange
from datetime import date
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    BalancePoint, YearlyCreditAvg, CategoryBreakdown,
    AvgVsClosing, HeatmapPoint, ProjectionResult, ProjectionPoint,
)

router = APIRouter()

MONTH_NAMES = [
    "", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Set", "Oct", "Nov", "Dic",
]


@router.get("/balance-evolution", response_model=list[BalancePoint])
def balance_evolution(db: Session = Depends(get_db)):
    """Saldo apertura / cierre por mes a lo largo del tiempo."""
    rows = db.execute(text("""
        SELECT year, month, saldo_apertura, saldo_cierre, saldo_promedio
        FROM statements
        ORDER BY year, month
    """)).fetchall()

    return [
        BalancePoint(
            year=r.year,
            month=r.month,
            month_label=f"{MONTH_NAMES[r.month]} {r.year}",
            saldo_apertura=float(r.saldo_apertura) if r.saldo_apertura else None,
            saldo_cierre=float(r.saldo_cierre)     if r.saldo_cierre   else None,
            saldo_promedio=float(r.saldo_promedio) if r.saldo_promedio else None,
        )
        for r in rows
    ]


@router.get("/yearly-credits-avg", response_model=list[YearlyCreditAvg])
def yearly_credits_avg(db: Session = Depends(get_db)):
    """Promedio de créditos agrupado por año."""
    rows = db.execute(text("""
        SELECT
            EXTRACT(YEAR FROM fecha_completa)::int AS year,
            AVG(credito)    AS avg_credito,
            SUM(credito)    AS total_credito,
            COUNT(*)        AS cnt
        FROM transactions
        WHERE credito > 0
          AND fecha_completa IS NOT NULL
        GROUP BY year
        ORDER BY year
    """)).fetchall()

    return [
        YearlyCreditAvg(
            year=r.year,
            avg_credito=float(r.avg_credito),
            total_credito=float(r.total_credito),
            count=r.cnt,
        )
        for r in rows
    ]


@router.get("/category-breakdown", response_model=list[CategoryBreakdown])
def category_breakdown(
    year:  Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db:    Session       = Depends(get_db),
):
    """Débitos y créditos totales por categoría."""
    where_clauses = ["1=1"]
    params: dict = {}
    if year:
        where_clauses.append("EXTRACT(YEAR FROM t.fecha_completa) = :year")
        params["year"] = year
    if month:
        where_clauses.append("EXTRACT(MONTH FROM t.fecha_completa) = :month")
        params["month"] = month

    where = " AND ".join(where_clauses)

    rows = db.execute(text(f"""
        SELECT
            COALESCE(cat.name, 'Sin categoría') AS category,
            COALESCE(cat.color, '#94a3b8')      AS color,
            COALESCE(SUM(t.debito)  FILTER (WHERE t.debito  > 0), 0) AS total_debito,
            COALESCE(SUM(t.credito) FILTER (WHERE t.credito > 0), 0) AS total_credito
        FROM transactions t
        LEFT JOIN references_catalog r ON t.reference_id = r.id
        LEFT JOIN categories cat       ON r.category_id  = cat.id
        WHERE {where}
        GROUP BY cat.name, cat.color
        ORDER BY total_debito DESC
    """), params).fetchall()

    return [
        CategoryBreakdown(
            category=r.category,
            color=r.color,
            total_debito=float(r.total_debito),
            total_credito=float(r.total_credito),
        )
        for r in rows
    ]


@router.get("/avg-vs-closing", response_model=list[AvgVsClosing])
def avg_vs_closing(db: Session = Depends(get_db)):
    """Saldo promedio mensual vs saldo cierre por mes."""
    rows = db.execute(text("""
        SELECT year, month, saldo_promedio, saldo_cierre
        FROM statements
        ORDER BY year, month
    """)).fetchall()

    return [
        AvgVsClosing(
            year=r.year,
            month=r.month,
            month_label=f"{MONTH_NAMES[r.month]} {r.year}",
            saldo_promedio=float(r.saldo_promedio) if r.saldo_promedio else None,
            saldo_cierre=float(r.saldo_cierre)     if r.saldo_cierre   else None,
        )
        for r in rows
    ]


@router.get("/heatmap", response_model=list[HeatmapPoint])
def heatmap(
    year:  Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db:    Session       = Depends(get_db),
):
    """
    Gasto por día de semana × categoría.
    day_of_week: 0=Dom, 1=Lun, ..., 6=Sáb  (PostgreSQL convention)
    """
    where_clauses = ["t.debito > 0", "t.fecha_completa IS NOT NULL"]
    params: dict = {}
    if year:
        where_clauses.append("EXTRACT(YEAR FROM t.fecha_completa) = :year")
        params["year"] = year
    if month:
        where_clauses.append("EXTRACT(MONTH FROM t.fecha_completa) = :month")
        params["month"] = month

    where = " AND ".join(where_clauses)

    rows = db.execute(text(f"""
        SELECT
            EXTRACT(DOW FROM t.fecha_completa)::int  AS day_of_week,
            COALESCE(cat.name, 'Sin categoría')      AS category,
            SUM(t.debito)                            AS total
        FROM transactions t
        LEFT JOIN references_catalog r ON t.reference_id = r.id
        LEFT JOIN categories cat       ON r.category_id  = cat.id
        WHERE {where}
        GROUP BY day_of_week, category
        ORDER BY day_of_week, category
    """), params).fetchall()

    return [
        HeatmapPoint(day_of_week=r.day_of_week, category=r.category, total=float(r.total))
        for r in rows
    ]


@router.get("/projection", response_model=ProjectionResult)
def projection(
    year:  Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    db:    Session       = Depends(get_db),
):
    """Proyección lineal del saldo para el resto del mes."""
    if not year or not month:
        today = date.today()
        year  = today.year
        month = today.month

    rows = db.execute(text("""
        SELECT DISTINCT ON (t.fecha_completa)
            EXTRACT(DAY FROM t.fecha_completa)::int AS day,
            t.saldo
        FROM transactions t
        JOIN statements s ON t.statement_id = s.id
        WHERE s.year  = :year
          AND s.month = :month
          AND t.fecha_completa IS NOT NULL
          AND t.saldo IS NOT NULL
        ORDER BY t.fecha_completa, t.id DESC
    """), {"year": year, "month": month}).fetchall()

    if not rows:
        return ProjectionResult(
            year=year, month=month,
            projected_closing=0, days_remaining=0, daily_rate=0, data=[],
        )

    days     = [r.day for r in rows]
    balances = [float(r.saldo) for r in rows]
    days_in_month = monthrange(year, month)[1]

    actual_points = [
        ProjectionPoint(day=d, balance=b, is_actual=True)
        for d, b in zip(days, balances)
    ]

    if len(days) >= 2:
        coeffs    = np.polyfit(days, balances, 1)
        m_rate, b = float(coeffs[0]), float(coeffs[1])
        last_day  = max(days)
        proj_days = list(range(last_day + 1, days_in_month + 1))
        proj_pts  = [
            ProjectionPoint(day=d, balance=float(m_rate * d + b), is_actual=False)
            for d in proj_days
        ]
        projected_closing = float(m_rate * days_in_month + b)
        days_remaining    = days_in_month - last_day
    else:
        m_rate            = 0.0
        proj_pts          = []
        projected_closing = balances[-1] if balances else 0.0
        days_remaining    = days_in_month - (days[-1] if days else 0)

    return ProjectionResult(
        year=year,
        month=month,
        projected_closing=projected_closing,
        days_remaining=days_remaining,
        daily_rate=m_rate,
        data=actual_points + proj_pts,
    )
