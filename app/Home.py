import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.styles import GLOBAL_CSS, fmt_money, PRIMARY
from utils import api_client as api

st.set_page_config(
    page_title="Itaú Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo" style="font-size:22px;font-weight:800;'
        'color:#00c795;margin-bottom:4px;">💳 FinTrack</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:11px;color:#475569;margin-bottom:20px;">Itaú · Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.page_link("Home.py",                   label="Inicio",       icon="🏠")
    st.page_link("pages/1_Dashboard.py",      label="Dashboard",    icon="📊")
    st.page_link("pages/2_Movimientos.py",    label="Movimientos",  icon="📄")
    st.page_link("pages/3_Categorias.py",     label="Categorías",   icon="🏷️")
    st.divider()
    api_ok = api.health()
    status_color = "#00c795" if api_ok else "#ef4444"
    status_text  = "Conectado" if api_ok else "Sin conexión"
    st.markdown(
        f'<div style="font-size:11px;color:{status_color};">● API {status_text}</div>',
        unsafe_allow_html=True,
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:32px 0 24px 0;">
  <div style="font-size:11px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
              color:#475569;margin-bottom:8px;">BIENVENIDO</div>
  <h1 style="font-size:34px;font-weight:800;color:#f0ede6;margin:0 0 8px 0;line-height:1.2;">
      Dashboard Financiero
  </h1>
  <p style="font-size:14px;color:#64748b;margin:0;">
      Visualizá y analizá tus movimientos bancarios de Itaú Uruguay.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Quick stats ───────────────────────────────────────────────────────────────
stmts = []
total_tx = 0
try:
    stmts = api.get_statements()
    total_tx = sum(s.get("transaction_count", 0) for s in stmts)
except Exception:
    pass

col1, col2, col3, col4 = st.columns(4)

def stat_card(col, icon, label, value, color=PRIMARY):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--accent:{color}">
            <div style="font-size:24px;margin-bottom:8px;">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>""", unsafe_allow_html=True)

stat_card(col1, "📋", "Extractos cargados",  str(len(stmts)),  PRIMARY)
stat_card(col2, "💸", "Total movimientos",   str(total_tx),    "#3b82f6")

if stmts:
    last = stmts[0]
    stat_card(col3, "📅", "Último extracto",
              f"{last.get('month','')}/{last.get('year','')}", "#8b5cf6")
    cierre = last.get("saldo_cierre")
    stat_card(col4, "💰", "Saldo cierre último mes",
              fmt_money(cierre) if cierre else "—", "#22c55e")
else:
    stat_card(col3, "📅", "Último extracto",   "—", "#8b5cf6")
    stat_card(col4, "💰", "Saldo último mes",  "—", "#22c55e")

# ── Quick nav cards ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-title">Accesos rápidos</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="kpi-card" style="--accent:#3b82f6">
      <div style="font-size:28px;margin-bottom:10px;">📊</div>
      <div class="kpi-label">Dashboard</div>
      <div style="font-size:13px;color:#94a3b8;margin-top:4px;">
          6 gráficos interactivos: evolución de saldo, heatmap de gastos,
          proyección y más.
      </div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/1_Dashboard.py", label="Ver Dashboard →")

with c2:
    st.markdown("""
    <div class="kpi-card" style="--accent:#f59e0b">
      <div style="font-size:28px;margin-bottom:10px;">📄</div>
      <div class="kpi-label">Movimientos</div>
      <div style="font-size:13px;color:#94a3b8;margin-top:4px;">
          Subí el PDF del mes, explorá tus transacciones y exportá a CSV/Excel.
      </div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/2_Movimientos.py", label="Ver Movimientos →")

with c3:
    st.markdown("""
    <div class="kpi-card" style="--accent:#ec4899">
      <div style="font-size:28px;margin-bottom:10px;">🏷️</div>
      <div class="kpi-label">Categorías</div>
      <div style="font-size:13px;color:#94a3b8;margin-top:4px;">
          Clasificá tus referencias por categorías para mejores análisis.
      </div>
    </div>""", unsafe_allow_html=True)
    st.page_link("pages/3_Categorias.py", label="Gestionar Categorías →")

# ── Recent statements table ───────────────────────────────────────────────────
if stmts:
    st.markdown('<div class="section-title">Extractos cargados</div>', unsafe_allow_html=True)
    import pandas as pd
    MONTH_NAMES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                   "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]
    rows = []
    for s in stmts:
        rows.append({
            "Período":           f"{MONTH_NAMES[s['month']]} {s['year']}",
            "Cuenta":            s.get("account_name", "—"),
            "Saldo apertura":    fmt_money(s.get("saldo_apertura")),
            "Saldo cierre":      fmt_money(s.get("saldo_cierre")),
            "Movimientos":       s.get("transaction_count", 0),
            "Subido":            s.get("uploaded_at", "")[:10],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("Todavía no hay extractos cargados. Andá a **Movimientos** para subir tu primer PDF.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2736;
     font-size:10px;color:#1e2736;text-align:center;">
    ITAÚ · DASHBOARD FINANCIERO
</div>""", unsafe_allow_html=True)
