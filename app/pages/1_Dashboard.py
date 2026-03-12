"""Dashboard page – all analytics charts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import date

from utils.styles import GLOBAL_CSS, kpi_card, section_title, fmt_money, chart_layout, PRIMARY
from utils import api_client as api

st.set_page_config(page_title="Dashboard · Itaú", page_icon="📊", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:20px;font-weight:800;color:#00c795;">💳 FinTrack</div>',
                unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#475569;margin-bottom:16px;">Itaú · Dashboard</div>',
                unsafe_allow_html=True)
    st.page_link("Home.py",                label="Inicio",      icon="🏠")
    st.page_link("pages/1_Dashboard.py",   label="Dashboard",   icon="📊")
    st.page_link("pages/2_Movimientos.py", label="Movimientos", icon="📄")
    st.page_link("pages/3_Categorias.py",  label="Categorías",  icon="🏷️")
    st.divider()
    st.markdown("**Filtros**")

    # Load statements for filter options
    stmts = []
    try:
        stmts = api.get_statements()
    except Exception:
        pass

    years_available = sorted({s["year"] for s in stmts}, reverse=True) if stmts else []
    months_available = list(range(1, 13))
    MONTH_NAMES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
                   "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

    selected_year  = st.selectbox("Año",  ["Todos"] + [str(y) for y in years_available])
    selected_month = st.selectbox("Mes",  ["Todos"] + [f"{m:02d} – {MONTH_NAMES[m]}" for m in months_available])

    year_filter  = int(selected_year)  if selected_year  != "Todos" else None
    month_filter = int(selected_month[:2]) if selected_month != "Todos" else None

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:20px 0 8px 0;">
  <div style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#475569;">
      ANÁLISIS
  </div>
  <h1 style="font-size:28px;font-weight:800;color:#f0ede6;margin:4px 0 0 0;">Dashboard</h1>
</div>""", unsafe_allow_html=True)

# ── Fetch all analytics ───────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_analytics(year_f, month_f):
    try:
        bal_evo    = api.get_balance_evolution()
        yearly_avg = api.get_yearly_credits_avg()
        cat_break  = api.get_category_breakdown(year_f, month_f)
        avg_close  = api.get_avg_vs_closing()
        heatmap    = api.get_heatmap(year_f, month_f)
        projection = api.get_projection(year_f, month_f)
        return bal_evo, yearly_avg, cat_break, avg_close, heatmap, projection
    except Exception as e:
        return None, None, None, None, None, None

bal_evo, yearly_avg, cat_break, avg_close, heatmap_data, proj = load_analytics(year_filter, month_filter)

if not bal_evo and not yearly_avg:
    st.info("No hay datos todavía. Subí un PDF en la página **Movimientos** para empezar.")
    st.stop()

# ── KPIs from latest statement ────────────────────────────────────────────────
try:
    last_stmt = stmts[0] if stmts else {}
    kpi_apertura = last_stmt.get("saldo_apertura")
    kpi_cierre   = last_stmt.get("saldo_cierre")
    kpi_promedio = last_stmt.get("saldo_promedio")
    last_period  = f"{MONTH_NAMES[last_stmt.get('month',1)]} {last_stmt.get('year','')}"

    all_tx = api.get_transactions(year=year_filter, month=month_filter, limit=2000)
    total_deb = sum(float(t.get("debito") or 0) for t in all_tx)
    total_cre = sum(float(t.get("credito") or 0) for t in all_tx)
except Exception:
    kpi_apertura = kpi_cierre = kpi_promedio = None
    last_period = "—"
    total_deb = total_cre = 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(kpi_card("Saldo apertura",  fmt_money(kpi_apertura), last_period, "#3b82f6"), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_card("Saldo cierre",    fmt_money(kpi_cierre),   last_period, "#8b5cf6"), unsafe_allow_html=True)
with col3:
    st.markdown(kpi_card("Total débitos",   fmt_money(total_deb),    f"{year_filter or 'Todo'}", "#ef4444"), unsafe_allow_html=True)
with col4:
    st.markdown(kpi_card("Total créditos",  fmt_money(total_cre),    f"{year_filter or 'Todo'}", PRIMARY), unsafe_allow_html=True)

# ── Chart 1: Evolución del saldo (line) ───────────────────────────────────────
st.markdown(section_title("Evolución del saldo apertura"), unsafe_allow_html=True)

