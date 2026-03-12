"""
PDF parser for Itaú Uruguay bank statements.
Adapted from pruebas/prueba.py to work as a reusable module.
"""
from __future__ import annotations
import re
from datetime import date
from typing import Optional

import fitz  # PyMuPDF


MESES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AGO": 8,
    "SET": 9, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}

MARCADORES_INICIO = {"SDO.APERTURA", "TRANSPORTE"}
MARCADORES_FIN    = {"SDO. CIERRE", "No paga intereses.", "SALDO PROMEDIO:", "Total de Reduccion"}
TIPOS_CREDITO     = {"REDIVA", "CRE. CAMBIOS", "CRED.DIRECTO", "CRE.CAMBIOS", "DEVOLUCION"}

RUIDO_RE = [
    r"^AG\. CIUDAD VIEJA$", r"^Zabala", r"^MONTEVIDEO$", r"^ÑI/",
    r"^SR\. ", r"^TREINTA Y TRES", r"^\d{5}$", r"^URUGUAY$",
    r"^\d{7}$", r"^URGP$", r"^US\.D$", r"^\d{2}FEB\d{4}$",
    r"^[A-Z0-9]{5,8}c$", r"^\d+/ \d+$",
    r"^A PARTIR", r"^EL PRECIO", r"^ACTUALIZ", r"^POR MAS",
    r"^DE TARIFAS", r"^WWW\.ITAU", r"^N$", r"^1L$", r"^\d{2}/ \d+ - S$",
    r"^Los movimientos", r"^00$", r"^\d{11}$",
    r"^CANTIDAD", r"^POR CAJA", r"^64951",
]


def _parse_monto(s: str) -> float:
    return float(s.strip().replace(".", "").replace(",", "."))


def _es_fecha(s: str) -> bool:
    return bool(re.match(r"^\d{2}[A-Z]{3}$", s.strip()))


def _es_monto(s: str) -> bool:
    return bool(re.match(r"^[\d.,]+$", s.strip()))


def _es_credito(tipo: str) -> bool:
    return any(tipo.strip().upper().startswith(t) for t in TIPOS_CREDITO)


def _es_ruido(s: str) -> bool:
    return any(re.match(p, s) for p in RUIDO_RE)


def _to_full_date(fecha: str, year: int) -> Optional[date]:
    """Convert 'DDMMM' (e.g. '02FEB') to a date object."""
    m = re.match(r"^(\d{2})([A-Z]{3})$", fecha.strip())
    if not m:
        return None
    day = int(m.group(1))
    month = MESES.get(m.group(2))
    if not month:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_account_name(all_lines: list[str]) -> Optional[str]:
    """Try to find the account holder name (line after 'SR.' prefix)."""
    for line in all_lines:
        m = re.match(r"^SRA?\.\s+(.+)$", line.strip())
        if m:
            return m.group(1).strip()
    return None


def _extract_fecha_estado(all_lines: list[str]) -> Optional[str]:
    """Find the statement date like '27FEB2026'."""
    for line in all_lines:
        m = re.match(r"^(\d{2}[A-Z]{3}\d{4})$", line.strip())
        if m:
            return m.group(1)
    return None


def _extract_saldo_promedio(lineas: list[str]) -> Optional[float]:
    """Extract 'SALDO PROMEDIO' from filtered lines."""
    for i, line in enumerate(lineas):
        if line.startswith("SALDO PROMEDIO:"):
            remainder = line[len("SALDO PROMEDIO:"):].strip()
            if remainder and _es_monto(remainder):
                return _parse_monto(remainder)
            for j in range(i + 1, min(i + 5, len(lineas))):
                if _es_monto(lineas[j]):
                    return _parse_monto(lineas[j])
    return None


