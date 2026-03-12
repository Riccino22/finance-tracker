"""
Prueba de parsing del Excel de Itaú Uruguay.
Formato: estado de cuenta .xls con header en fila 7 (índice 6).
"""
import re
import json
from datetime import date
import pandas as pd

ARCHIVO = "pruebas/Estado_De_Cuenta_3167882 (1).xls"

# ── Mapas de meses ────────────────────────────────────────────────────────────
MESES_INV = {
    1: "ENE", 2: "FEB",  3: "MAR", 4: "ABR",
    5: "MAY", 6: "JUN",  7: "JUL", 8: "AGO",
    9: "SET", 10: "OCT", 11: "NOV", 12: "DIC",
}

# ── Tipos conocidos (regex para separar tipo de descripción en Concepto) ──────
# Orden importa: los más específicos primero
TIPO_PATTERNS = [
    r"^(REDIVA\s+\d+)\s*(.+)$",       # REDIVA 17934BURGER KING
    r"^(DEB\.\s*CAMBIOS)\s*(.+)$",    # DEB. CAMBIOSTOLD...
    r"^(CRE\.\s*CAMBIOS)\s*(.+)$",    # CRE. CAMBIOS...
    r"^(CRED\.DIRECTO)\s*(.+)$",      # CRED.DIRECTOARNALDO...
    r"^(TRASPASO\s+A)\s+(.+)$",       # TRASPASO A 2982535...
    r"^(TRASPASO\s+DE)\s*(.+)$",
    r"^(DEVOLUCION)\s*(.+)$",
    r"^(COMPRA)\s+(.+)$",             # COMPRA      BURGER KING
]


def split_concepto(concepto: str) -> tuple[str, str]:
    """Separa 'CRED.DIRECTOARNALDO C. C' en ('CRED.DIRECTO', 'ARNALDO C. C')."""
    s = concepto.strip()
    for pat in TIPO_PATTERNS:
        m = re.match(pat, s, re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    # Fallback: todo es tipo, sin descripción
    return s, ""


def parse_fecha(raw) -> tuple[str, str, int, int]:
    """
    Convierte '05/03/2026' en:
      fecha       → '05MAR'
      fecha_iso   → '2026-03-05'
      year        → 2026
      month       → 3
    """
    if pd.isna(raw):
        return "", "", 0, 0
    if hasattr(raw, "strftime"):          # ya es datetime de pandas
        d = raw.date() if hasattr(raw, "date") else raw
    else:
        d = date(*reversed([int(x) for x in str(raw).split("/")]))
    mes_abr = MESES_INV[d.month]
    return f"{d.day:02d}{mes_abr}", d.isoformat(), d.year, d.month


def parse_excel(path: str) -> dict:
    xl = pd.ExcelFile(path)
    raw = xl.parse(xl.sheet_names[0], header=None)

    # ── Metadatos de la cuenta (fila 4, 0-indexed) ────────────────────────────
    cuenta   = str(raw.iloc[4, 1]).strip() if not pd.isna(raw.iloc[4, 1]) else "CUENTA ITAÚ"
    moneda   = str(raw.iloc[4, 5]).strip() if not pd.isna(raw.iloc[4, 5]) else ""
    nro_cta  = str(raw.iloc[4, 6]).strip() if not pd.isna(raw.iloc[4, 6]) else ""

    # ── Parsear filas de transacciones (desde fila 7 en adelante) ─────────────
    # Columnas por posición (evita problemas de encoding con Débito/Crédito):
    #  1=Fecha  2=Concepto  4=Debito  5=Credito  6=Saldo  7=Referencia
    data_rows = raw.iloc[7:].copy()
    data_rows.columns = range(len(data_rows.columns))

    saldo_apertura = None
    saldo_cierre   = None
    year = month   = None
    movimientos    = []

    for _, row in data_rows.iterrows():
        concepto = str(row[2]).strip() if not pd.isna(row[2]) else ""
        if not concepto:
            continue

        if concepto == "SALDO ANTERIOR":
            saldo_apertura = float(row[6]) if not pd.isna(row[6]) else None
            _, _, year, month = parse_fecha(row[1])
            continue

        if concepto == "SALDO FINAL":
            saldo_cierre = float(row[6]) if not pd.isna(row[6]) else None
            continue

        tipo, descripcion = split_concepto(concepto)

        fecha_corta, fecha_iso, yr, mo = parse_fecha(row[1])
        if yr:
            year, month = yr, mo

        debito  = float(row[4]) if not pd.isna(row[4]) else None
        credito = float(row[5]) if not pd.isna(row[5]) else None
        saldo   = float(row[6]) if not pd.isna(row[6]) else None

        movimientos.append({
            "fecha":          fecha_corta,
            "fecha_completa": fecha_iso,
            "tipo":           tipo,
            "descripcion":    descripcion,
            "debito":         debito,
            "credito":        credito,
            "saldo":          saldo,
        })

    # fecha_estado: último día con movimientos
    fechas_validas = [m["fecha_completa"] for m in movimientos if m["fecha_completa"]]
    ultima_fecha   = max(fechas_validas) if fechas_validas else ""
    if ultima_fecha:
        d = date.fromisoformat(ultima_fecha)
        fecha_estado = f"{d.day:02d}{MESES_INV[d.month]}{d.year}"
    else:
        fecha_estado = ""

    return {
        "cuenta":            cuenta,
        "moneda":            moneda,
        "nro_cuenta":        nro_cta,
        "fecha_estado":      fecha_estado,
        "year":              year or 0,
        "month":             month or 0,
        "saldo_apertura":    saldo_apertura,
        "saldo_cierre":      saldo_cierre,
        "saldo_promedio":    None,   # el Excel no lo incluye
        "total_movimientos": len(movimientos),
        "movimientos":       movimientos,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    resultado = parse_excel(ARCHIVO)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
