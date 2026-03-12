"""
Excel parser for Itaú Uruguay bank statements (.xls).
Mirrors the output format of pdf_parser.parse_statement().
"""
from __future__ import annotations
import re
from datetime import date
from typing import Optional

import pandas as pd

MESES_INV = {
    1: "ENE", 2: "FEB",  3: "MAR", 4: "ABR",
    5: "MAY", 6: "JUN",  7: "JUL", 8: "AGO",
    9: "SET", 10: "OCT", 11: "NOV", 12: "DIC",
}

# Orden importa: patrones más específicos primero
_TIPO_PATTERNS = [
    r"^(REDIVA\s+\d+)\s*(.+)$",
    r"^(DEB\.\s*CAMBIOS)\s*(.+)$",
    r"^(CRE\.\s*CAMBIOS)\s*(.+)$",
    r"^(CRED\.DIRECTO)\s*(.+)$",
    r"^(TRASPASO\s+A)\s+(.+)$",
    r"^(TRASPASO\s+DE)\s*(.+)$",
    r"^(DEVOLUCION)\s*(.+)$",
    r"^(COMPRA)\s+(.+)$",
]


def _split_concepto(concepto: str) -> tuple[str, str]:
    for pat in _TIPO_PATTERNS:
        m = re.match(pat, concepto.strip(), re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return concepto.strip(), ""


def _parse_fecha(raw) -> tuple[Optional[str], Optional[str], Optional[int], Optional[int]]:
    """Returns (fecha_corta, fecha_iso, year, month) or (None,)*4 on failure."""
    if raw is None or (hasattr(raw, "__class__") and raw.__class__.__name__ == "float"):
        return None, None, None, None
    try:
        import pandas as pd
        if pd.isna(raw):
            return None, None, None, None
    except (TypeError, ValueError):
        pass
    try:
        if hasattr(raw, "year"):          # pandas Timestamp / datetime
            d = raw.date() if hasattr(raw, "date") else raw
        else:
            parts = str(raw).split("/")
            d = date(int(parts[2]), int(parts[1]), int(parts[0]))
        mes_abr = MESES_INV[d.month]
        return f"{d.day:02d}{mes_abr}", d.isoformat(), d.year, d.month
    except Exception:
        return None, None, None, None


def _float_or_none(val) -> Optional[float]:
    try:
        import pandas as pd
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def parse_excel_statement(file_bytes: bytes, filename: str = "") -> dict:
    """
    Parse an Itaú Uruguay bank statement Excel file (.xls / .xlsx).
    Returns the same structure as pdf_parser.parse_statement().
    """
    import io
    buf = io.BytesIO(file_bytes)

    try:
        xl = pd.ExcelFile(buf)
    except Exception as e:
        raise ValueError(f"No se pudo abrir el archivo Excel: {e}")

    raw = xl.parse(xl.sheet_names[0], header=None)

    if raw.shape[0] < 8 or raw.shape[1] < 7:
        raise ValueError("El Excel no tiene el formato esperado de estado de cuenta Itaú.")

    # ── Metadatos de la cuenta (fila 4) ──────────────────────────────────────
    def cell(r, c, default=""):
        try:
            v = raw.iloc[r, c]
            return "" if pd.isna(v) else str(v).strip()
        except Exception:
            return default

    cuenta = cell(4, 1) or "CUENTA ITAÚ"

    # ── Filas de transacciones (desde fila 7 en adelante) ────────────────────
    saldo_apertura: Optional[float] = None
    saldo_cierre:   Optional[float] = None
    year = month = None
    movimientos: list[dict] = []

    for idx in range(7, len(raw)):
        row = raw.iloc[idx]

        concepto = "" if pd.isna(row.iloc[2]) else str(row.iloc[2]).strip()
        if not concepto:
            continue

        if concepto == "SALDO ANTERIOR":
            saldo_apertura = _float_or_none(row.iloc[6])
            _, _, yr, mo = _parse_fecha(row.iloc[1])
            if yr:
                year, month = yr, mo
            continue

        if concepto == "SALDO FINAL":
            saldo_cierre = _float_or_none(row.iloc[6])
            continue

        tipo, descripcion = _split_concepto(concepto)
        fecha_corta, fecha_iso, yr, mo = _parse_fecha(row.iloc[1])
        if yr:
            year, month = yr, mo

        movimientos.append({
            "fecha":          fecha_corta or "",
            "fecha_completa": fecha_iso,
            "tipo":           tipo,
            "descripcion":    descripcion,
            "debito":         _float_or_none(row.iloc[4]),
            "credito":        _float_or_none(row.iloc[5]),
            "saldo":          _float_or_none(row.iloc[6]),
        })

    # fecha_estado: último día con fecha válida
    fechas = [m["fecha_completa"] for m in movimientos if m["fecha_completa"]]
    if fechas:
        d = date.fromisoformat(max(fechas))
        fecha_estado = f"{d.day:02d}{MESES_INV[d.month]}{d.year}"
    else:
        fecha_estado = ""

    return {
        "cuenta":            cuenta,
        "fecha_estado":      fecha_estado,
        "year":              year or 0,
        "month":             month or 0,
        "saldo_apertura":    saldo_apertura,
        "saldo_cierre":      saldo_cierre,
        "saldo_promedio":    None,
        "total_movimientos": len(movimientos),
        "movimientos":       movimientos,
    }