def parse_statement(pdf_bytes: bytes) -> dict:
    """
    Parse an Itaú Uruguay bank statement PDF.

    Returns a dict with:
      - cuenta: str
      - fecha_estado: str  (e.g. '27FEB2026')
      - year: int
      - month: int
      - saldo_apertura: float | None
      - saldo_cierre: float | None
      - saldo_promedio: float | None
      - total_movimientos: int
      - movimientos: list[dict]  each has fecha, fecha_completa, tipo, descripcion, debito, credito, saldo
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    raw = ""
    for page in doc:
        raw += page.get_text()
    doc.close()

    texto = raw.replace(r"\n", "\n")

    # ── Extract metadata before noise filtering ──────────────────────────────
    all_lines = [l.strip() for l in texto.split("\n") if l.strip()]
    cuenta      = _extract_account_name(all_lines)
    fecha_estado = _extract_fecha_estado(all_lines)

    # Parse year/month from fecha_estado
    year = month = None
    if fecha_estado:
        m = re.match(r"^\d{2}([A-Z]{3})(\d{4})$", fecha_estado)
        if m:
            month = MESES.get(m.group(1))
            year  = int(m.group(2))
    if not year:
        year = 2026
    if not month:
        month = 1

    # ── Filter noise ─────────────────────────────────────────────────────────
    lineas = [
        l.strip() for l in texto.split("\n")
        if l.strip() and l.strip() != " " and not _es_ruido(l.strip())
    ]

    saldo_promedio = _extract_saldo_promedio(lineas)

    # ── Saldo apertura ────────────────────────────────────────────────────────
    saldo_apertura = None
    idx_inicio = 0
    for i, l in enumerate(lineas):
        if l in MARCADORES_INICIO:
            for j in range(i + 1, min(i + 6, len(lineas))):
                if _es_monto(lineas[j]):
                    saldo_apertura = _parse_monto(lineas[j])
                    idx_inicio = j + 1
                    break
            break

    # ── Parse transactions ────────────────────────────────────────────────────
    movimientos = []
    i = idx_inicio
    while i < len(lineas):
        l = lineas[i]

        # Skip page-break marker
        if l in MARCADORES_INICIO:
            i += 1
            while i < len(lineas) and _es_monto(lineas[i]):
                i += 1
            continue

        # End of section
        if any(l.startswith(m) for m in MARCADORES_FIN):
            hay_mas = any(lineas[j] == "TRANSPORTE" for j in range(i, min(i + 10, len(lineas))))
            if not hay_mas:
                break
            else:
                i += 1
                continue

        if not _es_fecha(l):
            i += 1
            continue

        fecha = l; i += 1
        if i >= len(lineas):
            break
        tipo = lineas[i].strip(); i += 1
        if i >= len(lineas):
            break
        descripcion = lineas[i].strip(); i += 1

        montos: list[str] = []
        while i < len(lineas) \
                and not _es_fecha(lineas[i]) \
                and lineas[i] not in MARCADORES_INICIO \
                and not any(lineas[i].startswith(m) for m in MARCADORES_FIN):
            if _es_monto(lineas[i]):
                montos.append(lineas[i].strip())
            i += 1

        debito = credito = saldo = None
        if len(montos) == 1:
            saldo = _parse_monto(montos[0])
        elif len(montos) >= 2:
            saldo      = _parse_monto(montos[-1])
            monto_op   = _parse_monto(montos[0])
            if _es_credito(tipo):
                credito = monto_op
            else:
                debito  = monto_op

        fecha_completa = _to_full_date(fecha, year)

        movimientos.append({
            "fecha":          fecha,
            "fecha_completa": fecha_completa.isoformat() if fecha_completa else None,
            "tipo":           tipo,
            "descripcion":    descripcion,
            "debito":         debito,
            "credito":        credito,
            "saldo":          saldo,
        })

    saldo_cierre = movimientos[-1]["saldo"] if movimientos else None

    return {
        "cuenta":           cuenta or "CUENTA ITAÚ",
        "fecha_estado":     fecha_estado or "",
        "year":             year,
        "month":            month,
        "saldo_apertura":   saldo_apertura,
        "saldo_cierre":     saldo_cierre,
        "saldo_promedio":   saldo_promedio,
        "total_movimientos": len(movimientos),
        "movimientos":      movimientos,
    }