if bal_evo:
    df_bal = pd.DataFrame(bal_evo)
    fig_evo = go.Figure()
    fig_evo.add_trace(go.Scatter(
        x=df_bal["month_label"], y=df_bal["saldo_apertura"].astype(float),
        name="Saldo apertura",
        mode="lines+markers",
        line=dict(color=PRIMARY, width=2),
        fill="tozeroy",
        fillcolor="rgba(0,199,149,0.06)",
        marker=dict(size=6, color=PRIMARY),
        hovertemplate="<b>%{x}</b><br>Apertura: %{y:$,.2f}<extra></extra>",
    ))
    if "saldo_cierre" in df_bal.columns:
        fig_evo.add_trace(go.Scatter(
            x=df_bal["month_label"], y=df_bal["saldo_cierre"].astype(float),
            name="Saldo cierre",
            mode="lines+markers",
            line=dict(color="#8b5cf6", width=2, dash="dot"),
            marker=dict(size=5, color="#8b5cf6"),
            hovertemplate="<b>%{x}</b><br>Cierre: %{y:$,.2f}<extra></extra>",
        ))
    layout = chart_layout(height=280)
    layout["yaxis"]["tickformat"] = "$,.0f"
    fig_evo.update_layout(**layout)
    st.plotly_chart(fig_evo, use_container_width=True)

    # Export
    with st.expander("⬇ Exportar datos de evolución"):
        st.download_button(
            "CSV", df_bal.to_csv(index=False).encode("utf-8"),
            "evolucion_saldo.csv", "text/csv",
        )

# ── Row: Category breakdown + Yearly credits ─────────────────────────────────
st.markdown(section_title("Breakdown por categoría / Créditos anuales"), unsafe_allow_html=True)
col_a, col_b = st.columns([1.6, 1])

with col_a:
    if cat_break:
        df_cat = pd.DataFrame(cat_break)
        df_cat = df_cat[df_cat["total_debito"] + df_cat["total_credito"] > 0]

        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            name="Débitos",
            x=df_cat["category"],
            y=df_cat["total_debito"].astype(float),
            marker_color="#ef4444",
            hovertemplate="<b>%{x}</b><br>Débitos: %{y:$,.2f}<extra></extra>",
        ))
        fig_cat.add_trace(go.Bar(
            name="Créditos",
            x=df_cat["category"],
            y=df_cat["total_credito"].astype(float),
            marker_color=PRIMARY,
            hovertemplate="<b>%{x}</b><br>Créditos: %{y:$,.2f}<extra></extra>",
        ))
        layout = chart_layout(
            title=dict(text="Débitos y créditos por categoría",
                       font=dict(size=12, color="#64748b"), x=0),
            barmode="group", height=300,
        )
        layout["yaxis"]["tickformat"] = "$,.0f"
        fig_cat.update_layout(**layout)
        st.plotly_chart(fig_cat, use_container_width=True)

        with st.expander("⬇ Exportar"):
            st.download_button(
                "CSV", df_cat.to_csv(index=False).encode("utf-8"),
                "categorias.csv", "text/csv",
            )

with col_b:
    if yearly_avg:
        df_yr = pd.DataFrame(yearly_avg)
        fig_yr = go.Figure(go.Bar(
            x=df_yr["year"].astype(str),
            y=df_yr["avg_credito"].astype(float),
            marker=dict(
                color=df_yr["avg_credito"].astype(float),
                colorscale=[[0, "rgba(0,199,149,.3)"], [1, PRIMARY]],
                showscale=False,
            ),
            text=[fmt_money(v) for v in df_yr["avg_credito"]],
            textposition="outside",
            textfont=dict(size=9, color="#64748b"),
            hovertemplate="<b>%{x}</b><br>Prom. crédito: %{y:$,.2f}<extra></extra>",
        ))
        layout = chart_layout(
            title=dict(text="Promedio de créditos por año",
                       font=dict(size=12, color="#64748b"), x=0),
            height=300,
        )
        layout["yaxis"]["tickformat"] = "$,.0f"
        fig_yr.update_layout(**layout)
        st.plotly_chart(fig_yr, use_container_width=True)

# ── Row: Avg vs Closing + Projection ─────────────────────────────────────────
st.markdown(section_title("Saldo promedio vs cierre / Proyección"), unsafe_allow_html=True)
col_c, col_d = st.columns(2)

with col_c:
    if avg_close:
        df_avc = pd.DataFrame(avg_close)
        df_avc = df_avc.dropna(subset=["saldo_promedio", "saldo_cierre"])
        if not df_avc.empty:
            fig_avc = go.Figure()
            fig_avc.add_trace(go.Bar(
                name="Saldo promedio",
                x=df_avc["month_label"],
                y=df_avc["saldo_promedio"].astype(float),
                marker_color="#3b82f6",
                hovertemplate="<b>%{x}</b><br>Promedio: %{y:$,.2f}<extra></extra>",
            ))
            fig_avc.add_trace(go.Bar(
                name="Saldo cierre",
                x=df_avc["month_label"],
                y=df_avc["saldo_cierre"].astype(float),
                marker_color=PRIMARY,
                hovertemplate="<b>%{x}</b><br>Cierre: %{y:$,.2f}<extra></extra>",
            ))
            layout = chart_layout(
                title=dict(text="Saldo promedio vs cierre",
                           font=dict(size=12, color="#64748b"), x=0),
                barmode="group", height=300,
            )
            layout["yaxis"]["tickformat"] = "$,.0f"
            fig_avc.update_layout(**layout)
            st.plotly_chart(fig_avc, use_container_width=True)

