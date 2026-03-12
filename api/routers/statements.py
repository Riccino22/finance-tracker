from __future__ import annotations
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from models import Statement, Transaction, ReferenceCatalog
from pdf_parser import parse_statement
from excel_parser import parse_excel_statement
from schemas import StatementOut, StatementDetail, TransactionOut

_EXCEL_EXTS = {".xls", ".xlsx"}

router = APIRouter()


def _build_transaction_out(t: Transaction) -> dict:
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
        "created_at": t.created_at,
    }


@router.get("/", response_model=list[StatementOut])
def list_statements(db: Session = Depends(get_db)):
    stmts = db.query(Statement).order_by(Statement.year.desc(), Statement.month.desc()).all()
    result = []
    for s in stmts:
        d = StatementOut.model_validate(s)
        d.transaction_count = len(s.transactions)
        result.append(d)
    return result


@router.get("/{statement_id}", response_model=StatementDetail)
def get_statement(statement_id: int, db: Session = Depends(get_db)):
    s = db.query(Statement).filter(Statement.id == statement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Statement not found")
    d = StatementDetail.model_validate(s)
    d.transaction_count = len(s.transactions)
    d.transactions = [TransactionOut.model_validate(_build_transaction_out(t)) for t in s.transactions]
    return d


@router.post("/upload", status_code=201)
def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Sube un extracto PDF o Excel.

    - Si el mes/año no existe: lo crea e inserta todos los movimientos.
    - Si ya existe: actualiza el saldo de cierre e inserta solo los movimientos
      nuevos (detectados por su posición en el archivo).  Así se puede subir el
      mismo mes varias veces durante el mes y hacer updates incrementales.

    La deduplicación usa (statement_id, position) como clave única, donde
    position es el índice 0-based del movimiento en el archivo fuente.
    """
    fname = file.filename.lower()
    ext   = "." + fname.rsplit(".", 1)[-1] if "." in fname else ""

    if ext not in {".pdf"} | _EXCEL_EXTS:
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF o Excel (.xls, .xlsx)")

    raw_bytes = file.file.read()
    try:
        if ext == ".pdf":
            parsed = parse_statement(raw_bytes)
        else:
            parsed = parse_excel_statement(raw_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error al parsear el archivo: {e}")

    year  = parsed["year"]
    month = parsed["month"]

    if not year or not month:
        raise HTTPException(status_code=422, detail="No se pudo determinar el mes/año del extracto.")

    # ── Upsert statement ──────────────────────────────────────────────────────
    stmt = db.query(Statement).filter_by(year=year, month=month).first()
    is_new = stmt is None

    if is_new:
        stmt = Statement(
            account_name   = parsed["cuenta"],
            year           = year,
            month          = month,
            fecha_estado   = parsed["fecha_estado"],
            saldo_apertura = parsed["saldo_apertura"],
            saldo_cierre   = parsed["saldo_cierre"],
            saldo_promedio = parsed["saldo_promedio"],
            filename       = file.filename,
        )
        db.add(stmt)
        db.flush()
    else:
        # Actualizar saldo de cierre y promedio con los datos más recientes
        stmt.saldo_cierre   = parsed["saldo_cierre"]
        stmt.fecha_estado   = parsed["fecha_estado"]
        stmt.filename       = file.filename
        if parsed["saldo_promedio"] is not None:
            stmt.saldo_promedio = parsed["saldo_promedio"]
        db.flush()

    # ── Posiciones ya guardadas para este statement ───────────────────────────
    existing_positions: set[int] = {
        row.position
        for row in db.query(Transaction.position)
                      .filter(Transaction.statement_id == stmt.id)
                      .all()
    }

    # ── Insertar solo movimientos nuevos (por posición) ───────────────────────
    inserted = 0
    skipped  = 0

    for position, mov in enumerate(parsed["movimientos"]):
        if position in existing_positions:
            skipped += 1
            continue

        descripcion = mov["descripcion"]
        ref = db.query(ReferenceCatalog).filter_by(descripcion=descripcion).first()
        if not ref:
            ref = ReferenceCatalog(descripcion=descripcion)
            db.add(ref)
            db.flush()

        fecha_completa = None
        if mov["fecha_completa"]:
            fecha_completa = date.fromisoformat(mov["fecha_completa"])

        tx = Transaction(
            statement_id   = stmt.id,
            position       = position,
            fecha          = mov["fecha"],
            fecha_completa = fecha_completa,
            tipo           = mov["tipo"],
            descripcion    = descripcion,
            reference_id   = ref.id,
            debito         = mov["debito"],
            credito        = mov["credito"],
            saldo          = mov["saldo"],
        )
        db.add(tx)
        inserted += 1

    db.commit()
    db.refresh(stmt)

    label = _month_label(year, month)
    if is_new:
        message = f"Extracto {label} importado — {inserted} movimientos guardados."
    elif inserted > 0:
        message = f"Extracto {label} actualizado — {inserted} nuevos, {skipped} ya existían."
    else:
        message = f"Extracto {label} ya estaba al día — ningún movimiento nuevo."

    return {
        "id":              stmt.id,
        "message":         message,
        "is_new":          is_new,
        "year":            year,
        "month":           month,
        "inserted":        inserted,
        "skipped":         skipped,
        "total_en_archivo": len(parsed["movimientos"]),
        "saldo_apertura":  parsed["saldo_apertura"],
        "saldo_cierre":    parsed["saldo_cierre"],
    }


@router.delete("/{statement_id}", status_code=204)
def delete_statement(statement_id: int, db: Session = Depends(get_db)):
    s = db.query(Statement).filter(Statement.id == statement_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Statement not found")
    db.delete(s)
    db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

MONTH_NAMES = [
    "", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Set", "Oct", "Nov", "Dic",
]

def _month_label(year: int, month: int) -> str:
    return f"{MONTH_NAMES[month]} {year}"
