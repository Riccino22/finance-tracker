from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Transaction, Statement, ReferenceCatalog
from schemas import TransactionOut, TransactionNotaUpdate

router = APIRouter()


def _tx_out(t: Transaction) -> dict:
    cat = None
    if t.reference and t.reference.category:
        c = t.reference.category
        cat = {"id": c.id, "name": c.name, "color": c.color, "created_at": c.created_at}
    return {
        "id": t.id,
        "statement_id": t.statement_id,
        "fecha": t.fecha,
        "fecha_completa": t.fecha_completa,
        "tipo": t.tipo,
        "descripcion": t.descripcion,
        "reference_id": t.reference_id,
        "category": cat,
        "debito": t.debito,
        "credito": t.credito,
        "saldo": t.saldo,
        "nota": t.nota,
        "created_at": t.created_at,
    }


@router.get("/", response_model=list[TransactionOut])
def list_transactions(
    year:        Optional[int] = Query(None),
    month:       Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    tipo:        Optional[str] = Query(None),
    search:      Optional[str] = Query(None),
    limit:       int           = Query(500, le=2000),
    offset:      int           = Query(0),
    db:          Session       = Depends(get_db),
):
    q = db.query(Transaction).join(Statement)

    if year:
        q = q.filter(Statement.year == year)
    if month:
        q = q.filter(Statement.month == month)
    if category_id is not None:
        q = q.join(ReferenceCatalog, Transaction.reference_id == ReferenceCatalog.id)
        q = q.filter(ReferenceCatalog.category_id == category_id)
    if tipo:
        q = q.filter(Transaction.tipo.ilike(f"%{tipo}%"))
    if search:
        q = q.filter(Transaction.descripcion.ilike(f"%{search}%"))

    txs = (
        q.order_by(Transaction.fecha_completa, Transaction.id)
         .offset(offset)
         .limit(limit)
         .all()
    )
    return [TransactionOut.model_validate(_tx_out(t)) for t in txs]


@router.patch("/{transaction_id}/nota", response_model=TransactionOut)
def update_nota(
    transaction_id: int,
    body: TransactionNotaUpdate,
    db: Session = Depends(get_db),
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx.nota = body.nota
    db.commit()
    db.refresh(tx)
    return TransactionOut.model_validate(_tx_out(tx))
