import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Estado de Cuenta · Itaú",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background-color: #0f0f0f;
    color: #f0ede6;
}

section[data-testid="stSidebar"] {
    background-color: #161616;
    border-right: 1px solid #2a2a2a;
}

.metric-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 8px;
}
.metric-value {
    font-family: 'DM Mono', monospace;
    font-size: 26px;
    font-weight: 500;
    color: #f0ede6;
    line-height: 1;
}
.metric-sub {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #555;
    margin-top: 6px;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #444;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1f1f1f;
}

.tag {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 500;
}
.tag-debito { background: #2a1515; color: #ff6b6b; border: 1px solid #3d1f1f; }
.tag-credito { background: #0f2a1a; color: #51cf66; border: 1px solid #1a3d25; }

[data-testid="stDataFrame"] {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stMultiSelect"] label {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

# ── Datos de prueba ───────────────────────────────────────────────────────────
DATA = {
    "cuenta": "RICCARDO RAINIER INOJOSA MED",
    "fecha_estado": "27FEB2026",
    "saldo_apertura": 48111.50,
    "saldo_cierre": 6422.86,
    "movimientos": [
        {"fecha": "02FEB", "tipo": "COMPRA",       "descripcion": "SUPERMERCADO",  "debito": 199.80,   "credito": None,     "saldo": 47911.70},
        {"fecha": "02FEB", "tipo": "REDIVA 19210",  "descripcion": "DISCO N 17",    "debito": None,     "credito": 3.70,     "saldo": 47915.40},
        {"fecha": "02FEB", "tipo": "COMPRA",        "descripcion": "DISCO N 17",    "debito": 225.60,   "credito": None,     "saldo": 47689.80},
        {"fecha": "02FEB", "tipo": "REDIVA 19210",  "descripcion": "SUPERMERCADO",  "debito": None,     "credito": 3.28,     "saldo": 47693.08},
        {"fecha": "02FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD27245231",  "debito": 10.00,    "credito": None,     "saldo": 47683.08},
        {"fecha": "02FEB", "tipo": "CRE. CAMBIOS",  "descripcion": "RECH27245231",  "debito": None,     "credito": 10.00,    "saldo": 47693.08},
        {"fecha": "02FEB", "tipo": "TRASPASO A",    "descripcion": "2982535ILINK",  "debito": 10.00,    "credito": None,     "saldo": 47683.08},
        {"fecha": "02FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD27247476",  "debito": 20.00,    "credito": None,     "saldo": 47663.08},
        {"fecha": "02FEB", "tipo": "CRE. CAMBIOS",  "descripcion": "RECH27247476",  "debito": None,     "credito": 20.00,    "saldo": 47683.08},
        {"fecha": "02FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD27247935",  "debito": 10.00,    "credito": None,     "saldo": 47673.08},
        {"fecha": "02FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD27251877",  "debito": 12000.00, "credito": None,     "saldo": 35673.08},
        {"fecha": "02FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD27318019",  "debito": 5000.00,  "credito": None,     "saldo": 30673.08},
        {"fecha": "06FEB", "tipo": "CRED.DIRECTO",  "descripcion": "ARNALDO C. C",  "debito": None,     "credito": 41319.00, "saldo": 71992.08},
        {"fecha": "09FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD27615484",  "debito": 2000.00,  "credito": None,     "saldo": 69992.08},
        {"fecha": "11FEB", "tipo": "TRASPASO A",    "descripcion": "2982541ILINK",  "debito": 118.80,   "credito": None,     "saldo": 69873.28},
        {"fecha": "11FEB", "tipo": "TRASPASO A",    "descripcion": "2982541ILINK",  "debito": 39600.00, "credito": None,     "saldo": 30273.28},
        {"fecha": "12FEB", "tipo": "REDIVA 17934",  "descripcion": "RIGOR PIZZA",   "debito": None,     "credito": 28.77,    "saldo": 30302.05},
        {"fecha": "12FEB", "tipo": "REDIVA 17934",  "descripcion": "RIGOR PIZZA",   "debito": None,     "credito": 8.85,     "saldo": 30310.90},
        {"fecha": "12FEB", "tipo": "COMPRA",        "descripcion": "SUPERMERCADO",  "debito": 379.00,   "credito": None,     "saldo": 29931.90},
        {"fecha": "12FEB", "tipo": "COMPRA",        "descripcion": "RIGOR PIZZA",   "debito": 390.00,   "credito": None,     "saldo": 29541.90},
        {"fecha": "12FEB", "tipo": "COMPRA",        "descripcion": "RIGOR PIZZA",   "debito": 120.00,   "credito": None,     "saldo": 29421.90},
        {"fecha": "12FEB", "tipo": "TRASPASO A",    "descripcion": "2982541ILINK",  "debito": 5947.50,  "credito": None,     "saldo": 23474.40},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "MERPAGO*CLAR",  "debito": 400.00,   "credito": None,     "saldo": 23074.40},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "PUESTO BLANC",  "debito": 1295.00,  "credito": None,     "saldo": 21779.40},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "TATA 103 VIS",  "debito": None,     "credito": 9.71,     "saldo": 21789.11},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "TATA 103 VIS",  "debito": 592.06,   "credito": None,     "saldo": 21197.05},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "PUESTO BLANC",  "debito": None,     "credito": 21.23,    "saldo": 21218.28},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "MERPAGO*CLAR",  "debito": None,     "credito": 6.56,     "saldo": 21224.84},
        {"fecha": "18FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD28015964",  "debito": 2000.00,  "credito": None,     "saldo": 19224.84},
        {"fecha": "18FEB", "tipo": "CRE. CAMBIOS",  "descripcion": "RECH28015964",  "debito": None,     "credito": 2000.00,  "saldo": 21224.84},
        {"fecha": "18FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD28115559",  "debito": 10000.00, "credito": None,     "saldo": 11224.84},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "MUNDO TROPIC",  "debito": 320.00,   "credito": None,     "saldo": 10904.84},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "BIG",           "debito": None,     "credito": 4.75,     "saldo": 10909.59},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "FARMASHOP 64",  "debito": None,     "credito": 8.77,     "saldo": 10918.36},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "SUPERMERCADO",  "debito": None,     "credito": 2.21,     "saldo": 10920.57},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "TATA 103 VIS",  "debito": None,     "credito": 2.44,     "saldo": 10923.01},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "BIG",           "debito": 290.00,   "credito": None,     "saldo": 10633.01},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "FARMASHOP 64",  "debito": 535.00,   "credito": None,     "saldo": 10098.01},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "SUPERMERCADO",  "debito": 134.90,   "credito": None,     "saldo": 9963.11},
        {"fecha": "18FEB", "tipo": "REDIVA 19210",  "descripcion": "MUNDO TROPIC",  "debito": None,     "credito": 5.25,     "saldo": 9968.36},
        {"fecha": "18FEB", "tipo": "COMPRA",        "descripcion": "TATA 103 VIS",  "debito": 149.00,   "credito": None,     "saldo": 9819.36},
        {"fecha": "19FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD28173616",  "debito": 3000.00,  "credito": None,     "saldo": 6819.36},
        {"fecha": "19FEB", "tipo": "DEB. CAMBIOS",  "descripcion": "TOLD28174191",  "debito": 396.50,   "credito": None,     "saldo": 6422.86},
        {"fecha": "23FEB", "tipo": "COMPRA",        "descripcion": "DIGITALOCEAN",  "debito": 567.23,   "credito": None,     "saldo": 5855.63},
        {"fecha": "23FEB", "tipo": "DEVOLUCION",    "descripcion": "DIGITALOCEAN",  "debito": None,     "credito": 567.23,   "saldo": 6422.86},
    ]
}

