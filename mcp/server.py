"""
MCP Server – Banco Dashboard
Permite consultas conversacionales sobre movimientos bancarios.

Transports:
  - SSE (HTTP) cuando MCP_TRANSPORT=sse  (por defecto, para Docker)
  - stdio cuando MCP_TRANSPORT=stdio    (para Claude Desktop local)

Conexión desde Claude Desktop (SSE):
  Agrega en ~/.config/claude/claude_desktop_config.json:
  {
    "mcpServers": {
      "banco-dashboard": {
        "transport": "sse",
        "url": "http://localhost:8002/sse"
      }
    }
  }
"""
from __future__ import annotations
import os
import json
from datetime import date
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ── Configuration ─────────────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:8000")
MCP_PORT = int(os.getenv("MCP_PORT", "8002"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

MONTH_NAMES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

mcp = FastMCP("banco-dashboard", instructions="""
Sos un asistente financiero personal que analiza los movimientos bancarios.
Tenés acceso a datos reales de la cuenta: movimientos, saldos, categorías y tendencias.

Cuando el usuario hace preguntas ambiguas como "¿cómo estoy este mes?", primero clarificá:
- ¿Comparado con qué? ¿El mes anterior, el mismo mes del año pasado, o el promedio anual?

Usá las tools disponibles para obtener datos actualizados antes de responder.
Mostrá los montos en formato $ X.XXX,XX (formato uruguayo).
""")


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _get(path: str, params: dict | None = None) -> dict | list:
    try:
        r = httpx.get(f"{API_URL}{path}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        return {"error": "No se puede conectar con la API"}
    except httpx.HTTPStatusError as e:
        return {"error": f"API error {e.response.status_code}: {e.response.text}"}


def _fmt(n: float | None) -> str:
    if n is None:
        return "—"
    return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _current_period():
    today = date.today()
    return today.year, today.month


# ── Resources ─────────────────────────────────────────────────────────────────

@mcp.resource("banking://months")
def available_months() -> str:
    """Lista de meses disponibles en la base de datos."""
    stmts = _get("/statements/")
    if isinstance(stmts, dict) and "error" in stmts:
        return f"Error: {stmts['error']}"
    if not stmts:
        return "No hay extractos cargados todavía."
    lines = ["Extractos disponibles:"]
    for s in stmts:
        m = s["month"]
        y = s["year"]
        lines.append(
            f"  • {MONTH_NAMES[m]} {y} — "
            f"Apertura: {_fmt(s.get('saldo_apertura'))} · "
            f"Cierre: {_fmt(s.get('saldo_cierre'))} · "
            f"{s.get('transaction_count', 0)} movimientos"
        )
    return "\n".join(lines)


@mcp.resource("banking://categories")
def available_categories() -> str:
    """Lista de categorías configuradas."""
    cats = _get("/categories/")
    if isinstance(cats, dict) and "error" in cats:
        return f"Error: {cats['error']}"
    if not cats:
        return "No hay categorías configuradas."
    return "Categorías:\n" + "\n".join(f"  • {c['name']} ({c['id']})" for c in cats)


@mcp.resource("banking://summary/current")
def current_month_summary() -> str:
    """Resumen del mes actual."""
    year, month = _current_period()
    return _build_monthly_summary(year, month)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_monthly_summary(year: int, month: int) -> str:
    """
    Obtiene el resumen completo de un mes específico: saldos, totales de débitos
    y créditos, y los 5 mayores gastos.

    Args:
        year:  Año (ej: 2026)
        month: Mes como número (1=Ene, 2=Feb, ..., 12=Dic)
    """
    return _build_monthly_summary(year, month)


def _build_monthly_summary(year: int, month: int) -> str:
    stmts = _get("/statements/")
    if isinstance(stmts, dict) and "error" in stmts:
        return f"Error: {stmts['error']}"

    stmt = next((s for s in stmts if s["year"] == year and s["month"] == month), None)
    if not stmt:
        return f"No hay extracto para {MONTH_NAMES[month]} {year}."

    txs = _get("/transactions/", {"year": year, "month": month, "limit": 2000})
    if isinstance(txs, dict) and "error" in txs:
        return f"Error al cargar movimientos: {txs['error']}"

    total_deb = sum(float(t.get("debito") or 0) for t in txs)
    total_cre = sum(float(t.get("credito") or 0) for t in txs)

    # Top 5 debits
    debits = sorted(
        [t for t in txs if float(t.get("debito") or 0) > 0],
        key=lambda t: float(t.get("debito") or 0),
        reverse=True,
    )[:5]

    lines = [
        f"📅 **{MONTH_NAMES[month]} {year}**",
        f"Saldo apertura:  {_fmt(stmt.get('saldo_apertura'))}",
        f"Saldo cierre:    {_fmt(stmt.get('saldo_cierre'))}",
        f"Saldo promedio:  {_fmt(stmt.get('saldo_promedio'))}",
        f"Total débitos:   {_fmt(total_deb)}  ({sum(1 for t in txs if float(t.get('debito') or 0) > 0)} movs)",
        f"Total créditos:  {_fmt(total_cre)}  ({sum(1 for t in txs if float(t.get('credito') or 0) > 0)} movs)",
        "",
        "Top 5 mayores gastos:",
    ]
    for t in debits:
        cat = t.get("category")
        cat_name = cat["name"] if cat else "Sin categoría"
        nota = t.get("nota") or ""
        nota_str = f"  📝 {nota}" if nota else ""
        lines.append(f"  • {t.get('descripcion', '—')} — {_fmt(float(t.get('debito') or 0))} [{cat_name}]{nota_str}")

    return "\n".join(lines)


@mcp.tool()
def compare_periods(
    year1: int,
    month1: int,
    year2: int,
    month2: int,
) -> str:
    """
    Compara dos meses: diferencias en saldos, débitos y créditos.

    Args:
        year1, month1: Primer período
        year2, month2: Segundo período
    """
    stmts = _get("/statements/")
    if isinstance(stmts, dict) and "error" in stmts:
        return f"Error: {stmts['error']}"

    s1 = next((s for s in stmts if s["year"] == year1 and s["month"] == month1), None)
    s2 = next((s for s in stmts if s["year"] == year2 and s["month"] == month2), None)

    if not s1:
        return f"No hay datos para {MONTH_NAMES[month1]} {year1}."
    if not s2:
        return f"No hay datos para {MONTH_NAMES[month2]} {year2}."

    txs1 = _get("/transactions/", {"year": year1, "month": month1, "limit": 2000})
    txs2 = _get("/transactions/", {"year": year2, "month": month2, "limit": 2000})

    deb1 = sum(float(t.get("debito") or 0) for t in txs1)
    deb2 = sum(float(t.get("debito") or 0) for t in txs2)
    cre1 = sum(float(t.get("credito") or 0) for t in txs1)
    cre2 = sum(float(t.get("credito") or 0) for t in txs2)

    def diff(a, b):
        if a and b:
            pct = ((b - a) / a) * 100
            sign = "+" if pct >= 0 else ""
            return f"{sign}{pct:.1f}%"
        return "—"

    p1 = f"{MONTH_NAMES[month1]} {year1}"
    p2 = f"{MONTH_NAMES[month2]} {year2}"

    lines = [
        f"📊 Comparación: **{p1}** vs **{p2}**",
        "",
        f"{'':20} {p1:>18} {p2:>18} {'Δ':>10}",
        f"{'─' * 68}",
        f"{'Saldo apertura':20} {_fmt(s1.get('saldo_apertura')):>18} {_fmt(s2.get('saldo_apertura')):>18} {diff(s1.get('saldo_apertura'), s2.get('saldo_apertura')):>10}",
        f"{'Saldo cierre':20} {_fmt(s1.get('saldo_cierre')):>18} {_fmt(s2.get('saldo_cierre')):>18} {diff(s1.get('saldo_cierre'), s2.get('saldo_cierre')):>10}",
        f"{'Total débitos':20} {_fmt(deb1):>18} {_fmt(deb2):>18} {diff(deb1, deb2):>10}",
        f"{'Total créditos':20} {_fmt(cre1):>18} {_fmt(cre2):>18} {diff(cre1, cre2):>10}",
    ]
    return "\n".join(lines)


@mcp.tool()
def get_top_merchants(
    year: Optional[int] = None,
    month: Optional[int] = None,
    top_n: int = 10,
) -> str:
    """
    Muestra los comercios/referencias donde más gastaste.

    Args:
        year:   Año (opcional, filtra si se especifica)
        month:  Mes (opcional)
        top_n:  Cuántos resultados mostrar (default: 10)
    """
    params: dict = {"limit": 2000}
    if year:  params["year"]  = year
    if month: params["month"] = month

    txs = _get("/transactions/", params)
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"

    # Group by description
    from collections import defaultdict
    totals: dict[str, float] = defaultdict(float)
    for t in txs:
        if float(t.get("debito") or 0) > 0:
            totals[t.get("descripcion", "—")] += float(t["debito"])

    if not totals:
        return "No hay débitos para el período seleccionado."

    sorted_merchants = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:top_n]
    period_label = f"{MONTH_NAMES[month]} {year}" if month and year else (str(year) if year else "todos los meses")

    lines = [f"🛒 **Top {top_n} comercios – {period_label}**", ""]
    for i, (desc, total) in enumerate(sorted_merchants, 1):
        lines.append(f"  {i:2}. {desc:<30} {_fmt(total):>16}")

    return "\n".join(lines)


@mcp.tool()
def get_category_spending(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """
    Muestra el gasto total y porcentaje por categoría.

    Args:
        year:  Año (opcional)
        month: Mes (opcional)
    """
    params: dict = {}
    if year:  params["year"]  = year
    if month: params["month"] = month

    breakdown = _get("/analytics/category-breakdown", params)
    if isinstance(breakdown, dict) and "error" in breakdown:
        return f"Error: {breakdown['error']}"
    if not breakdown:
        return "No hay datos de categorías para el período seleccionado."

    period_label = f"{MONTH_NAMES[month]} {year}" if month and year else (str(year) if year else "todos los meses")
    total_deb = sum(float(b.get("total_debito") or 0) for b in breakdown)

    lines = [f"🏷️ **Gastos por categoría – {period_label}**", ""]
    for b in breakdown:
        deb = float(b.get("total_debito") or 0)
        pct = (deb / total_deb * 100) if total_deb > 0 else 0
        bar = "█" * int(pct / 5)
        lines.append(f"  {b['category']:<20} {_fmt(deb):>16}  {pct:5.1f}% {bar}")

    lines += ["", f"  {'TOTAL':20} {_fmt(total_deb):>16}"]
    return "\n".join(lines)


@mcp.tool()
def get_balance_trend() -> str:
    """
    Muestra la evolución del saldo apertura y cierre mes a mes.
    """
    data = _get("/analytics/balance-evolution")
    if isinstance(data, dict) and "error" in data:
        return f"Error: {data['error']}"
    if not data:
        return "No hay datos de evolución de saldo."

    lines = ["📈 **Evolución del saldo**", ""]
    lines.append(f"{'Período':15} {'Apertura':>16} {'Cierre':>16} {'Variación':>12}")
    lines.append("─" * 62)
    for p in data:
        ap = p.get("saldo_apertura")
        ci = p.get("saldo_cierre")
        if ap and ci:
            var = float(ci) - float(ap)
            sign = "+" if var >= 0 else ""
            var_str = f"{sign}{_fmt(abs(var))}"
        else:
            var_str = "—"
        lines.append(
            f"{p['month_label']:15} {_fmt(ap):>16} {_fmt(ci):>16} {var_str:>12}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_projection_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """
    Proyecta el saldo al cierre del mes basado en tendencia lineal.

    Args:
        year:  Año (default: año actual)
        month: Mes (default: mes actual)
    """
    params: dict = {}
    if year:  params["year"]  = year
    if month: params["month"] = month

    proj = _get("/analytics/projection", params)
    if isinstance(proj, dict) and "error" in proj:
        return f"Error: {proj['error']}"
    if not proj.get("data"):
        return "No hay suficientes datos para proyectar el saldo."

    y = proj["year"]
    m = proj["month"]
    projected_closing = proj.get("projected_closing", 0)
    daily_rate        = proj.get("daily_rate", 0)
    days_remaining    = proj.get("days_remaining", 0)

    actual_points = [p for p in proj["data"] if p["is_actual"]]
    last_balance  = actual_points[-1]["balance"] if actual_points else 0

    sign = "+" if daily_rate >= 0 else ""
    trend_emoji = "📈" if daily_rate >= 0 else "📉"

    lines = [
        f"{trend_emoji} **Proyección – {MONTH_NAMES[m]} {y}**",
        "",
        f"Saldo actual:          {_fmt(last_balance)}",
        f"Saldo proyectado:      {_fmt(projected_closing)}",
        f"Variación diaria est.: {sign}{_fmt(daily_rate)}/día",
        f"Días restantes:        {days_remaining}",
        "",
    ]

    if daily_rate < 0:
        lines.append("⚠️ Al ritmo actual, el saldo seguirá bajando. Revisá tus gastos.")
    else:
        lines.append("✅ Al ritmo actual, el saldo se mantiene o sube.")

    return "\n".join(lines)


# ── Tools adicionales ─────────────────────────────────────────────────────────

@mcp.tool()
def get_categories() -> str:
    """
    Lista todas las categorías disponibles con su id y color.
    Útil antes de filtrar transacciones por categoría.
    """
    cats = _get("/categories/")
    if isinstance(cats, dict) and "error" in cats:
        return f"Error: {cats['error']}"
    if not cats:
        return "No hay categorías configuradas."
    lines = ["🏷️ **Categorías disponibles**", ""]
    for c in cats:
        lines.append(f"  id={c['id']:3}  {c['name']}")
    return "\n".join(lines)


@mcp.tool()
def search_transactions(
    search:      Optional[str] = None,
    year:        Optional[int] = None,
    month:       Optional[int] = None,
    tipo:        Optional[str] = None,
    category_id: Optional[int] = None,
    limit:       int = 30,
) -> str:
    """
    Busca transacciones con filtros combinables.

    Args:
        search:      Texto a buscar en la descripción (ej: "BURGER", "SUPERMERCADO")
        year:        Filtrar por año
        month:       Filtrar por mes (1-12)
        tipo:        Filtrar por tipo (ej: "COMPRA", "REDIVA", "DEB. CAMBIOS")
        category_id: Filtrar por id de categoría (usá get_categories para ver ids)
        limit:       Máximo de resultados (default 30, máx 200)
    """
    params: dict = {"limit": min(limit, 200)}
    if year:        params["year"]        = year
    if month:       params["month"]       = month
    if tipo:        params["tipo"]        = tipo
    if category_id: params["category_id"] = category_id
    if search:      params["search"]      = search

    txs = _get("/transactions/", params)
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"
    if not txs:
        return "No se encontraron transacciones con esos filtros."

    period = f"{MONTH_NAMES[month]} {year}" if month and year else (str(year) if year else "todo el historial")
    lines = [
        f"🔍 **Transacciones – {period}**"
        + (f" · búsqueda: '{search}'" if search else "")
        + (f" · tipo: {tipo}" if tipo else ""),
        f"   ({len(txs)} resultado{'s' if len(txs) != 1 else ''})",
        "",
        f"{'Fecha':<12} {'Tipo':<20} {'Descripción':<25} {'Débito':>12} {'Crédito':>12} {'Categoría':<18}",
        "─" * 102,
    ]
    total_deb = total_cre = 0.0
    for t in txs:
        cat   = (t.get("category") or {}).get("name", "—")
        deb   = float(t.get("debito")  or 0)
        cre   = float(t.get("credito") or 0)
        total_deb += deb
        total_cre += cre
        fecha = t.get("fecha_completa") or t.get("fecha", "")
        nota  = t.get("nota") or ""
        nota_str = f"  📝 {nota}" if nota else ""
        lines.append(
            f"{fecha:<12} {t.get('tipo',''):<20} {t.get('descripcion',''):<25} "
            f"{(_fmt(deb) if deb else '—'):>12} {(_fmt(cre) if cre else '—'):>12} {cat:<18}{nota_str}"
        )
    lines += [
        "─" * 102,
        f"{'TOTAL':>59} {_fmt(total_deb):>12} {_fmt(total_cre):>12}",
    ]
    return "\n".join(lines)


@mcp.tool()
def get_largest_transactions(
    year:        Optional[int] = None,
    month:       Optional[int] = None,
    top_n:       int = 10,
    tx_type:     str = "debito",
) -> str:
    """
    Muestra las N transacciones más grandes.

    Args:
        year:    Año (opcional)
        month:   Mes (opcional)
        top_n:   Cantidad de resultados (default 10)
        tx_type: "debito" para gastos, "credito" para ingresos
    """
    params: dict = {"limit": 2000}
    if year:  params["year"]  = year
    if month: params["month"] = month

    txs = _get("/transactions/", params)
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"

    field = "debito" if tx_type == "debito" else "credito"
    emoji = "💸" if field == "debito" else "💰"

    filtered = sorted(
        [t for t in txs if float(t.get(field) or 0) > 0],
        key=lambda t: float(t.get(field) or 0),
        reverse=True,
    )[:top_n]

    if not filtered:
        return f"No hay transacciones de tipo '{tx_type}' en el período."

    period = f"{MONTH_NAMES[month]} {year}" if month and year else (str(year) if year else "todo el historial")
    lines = [f"{emoji} **Top {top_n} {tx_type}s – {period}**", ""]
    for i, t in enumerate(filtered, 1):
        cat   = (t.get("category") or {}).get("name", "Sin categoría")
        monto = float(t.get(field) or 0)
        fecha = t.get("fecha_completa") or t.get("fecha", "")
        nota  = t.get("nota") or ""
        nota_str = f"  📝 {nota}" if nota else ""
        lines.append(
            f"  {i:2}. {fecha:<12} {t.get('descripcion',''):<28} "
            f"{_fmt(monto):>14}  [{cat}]{nota_str}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_transactions_by_category(
    category_name: str,
    year:          Optional[int] = None,
    month:         Optional[int] = None,
) -> str:
    """
    Lista todas las transacciones de una categoría específica.

    Args:
        category_name: Nombre de la categoría (ej: "Supermercados", "Restaurantes")
        year:          Año (opcional)
        month:         Mes (opcional)
    """
    # Resolver id de categoría por nombre
    cats = _get("/categories/")
    if isinstance(cats, dict) and "error" in cats:
        return f"Error: {cats['error']}"

    cat = next(
        (c for c in cats if c["name"].lower() == category_name.lower()), None
    )
    if not cat:
        available = ", ".join(c["name"] for c in cats)
        return f"Categoría '{category_name}' no encontrada. Disponibles: {available}"

    params: dict = {"category_id": cat["id"], "limit": 500}
    if year:  params["year"]  = year
    if month: params["month"] = month

    txs = _get("/transactions/", params)
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"
    if not txs:
        return f"No hay transacciones en '{category_name}' para el período."

    total_deb = sum(float(t.get("debito")  or 0) for t in txs)
    total_cre = sum(float(t.get("credito") or 0) for t in txs)
    period    = f"{MONTH_NAMES[month]} {year}" if month and year else (str(year) if year else "todo el historial")

    lines = [
        f"🏷️ **{category_name} – {period}**",
        f"   {len(txs)} transacciones · Débitos: {_fmt(total_deb)} · Créditos: {_fmt(total_cre)}",
        "",
    ]
    for t in txs:
        deb = float(t.get("debito")  or 0)
        cre = float(t.get("credito") or 0)
        fecha = t.get("fecha_completa") or t.get("fecha", "")
        signo = f"-{_fmt(deb)}" if deb else f"+{_fmt(cre)}"
        nota  = t.get("nota") or ""
        nota_str = f"  📝 {nota}" if nota else ""
        lines.append(f"  {fecha:<12} {t.get('descripcion',''):<30} {signo:>16}{nota_str}")
    return "\n".join(lines)


@mcp.tool()
def get_recurring_expenses(min_months: int = 2) -> str:
    """
    Detecta gastos que se repiten en múltiples meses (suscripciones, servicios fijos).

    Args:
        min_months: Mínimo de meses en que debe aparecer para considerarse recurrente (default 2)
    """
    txs = _get("/transactions/", {"limit": 2000})
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"
    if not txs:
        return "No hay transacciones cargadas."

    from collections import defaultdict
    # Agrupar por descripción: {descripcion: {(year,month): total_debito}}
    by_desc: dict[str, dict] = defaultdict(lambda: defaultdict(float))
    for t in txs:
        if float(t.get("debito") or 0) > 0:
            fc = t.get("fecha_completa", "")
            if fc:
                y, m = int(fc[:4]), int(fc[5:7])
                by_desc[t.get("descripcion", "")][( y, m)] += float(t["debito"])

    recurrentes = [
        (desc, periods)
        for desc, periods in by_desc.items()
        if len(periods) >= min_months
    ]
    recurrentes.sort(key=lambda x: len(x[1]), reverse=True)

    if not recurrentes:
        return f"No se detectaron gastos recurrentes en al menos {min_months} meses."

    lines = [
        f"🔁 **Gastos recurrentes** (≥{min_months} meses)",
        "",
        f"{'Descripción':<30} {'Meses':>6} {'Promedio':>14} {'Total':>14}",
        "─" * 68,
    ]
    for desc, periods in recurrentes[:20]:
        valores = list(periods.values())
        promedio = sum(valores) / len(valores)
        total    = sum(valores)
        n_meses  = len(periods)
        lines.append(
            f"{desc:<30} {n_meses:>6}   {_fmt(promedio):>14} {_fmt(total):>14}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_spending_stats(
    year:  Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """
    Estadísticas descriptivas de los gastos: promedio, mediana, máximo, mínimo
    y distribución por rango de monto.

    Args:
        year:  Año (opcional)
        month: Mes (opcional)
    """
    params: dict = {"limit": 2000}
    if year:  params["year"]  = year
    if month: params["month"] = month

    txs = _get("/transactions/", params)
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"

    debitos = sorted([float(t["debito"]) for t in txs if float(t.get("debito") or 0) > 0])
    if not debitos:
        return "No hay débitos para calcular estadísticas."

    n      = len(debitos)
    total  = sum(debitos)
    prom   = total / n
    median = debitos[n // 2] if n % 2 else (debitos[n//2 - 1] + debitos[n//2]) / 2
    period = f"{MONTH_NAMES[month]} {year}" if month and year else (str(year) if year else "todo el historial")

    # Distribución por rangos
    rangos = [
        ("< $ 100",        lambda x: x < 100),
        ("$ 100 – 500",    lambda x: 100 <= x < 500),
        ("$ 500 – 2.000",  lambda x: 500 <= x < 2000),
        ("$ 2.000 – 10K",  lambda x: 2000 <= x < 10000),
        ("> $ 10.000",     lambda x: x >= 10000),
    ]

    lines = [
        f"📊 **Estadísticas de gastos – {period}**",
        "",
        f"  Transacciones:  {n}",
        f"  Total:          {_fmt(total)}",
        f"  Promedio:       {_fmt(prom)}",
        f"  Mediana:        {_fmt(median)}",
        f"  Mínimo:         {_fmt(debitos[0])}",
        f"  Máximo:         {_fmt(debitos[-1])}",
        "",
        "  Distribución:",
    ]
    for label, fn in rangos:
        cnt  = sum(1 for x in debitos if fn(x))
        pct  = cnt / n * 100
        bar  = "█" * int(pct / 5)
        lines.append(f"    {label:<18} {cnt:4}  {pct:5.1f}% {bar}")

    return "\n".join(lines)


@mcp.tool()
def get_daily_spending(year: int, month: int) -> str:
    """
    Muestra el gasto total por día para un mes específico.
    Útil para identificar días de alto consumo.

    Args:
        year:  Año
        month: Mes (1-12)
    """
    txs = _get("/transactions/", {"year": year, "month": month, "limit": 2000})
    if isinstance(txs, dict) and "error" in txs:
        return f"Error: {txs['error']}"
    if not txs:
        return f"No hay transacciones para {MONTH_NAMES[month]} {year}."

    from collections import defaultdict
    por_dia: dict[str, float] = defaultdict(float)
    for t in txs:
        if float(t.get("debito") or 0) > 0 and t.get("fecha_completa"):
            por_dia[t["fecha_completa"]] += float(t["debito"])

    if not por_dia:
        return "No hay débitos con fecha completa."

    max_gasto = max(por_dia.values())
    lines     = [f"📅 **Gasto diario – {MONTH_NAMES[month]} {year}**", ""]
    for fecha in sorted(por_dia):
        gasto  = por_dia[fecha]
        bar    = "█" * int(gasto / max_gasto * 20)
        dia    = fecha[8:]    # "2026-03-05" → "05"
        dow    = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][
            __import__("datetime").date.fromisoformat(fecha).weekday()
        ]
        alerta = " ⚠️" if gasto == max_gasto else ""
        lines.append(f"  {dia} {dow}  {bar:<22} {_fmt(gasto):>14}{alerta}")

    lines += ["", f"  Día con mayor gasto: {_fmt(max_gasto)}"]
    return "\n".join(lines)


# ── Prompts (slash commands) ──────────────────────────────────────────────────

@mcp.prompt()
def analizar_mes(year: Optional[int] = None, month: Optional[int] = None) -> str:
    """
    /analizar-mes — Análisis completo del mes indicado.
    Si no se especifica mes/año, usa el más reciente disponible.
    """
    today = date.today()
    y = year  or today.year
    m = month or today.month

    return (
        f"Hacé un análisis completo del mes {MONTH_NAMES[m]} {y}. "
        f"Usá la tool `get_monthly_summary` con year={y} y month={m}. "
        f"Luego complementá con `get_category_spending` para el mismo período. "
        f"Finalmente, compará con el mes anterior usando `compare_periods` si hay datos disponibles. "
        f"Presentá un resumen ejecutivo con puntos clave, alertas de gastos inusuales "
        f"y una recomendación concreta."
    )


@mcp.prompt()
def comparar_anios(year1: Optional[int] = None, year2: Optional[int] = None) -> str:
    """
    /comparar-años — Compara el comportamiento financiero entre dos años.
    """
    today = date.today()
    y1 = year1 or today.year - 1
    y2 = year2 or today.year

    return (
        f"Comparate los años {y1} y {y2}. "
        f"Primero consultá `get_balance_trend` para ver la evolución. "
        f"Luego usá `get_yearly_credits_avg` para comparar ingresos. "
        f"Calculá el promedio mensual de débitos en cada año usando `get_category_spending` "
        f"para cada mes disponible. "
        f"Presentá: (1) cuál año fue mejor financieramente, (2) en qué categorías cambió más el gasto, "
        f"(3) tendencia general."
    )


@mcp.prompt()
def donde_gasto_mas(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """
    /donde-gasto-mas — Identifica los principales destinos de gasto.
    Puede ser ambiguo: si no se especifica período, clarificá antes de responder.
    """
    if year is None and month is None:
        return (
            "El usuario quiere saber dónde gasta más pero no especificó el período. "
            "Antes de usar las tools, preguntale: "
            "'¿Querés que analice (1) el mes actual, (2) un mes específico, "
            "o (3) el historial completo?' "
            "Una vez que confirme, usá `get_top_merchants` y `get_category_spending` "
            "con el período elegido."
        )
    today = date.today()
    y = year  or today.year
    m = month or today.month
    return (
        f"Analizá dónde gasta más el usuario en {MONTH_NAMES[m] if m else str(y)}. "
        f"Usá `get_top_merchants` con year={y}{f', month={m}' if m else ''} para ver los comercios. "
        f"Luego `get_category_spending` para ver las categorías. "
        f"Identificá patrones, gastos recurrentes y sugiere dónde podría recortar."
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Starting MCP server (transport={MCP_TRANSPORT}, port={MCP_PORT})")
    print(f"API URL: {API_URL}")

    if MCP_TRANSPORT == "sse":
        # FastMCP reads FASTMCP_HOST / FASTMCP_PORT from env.
        # Setting them programmatically as fallback.
        os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")
        os.environ.setdefault("FASTMCP_PORT", str(MCP_PORT))
        try:
            mcp.run(transport="sse", host="0.0.0.0", port=MCP_PORT)
        except TypeError:
            # Older FastMCP versions don't accept host/port kwargs
            mcp.run(transport="sse")
    else:
        mcp.run()  # stdio
