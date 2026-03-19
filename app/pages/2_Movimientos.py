"""Movimientos page – PDF upload, transaction list, export."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io
import streamlit as st
import pandas as pd
import httpx

from utils.styles import GLOBAL_CSS, section_title, fmt_money, PRIMARY
from utils import api_client as api

st.set_page_config(page_title="Movimientos · Itaú", page_icon="📄", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

MONTH_NAMES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:20px;font-weight:800;color:#00c795;">💳 FinTrack</div>',
                unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#475569;margin-bottom:16px;">Itaú · Movimientos</div>',
                unsafe_allow_html=True)
    st.page_link("Home.py",                label="Inicio",      icon="🏠")
    st.page_link("pages/1_Dashboard.py",   label="Dashboard",   icon="📊")
    st.page_link("pages/2_Movimientos.py", label="Movimientos", icon="📄")
    st.page_link("pages/3_Categorias.py",  label="Categorías",  icon="🏷️")
    st.divider()
    st.markdown("**Filtros de tabla**")

    try:
        stmts = api.get_statements()
    except Exception:
        stmts = []

    year_opts  = sorted({s["year"] for s in stmts}, reverse=True) if stmts else []
    sel_year   = st.selectbox("Año",  ["Todos"] + [str(y) for y in year_opts])
    sel_month  = st.selectbox("Mes",  ["Todos"] + [f"{m:02d} – {MONTH_NAMES[m]}" for m in range(1, 13)])
    search_txt = st.text_input("Buscar descripción", placeholder="ej: SUPERMERCADO")

    year_f  = int(sel_year)       if sel_year  != "Todos" else None
    month_f = int(sel_month[:2])  if sel_month != "Todos" else None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:20px 0 8px 0;">
  <div style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#475569;">
      EXTRACTOS BANCARIOS
  </div>
  <h1 style="font-size:28px;font-weight:800;color:#f0ede6;margin:4px 0 0 0;">Movimientos</h1>
</div>""", unsafe_allow_html=True)

# ── Upload section ────────────────────────────────────────────────────────────
st.markdown(section_title("Subir nuevo extracto PDF"), unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Arrastrá o seleccioná tu estado de cuenta de Itaú",
    type=["pdf", "xls", "xlsx"],
    help="PDF o Excel (.xls/.xlsx) · Un archivo por mes · El sistema detecta duplicados automáticamente.",
)

if uploaded_file is not None:
    with st.spinner("Procesando archivo..."):
        try:
            result = api.upload_statement(uploaded_file.name, uploaded_file.getvalue())

            inserted = result.get("inserted", 0)
            skipped  = result.get("skipped",  0)
            total    = result.get("total_en_archivo", inserted + skipped)

            if inserted > 0:
                st.success(f"✅ **{result['message']}**")
            else:
                st.info(f"ℹ️ **{result['message']}**")

            col_i, col_s, col_t = st.columns(3)
            col_i.metric("Nuevos guardados", inserted)
            col_s.metric("Ya existían",      skipped)
            col_t.metric("Total en archivo", total)

            st.caption(
                f"Apertura: `{fmt_money(result.get('saldo_apertura'))}`  ·  "
                f"Cierre: `{fmt_money(result.get('saldo_cierre'))}`"
            )
            st.cache_data.clear()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                st.error(f"❌ Error al parsear: {e.response.json().get('detail', e)}")
            else:
                st.error(f"❌ Error del servidor ({e.response.status_code}): {e.response.text[:200]}")
        except Exception as e:
            st.error(f"❌ No se pudo conectar con la API: {e}")

