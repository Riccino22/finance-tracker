"""Shared CSS styles and chart helpers for the Streamlit app."""
from __future__ import annotations

PRIMARY      = "#00c795"
BG_DARK      = "#0E1117"
BG_CARD      = "#161B27"
BORDER_COLOR = "#1e2736"
TEXT_MUTED   = "#64748b"
TEXT_DIM     = "#475569"

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Sidebar ──────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #0b1219 !important;
    border-right: 1px solid #1e2736;
}
section[data-testid="stSidebar"] * { color: #94a3b8; }
section[data-testid="stSidebar"] .sidebar-logo { color: #00c795 !important; }

/* ── KPI cards ────────────────────────────────────────────────── */
.kpi-card {
    background: #161B27;
    border: 1px solid #1e2736;
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    margin-bottom: 4px;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #00c795);
}
.kpi-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 8px;
}
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #f0ede6;
    line-height: 1.3;
}
.kpi-sub {
    font-size: 11px;
    color: #475569;
    margin-top: 6px;
}

/* ── Section titles ───────────────────────────────────────────── */
.section-title {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #475569;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2736;
}

/* ── Alert banner ─────────────────────────────────────────────── */
.alert-banner {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.25);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.alert-banner .alert-text { color: #f59e0b; font-size: 13px; font-weight: 600; }
.alert-banner .alert-sub  { color: rgba(245,158,11,0.7); font-size: 11px; }

/* ── Category badges ──────────────────────────────────────────── */
.badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 99px;
}
.badge-green  { background:rgba(0,199,149,.15); color:#00c795; border:1px solid rgba(0,199,149,.3); }
.badge-red    { background:rgba(239,68,68,.15);  color:#ef4444; border:1px solid rgba(239,68,68,.3); }
.badge-amber  { background:rgba(245,158,11,.15); color:#f59e0b; border:1px solid rgba(245,158,11,.3); }
.badge-blue   { background:rgba(59,130,246,.15); color:#3b82f6; border:1px solid rgba(59,130,246,.3); }
.badge-gray   { background:rgba(100,116,139,.15);color:#94a3b8; border:1px solid rgba(100,116,139,.3); }

/* ── Upload zone ──────────────────────────────────────────────── */
.upload-zone {
    border: 2px dashed #1e3a2e;
    background: rgba(0,199,149,0.03);
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    transition: border-color .2s;
}
.upload-zone:hover { border-color: #00c795; }
</style>
"""


def kpi_card(label: str, value: str, sub: str = "", accent: str = PRIMARY) -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="kpi-card" style="--accent:{accent}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>"""


def section_title(text: str) -> str:
    return f'<div class="section-title">{text}</div>'


def fmt_money(n: float | str | None) -> str:
    if n is None:
        return "—"
    try:
        n = float(n)
    except (ValueError, TypeError):
        return "—"
    return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── Plotly common layout ──────────────────────────────────────────────────────

def chart_layout(**overrides) -> dict:
    base = dict(
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_CARD,
        font=dict(family="Inter", color=TEXT_MUTED, size=11),
        margin=dict(l=10, r=10, t=35, b=10),
        xaxis=dict(showgrid=False, zeroline=False, color=TEXT_DIM),
        yaxis=dict(showgrid=True, gridcolor=BORDER_COLOR, zeroline=False, color=TEXT_DIM),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_MUTED, size=10),
        ),
        hovermode="x unified",
    )
    base.update(overrides)
    return base