with col_d:
    if proj and proj.get("data"):
        df_proj = pd.DataFrame(proj["data"])
        actual  = df_proj[df_proj["is_actual"]]
        projected = df_proj[~df_proj["is_actual"]]

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=actual["day"], y=actual["balance"].astype(float),
            name="Real",
            mode="lines+markers",
            line=dict(color=PRIMARY, width=2),
            marker=dict(size=5, color=PRIMARY),
            hovertemplate="Día %{x}: %{y:$,.2f}<extra>Real</extra>",
        ))
        if not projected.empty:
            # Connect last actual point to projected line
            last_actual = actual.iloc[-1]
            conn_x = [last_actual["day"]] + projected["day"].tolist()
            conn_y = [float(last_actual["balance"])] + projected["balance"].astype(float).tolist()
            fig_proj.add_trace(go.Scatter(
                x=conn_x, y=conn_y,
                name="Proyección",
                mode="lines",
                line=dict(color=PRIMARY, width=2, dash="dot"),
                hovertemplate="Día %{x}: %{y:$,.2f}<extra>Proyección</extra>",
            ))
            fig_proj.add_annotation(
                x=conn_x[-1], y=conn_y[-1],
                text=f"Cierre est.<br>{fmt_money(proj['projected_closing'])}",
                showarrow=True, arrowhead=2,
                font=dict(size=10, color="#64748b"),
                arrowcolor="#475569",
                bgcolor="rgba(22,27,39,0.9)",
                bordercolor="#1e2736",
                borderwidth=1,
            )
        layout = chart_layout(
            title=dict(text="Proyección de saldo (regresión lineal)",
                       font=dict(size=12, color="#64748b"), x=0),
            height=300,
        )
        layout["xaxis"]["title"] = dict(text="Día del mes", font=dict(size=10))
        layout["yaxis"]["tickformat"] = "$,.0f"
        fig_proj.update_layout(**layout)
        st.plotly_chart(fig_proj, use_container_width=True)

        rate = proj.get("daily_rate", 0)
        rate_color = "#22c55e" if rate >= 0 else "#ef4444"
        rate_icon  = "▲" if rate >= 0 else "▼"
        st.markdown(
            f'<div style="font-size:11px;color:{rate_color};margin-top:-8px;">'
            f'{rate_icon} Variación diaria estimada: {fmt_money(abs(rate))} / día'
            f' · {proj.get("days_remaining", 0)} días restantes</div>',
            unsafe_allow_html=True,
        )

# ── Chart: Heatmap gastos día × categoría ────────────────────────────────────
st.markdown(section_title("Heatmap de gastos: día de semana × categoría"), unsafe_allow_html=True)

if heatmap_data:
    # PostgreSQL DOW: 0=Sunday, 1=Monday, ..., 6=Saturday
    DOW_MAP   = {0: "Dom", 1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb"}
    DOW_ORDER = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    df_heat = pd.DataFrame(heatmap_data)
    df_heat["day_name"] = df_heat["day_of_week"].map(DOW_MAP)

    pivot = df_heat.pivot_table(
        values="total", index="category", columns="day_name", aggfunc="sum", fill_value=0
    )
    # Reorder days
    existing_days = [d for d in DOW_ORDER if d in pivot.columns]
    pivot = pivot.reindex(columns=existing_days, fill_value=0)

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0,   "#0b1219"],
            [0.2, "rgba(0,199,149,0.2)"],
            [0.6, "rgba(0,199,149,0.6)"],
            [1,   PRIMARY],
        ],
        hovertemplate="%{y}<br>%{x}: %{z:$,.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(
            tickfont=dict(color="#64748b", size=9),
            outlinecolor="#1e2736",
            bgcolor="#0E1117",
        ),
    ))
    layout = chart_layout(
        title=dict(text="Gasto por día de semana y categoría",
                   font=dict(size=12, color="#64748b"), x=0),
        height=max(280, 45 * len(pivot)),
        hovermode="closest",
    )
    layout.pop("hovermode", None)
    layout["hovermode"] = "closest"
    layout["yaxis"] = dict(color="#64748b", showgrid=False, zeroline=False)
    layout["xaxis"] = dict(color="#64748b", showgrid=False, zeroline=False)
    fig_heat.update_layout(**layout)
    st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("⬇ Exportar heatmap"):
        st.download_button(
            "CSV", df_heat.to_csv(index=False).encode("utf-8"),
            "heatmap.csv", "text/csv",
        )
else:
    st.info("No hay datos suficientes para mostrar el heatmap con los filtros actuales.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2736;
     font-size:10px;color:#1e2736;text-align:center;">
    ITAÚ · DASHBOARD FINANCIERO
</div>""", unsafe_allow_html=True)