# ── Statements list ───────────────────────────────────────────────────────────
if stmts:
    st.markdown(section_title("Extractos cargados"), unsafe_allow_html=True)
    cols = st.columns(min(len(stmts), 4))
    for i, s in enumerate(stmts[:4]):
        with cols[i % 4]:
            period = f"{MONTH_NAMES[s['month']]} {s['year']}"
            st.markdown(f"""
            <div class="kpi-card" style="--accent:#3b82f6;margin-bottom:8px;">
                <div class="kpi-label">{period}</div>
                <div class="kpi-value">{fmt_money(s.get('saldo_cierre'))}</div>
                <div class="kpi-sub">{s.get('transaction_count', 0)} movimientos</div>
            </div>""", unsafe_allow_html=True)

    # Delete statement
    with st.expander("🗑 Eliminar extracto"):
        stmt_options = {
            f"{MONTH_NAMES[s['month']]} {s['year']} (id={s['id']})": s["id"]
            for s in stmts
        }
        to_delete = st.selectbox("Seleccioná el extracto a eliminar", list(stmt_options.keys()))
        if st.button("Eliminar", type="primary"):
            try:
                api.delete_statement(stmt_options[to_delete])
                st.success("Extracto eliminado.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ── Transactions table ────────────────────────────────────────────────────────
st.markdown(section_title("Tabla de movimientos"), unsafe_allow_html=True)

try:
    txs = api.get_transactions(
        year=year_f, month=month_f,
        search=search_txt if search_txt else None,
        limit=2000,
    )
except Exception as e:
    st.error(f"No se pudo cargar la tabla: {e}")
    txs = []

if txs:
    rows = []
    for t in txs:
        cat = t.get("category")
        cat_name  = cat["name"]  if cat else "Sin categoría"
        rows.append({
            "_id":         t["id"],
            "Fecha":       t.get("fecha_completa") or t.get("fecha", ""),
            "Tipo":        t.get("tipo", ""),
            "Descripción": t.get("descripcion", ""),
            "Categoría":   cat_name,
            "Débito":      float(t["debito"])  if t.get("debito")  else None,
            "Crédito":     float(t["credito"]) if t.get("credito") else None,
            "Saldo":       float(t["saldo"])   if t.get("saldo")   else None,
            "Nota":        t.get("nota") or "",
        })

    df_tx = pd.DataFrame(rows)

    # Summary row
    total_deb = df_tx["Débito"].sum()
    total_cre = df_tx["Crédito"].sum()
    tx_by_id  = {t["id"]: t for t in txs}
    c1, c2, c3 = st.columns(3)
    c1.metric("Movimientos", len(df_tx))
    c2.metric("Total débitos",  fmt_money(total_deb))
    c3.metric("Total créditos", fmt_money(total_cre))

    # Format for display
    df_display = df_tx.drop(columns=["_id"]).copy()
    df_display["Débito"]  = df_display["Débito"].apply(lambda x: fmt_money(x) if x else "—")
    df_display["Crédito"] = df_display["Crédito"].apply(lambda x: fmt_money(x) if x else "—")
    df_display["Saldo"]   = df_display["Saldo"].apply(lambda x: fmt_money(x) if x else "—")

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "Fecha":       st.column_config.TextColumn(width="small"),
            "Tipo":        st.column_config.TextColumn(width="medium"),
            "Descripción": st.column_config.TextColumn(width="large"),
            "Categoría":   st.column_config.TextColumn(width="medium"),
            "Débito":      st.column_config.TextColumn(width="small"),
            "Crédito":     st.column_config.TextColumn(width="small"),
            "Saldo":       st.column_config.TextColumn(width="medium"),
            "Nota":        st.column_config.TextColumn(width="large"),
        },
    )

    # ── Nota editor ───────────────────────────────────────────────────────────
    with st.expander("📝 Agregar / editar nota en un movimiento"):
        tx_options = {
            f"{r['Fecha']}  ·  {r['Descripción'][:40]}": r["_id"]
            for r in rows
        }
        sel_label = st.selectbox("Movimiento", list(tx_options.keys()), key="nota_select")
        sel_id    = tx_options[sel_label]
        current   = tx_by_id[sel_id].get("nota") or ""
        nueva_nota = st.text_area("Nota", value=current, key="nota_text", height=80,
                                  placeholder="Ej: cuota del auto, regalo cumpleaños, gasto compartido...")
        if st.button("Guardar nota", key="nota_save"):
            try:
                api.update_transaction_nota(sel_id, nueva_nota or None)
                st.success("Nota guardada.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    # ── Export ────────────────────────────────────────────────────────────────
    st.markdown(section_title("Exportar datos"), unsafe_allow_html=True)
    col_csv, col_xlsx, _ = st.columns([1, 1, 4])

    df_export = df_tx.drop(columns=["_id"])

    with col_csv:
        st.download_button(
            label="⬇ CSV",
            data=df_export.to_csv(index=False).encode("utf-8"),
            file_name="movimientos.csv",
            mime="text/csv",
        )

    with col_xlsx:
        xlsx_buf = io.BytesIO()
        with pd.ExcelWriter(xlsx_buf, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Movimientos")
        st.download_button(
            label="⬇ Excel",
            data=xlsx_buf.getvalue(),
            file_name="movimientos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.info("No hay movimientos para los filtros seleccionados.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2736;
     font-size:10px;color:#1e2736;text-align:center;">
    ITAÚ · MOVIMIENTOS DE CUENTA
</div>""", unsafe_allow_html=True)
