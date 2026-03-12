from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Category, ReferenceCatalog
from schemas import CategoryCreate, CategoryUpdate, CategoryOut, ReferenceOut, ReferenceAssign

router = APIRouter()


@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    if db.query(Category).filter(Category.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")
    cat = Category(name=payload.name, color=payload.color)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if payload.name is not None:
        cat.name = payload.name
    if payload.color is not None:
        cat.color = payload.color
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db.delete(cat)
    db.commit()


# ── References ────────────────────────────────────────────────────────────────

@router.get("/references", response_model=list[ReferenceOut])
def list_references(
    unclassified_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(ReferenceCatalog)
    if unclassified_only:
        q = q.filter(ReferenceCatalog.category_id.is_(None))
    return q.order_by(ReferenceCatalog.descripcion).all()


@router.put("/references/{reference_id}", response_model=ReferenceOut)
def assign_reference_category(
    reference_id: int,
    payload: ReferenceAssign,
    db: Session = Depends(get_db),
):
    ref = db.query(ReferenceCatalog).filter(ReferenceCatalog.id == reference_id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Referencia no encontrada")
    ref.category_id = payload.category_id
    db.commit()
    db.refresh(ref)
    return ref