# ── Preparar DataFrame ────────────────────────────────────────────────────────
df = pd.DataFrame(DATA["movimientos"])
df["debito"]  = df["debito"].fillna(0)
df["credito"] = df["credito"].fillna(0)

# Categoría simplificada para agrupar
def categorizar(tipo):
    t = tipo.upper()
    if t.startswith("COMPRA"):       return "Compras"
    if t.startswith("REDIVA"):       return "REDIVA (IVA)"
    if t.startswith("DEB. CAMBIOS"): return "Deb. Cambios"
    if t.startswith("CRE. CAMBIOS"): return "Cre. Cambios"
    if t.startswith("TRASPASO"):     return "Traspasos"
    if t.startswith("CRED"):         return "Crédito Directo"
    if t.startswith("DEVOLUCION"):   return "Devolución"
    return tipo

df["categoria"] = df["tipo"].apply(categorizar)

# Extraer número de día para ordenar
def dia(fecha_str):
    return int(fecha_str[:2])

df["dia"] = df["fecha"].apply(dia)
df = df.sort_values("dia").reset_index(drop=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💳 Estado de Cuenta")
    st.markdown(f"**{DATA['cuenta']}**")
    st.markdown(f"`{DATA['fecha_estado']}`")
    st.divider()

    meses_disponibles = ["FEB 2026"]
    mes_sel = st.multiselect("Mes", meses_disponibles, default=meses_disponibles,
                              help="Seleccioná uno o más meses")

    cats = sorted(df["categoria"].unique().tolist())
    cats_sel = st.multiselect("Tipo de movimiento", cats, default=cats)

    dias_disponibles = sorted(df["dia"].unique().tolist())
    dia_min, dia_max = st.select_slider(
        "Rango de días",
        options=dias_disponibles,
        value=(dias_disponibles[0], dias_disponibles[-1])
    )

    solo_debitos  = st.checkbox("Solo débitos")
    solo_creditos = st.checkbox("Solo créditos")

# ── Filtrar ───────────────────────────────────────────────────────────────────
df_f = df[
    df["categoria"].isin(cats_sel) &
    df["dia"].between(dia_min, dia_max)
].copy()

if solo_debitos:
    df_f = df_f[df_f["debito"] > 0]
if solo_creditos:
    df_f = df_f[df_f["credito"] > 0]

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_debito  = df_f["debito"].sum()
total_credito = df_f["credito"].sum()
variacion     = DATA["saldo_cierre"] - DATA["saldo_apertura"]
var_pct       = (variacion / DATA["saldo_apertura"]) * 100

def fmt(n):
    return f"$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

col1, col2, col3, col4 = st.columns(4)

cards = [
    (col1, "Saldo apertura",  fmt(DATA["saldo_apertura"]),  "feb 2026",              "#3b82f6"),
    (col2, "Saldo cierre",    fmt(DATA["saldo_cierre"]),    "feb 2026",              "#8b5cf6"),
    (col3, "Total débitos",   fmt(total_debito),            f"{len(df_f[df_f['debito']>0])} movimientos", "#ef4444"),
    (col4, "Total créditos",  fmt(total_credito),           f"{len(df_f[df_f['credito']>0])} movimientos", "#22c55e"),
]

for col, label, value, sub, accent in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card" style="--accent: {accent}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Variación ─────────────────────────────────────────────────────────────────
var_color = "#22c55e" if variacion >= 0 else "#ef4444"
var_icon  = "▲" if variacion >= 0 else "▼"
st.markdown(f"""
<div style="margin: 16px 0 0 0; font-family: 'DM Mono', monospace; font-size: 12px; color: {var_color};">
    {var_icon} Variación del período: {fmt(abs(variacion))} ({var_pct:+.1f}%)
</div>
""", unsafe_allow_html=True)

# ── Gráfico 1: Evolución del saldo ───────────────────────────────────────────
st.markdown('<div class="section-title">Evolución del saldo</div>', unsafe_allow_html=True)

fig_saldo = go.Figure()
fig_saldo.add_trace(go.Scatter(
    x=df_f["fecha"], y=df_f["saldo"],
    mode="lines",
    line=dict(color="#3b82f6", width=2),
    fill="tozeroy",
    fillcolor="rgba(59,130,246,0.06)",
    hovertemplate="<b>%{x}</b><br>Saldo: $ %{y:,.2f}<extra></extra>",
))
fig_saldo.add_hline(
    y=DATA["saldo_apertura"], line_dash="dot",
    line_color="#444", annotation_text="Apertura",
    annotation_font_color="#666", annotation_font_size=10
)
fig_saldo.update_layout(
    height=260,
    paper_bgcolor="#0f0f0f", plot_bgcolor="#0f0f0f",
    font=dict(family="DM Mono", color="#666", size=11),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(showgrid=False, zeroline=False, color="#444"),
    yaxis=dict(showgrid=True, gridcolor="#1a1a1a", zeroline=False, color="#444",
               tickformat="$,.0f"),
    hovermode="x unified",
)
st.plotly_chart(fig_saldo, use_container_width=True)

# ── Gráficos 2 y 3 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Breakdown</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([1.2, 1])

with col_a:
    # Débitos por categoría (barras horizontales)
    deb_cat = (
        df_f[df_f["debito"] > 0]
        .groupby("categoria")["debito"]
        .sum()
        .sort_values(ascending=True)
        .reset_index()
    )
    fig_bar = go.Figure(go.Bar(
        x=deb_cat["debito"], y=deb_cat["categoria"],
        orientation="h",
        marker=dict(
            color=deb_cat["debito"],
            colorscale=[[0, "#1f2a3a"], [1, "#3b82f6"]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>$ %{x:,.2f}<extra></extra>",
        text=[fmt(v) for v in deb_cat["debito"]],
        textposition="outside",
        textfont=dict(family="DM Mono", size=10, color="#666"),
    ))
    fig_bar.update_layout(
        title=dict(text="Débitos por categoría", font=dict(size=11, color="#555",
                   family="DM Mono"), x=0),
        height=280,
        paper_bgcolor="#0f0f0f", plot_bgcolor="#0f0f0f",
        font=dict(family="DM Mono", color="#666", size=10),
        margin=dict(l=0, r=60, t=30, b=0),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, color="#555"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_b:
    # Torta de composición débitos vs créditos
    fig_pie = go.Figure(go.Pie(
        labels=["Débitos", "Créditos"],
        values=[total_debito, total_credito],
        hole=0.65,
        marker=dict(colors=["#ef4444", "#22c55e"],
                    line=dict(color="#0f0f0f", width=3)),
        hovertemplate="<b>%{label}</b><br>$ %{value:,.2f}<br>%{percent}<extra></extra>",
        textfont=dict(family="DM Mono", size=10),
    ))
    fig_pie.add_annotation(
        text=f"<b>{fmt(total_debito + total_credito)}</b>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=11, color="#f0ede6", family="DM Mono"),
        align="center",
    )
    fig_pie.update_layout(
        title=dict(text="Composición total", font=dict(size=11, color="#555",
                   family="DM Mono"), x=0),
        height=280,
        paper_bgcolor="#0f0f0f", plot_bgcolor="#0f0f0f",
        font=dict(family="DM Mono", color="#666", size=10),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(font=dict(family="DM Mono", size=10, color="#555"),
                    bgcolor="#0f0f0f"),
        showlegend=True,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Tabla de movimientos ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">Movimientos</div>', unsafe_allow_html=True)

df_tabla = df_f[["fecha", "tipo", "descripcion", "debito", "credito", "saldo"]].copy()
df_tabla.columns = ["Fecha", "Tipo", "Descripción", "Débito", "Crédito", "Saldo"]

# Formatear montos
for col in ["Débito", "Crédito", "Saldo"]:
    df_tabla[col] = df_tabla[col].apply(
        lambda x: fmt(x) if x > 0 else "—"
    )

st.dataframe(
    df_tabla,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Débito":  st.column_config.TextColumn(width="small"),
        "Crédito": st.column_config.TextColumn(width="small"),
        "Saldo":   st.column_config.TextColumn(width="medium"),
    },
    height=400,
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #1a1a1a;
     font-family: 'DM Mono', monospace; font-size: 10px; color: #333; text-align: center;">
    ITAÚ · ESTADO DE CUENTA · FEB 2026
</div>
""", unsafe_allow_html=True)