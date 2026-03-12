"""Categorías page – CRUD categories + assign references."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import httpx

from utils.styles import GLOBAL_CSS, section_title, PRIMARY
from utils import api_client as api

st.set_page_config(page_title="Categorías · Itaú", page_icon="🏷️", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:20px;font-weight:800;color:#00c795;">💳 FinTrack</div>',
                unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#475569;margin-bottom:16px;">Itaú · Categorías</div>',
                unsafe_allow_html=True)
    st.page_link("Home.py",                label="Inicio",      icon="🏠")
    st.page_link("pages/1_Dashboard.py",   label="Dashboard",   icon="📊")
    st.page_link("pages/2_Movimientos.py", label="Movimientos", icon="📄")
    st.page_link("pages/3_Categorias.py",  label="Categorías",  icon="🏷️")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:20px 0 8px 0;">
  <div style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:#475569;">
      CONFIGURACIÓN
  </div>
  <h1 style="font-size:28px;font-weight:800;color:#f0ede6;margin:4px 0 0 0;">Categorías</h1>
  <p style="font-size:13px;color:#64748b;margin:4px 0 0 0;">
      Gestioná las categorías y asignales referencias de tus movimientos.
  </p>
</div>""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_categories():
    try:
        return api.get_categories()
    except Exception:
        return []

@st.cache_data(ttl=5)
def load_references():
    try:
        return api.get_references()
    except Exception:
        return []

categories = load_categories()
references = load_references()

# ── Layout: two columns ───────────────────────────────────────────────────────
left, right = st.columns([1, 2.2], gap="large")

# ── Left: Category management ─────────────────────────────────────────────────
with left:
    st.markdown(section_title("Categorías"), unsafe_allow_html=True)

    # ── Add new category ──────────────────────────────────────────────────────
    with st.form("new_category", clear_on_submit=True):
        st.markdown("**Nueva categoría**")
        new_name  = st.text_input("Nombre", placeholder="ej: Entretenimiento")
        new_color = st.color_picker("Color", value=PRIMARY)
        submitted = st.form_submit_button("Agregar", type="primary", use_container_width=True)
        if submitted and new_name:
            try:
                api.create_category(new_name, new_color)
                st.success(f"Categoría **{new_name}** creada.")
                st.cache_data.clear()
                st.rerun()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 409:
                    st.warning("Ya existe una categoría con ese nombre.")
                else:
                    st.error(f"Error: {e}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Category list ─────────────────────────────────────────────────────────
    if not categories:
        st.info("No hay categorías.")
    else:
        for cat in categories:
            cid   = cat["id"]
            cname = cat["name"]
            cclr  = cat["color"]

            # Count references assigned
            ref_count = sum(1 for r in references if r.get("category_id") == cid)

            cols = st.columns([0.15, 0.6, 0.15, 0.1])
            with cols[0]:
                st.markdown(
                    f'<div style="width:14px;height:14px;border-radius:3px;'
                    f'background:{cclr};margin-top:10px;"></div>',
                    unsafe_allow_html=True,
                )
            with cols[1]:
                st.markdown(
                    f'<div style="padding:6px 0;font-size:13px;font-weight:600;">'
                    f'{cname}'
                    f'<span style="font-size:10px;color:#475569;font-weight:400;margin-left:6px;">'
                    f'{ref_count} refs</span></div>',
                    unsafe_allow_html=True,
                )
            with cols[2]:
                if st.button("✏", key=f"edit_{cid}", help="Editar"):
                    st.session_state[f"editing_{cid}"] = True
            with cols[3]:
                if st.button("✕", key=f"del_{cid}", help="Eliminar"):
                    try:
                        api.delete_category(cid)
                        st.success(f"Categoría **{cname}** eliminada.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            # Inline edit form
            if st.session_state.get(f"editing_{cid}"):
                with st.form(f"edit_cat_{cid}"):
                    e_name  = st.text_input("Nuevo nombre", value=cname, key=f"en_{cid}")
                    e_color = st.color_picker("Color", value=cclr, key=f"ec_{cid}")
                    c_save, c_cancel = st.columns(2)
                    if c_save.form_submit_button("Guardar"):
                        try:
                            api.update_category(cid, name=e_name, color=e_color)
                            del st.session_state[f"editing_{cid}"]
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    if c_cancel.form_submit_button("Cancelar"):
                        del st.session_state[f"editing_{cid}"]
                        st.rerun()

# ── Right: References table ───────────────────────────────────────────────────
with right:
    st.markdown(section_title("Referencias y asignación"), unsafe_allow_html=True)

    # Filter toggle
    show_unclassified = st.toggle("Mostrar solo sin categoría", value=False)

    cat_map = {c["id"]: c for c in categories}
    cat_options = {c["name"]: c["id"] for c in categories}
    cat_names   = ["Sin categoría"] + list(cat_options.keys())

    # Filter references
    refs_filtered = references
    if show_unclassified:
        refs_filtered = [r for r in references if r.get("category_id") is None]

    if not refs_filtered:
        st.info("No hay referencias para mostrar." + (" Todas están clasificadas." if show_unclassified else ""))
    else:
        # Search
        search_ref = st.text_input("Buscar referencia", placeholder="ej: SUPERMERCADO")
        if search_ref:
            refs_filtered = [r for r in refs_filtered
                             if search_ref.upper() in r["descripcion"].upper()]

        total_refs        = len(references)
        classified_refs   = sum(1 for r in references if r.get("category_id"))
        unclassified_refs = total_refs - classified_refs

        # Stats banner
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-bottom:12px;">
          <div style="font-size:12px;color:#64748b;">Total: <b style="color:#f0ede6">{total_refs}</b></div>
          <div style="font-size:12px;color:#64748b;">Clasificadas: <b style="color:#00c795">{classified_refs}</b></div>
          <div style="font-size:12px;color:#64748b;">Sin clasificar: <b style="color:#f59e0b">{unclassified_refs}</b></div>
        </div>""", unsafe_allow_html=True)

        # Render table-like rows using columns
        hdr = st.columns([2.5, 1.5, 1.5])
        hdr[0].markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.1em;'
                        'text-transform:uppercase;color:#475569;">Descripción</div>',
                        unsafe_allow_html=True)
        hdr[1].markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.1em;'
                        'text-transform:uppercase;color:#475569;">Categoría actual</div>',
                        unsafe_allow_html=True)
        hdr[2].markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.1em;'
                        'text-transform:uppercase;color:#475569;">Asignar</div>',
                        unsafe_allow_html=True)

        st.markdown('<hr style="border-color:#1e2736;margin:4px 0 8px 0;">', unsafe_allow_html=True)

        # Show up to 100 rows; paginate with offset
        page_size = 50
        if "ref_page" not in st.session_state:
            st.session_state.ref_page = 0

        start = st.session_state.ref_page * page_size
        end   = start + page_size
        page_refs = refs_filtered[start:end]

        for ref in page_refs:
            rid      = ref["id"]
            rdesc    = ref["descripcion"]
            rcid     = ref.get("category_id")
            rcat     = cat_map.get(rcid)
            rcat_name = rcat["name"]  if rcat else "Sin categoría"
            rcat_clr  = rcat["color"] if rcat else "#94a3b8"

            row = st.columns([2.5, 1.5, 1.5])
            with row[0]:
                icon = "⚠️" if not rcid else "●"
                clr  = "#f59e0b" if not rcid else rcat_clr
                st.markdown(
                    f'<div style="padding:4px 0;font-size:12px;color:#f0ede6;">'
                    f'<span style="color:{clr};margin-right:6px;">{icon}</span>{rdesc}</div>',
                    unsafe_allow_html=True,
                )
            with row[1]:
                badge_clr = f"rgba({int(rcat_clr[1:3],16)},{int(rcat_clr[3:5],16)},{int(rcat_clr[5:7],16)},0.15)"
                st.markdown(
                    f'<div style="padding:4px 0;">'
                    f'<span style="background:{badge_clr};color:{rcat_clr};'
                    f'border:1px solid {rcat_clr}44;border-radius:99px;'
                    f'padding:2px 8px;font-size:10px;font-weight:600;">{rcat_name}</span></div>',
                    unsafe_allow_html=True,
                )
            with row[2]:
                current_idx = cat_names.index(rcat_name) if rcat_name in cat_names else 0
                new_cat = st.selectbox(
                    "cat", cat_names,
                    index=current_idx,
                    key=f"ref_cat_{rid}",
                    label_visibility="collapsed",
                )
                if new_cat != rcat_name:
                    new_cid = cat_options.get(new_cat)
                    try:
                        api.assign_reference_category(rid, new_cid)
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        # Pagination
        total_pages = (len(refs_filtered) - 1) // page_size + 1
        if total_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            pcols = st.columns([1, 2, 1])
            with pcols[0]:
                if st.button("← Anterior") and st.session_state.ref_page > 0:
                    st.session_state.ref_page -= 1
                    st.rerun()
            with pcols[1]:
                st.markdown(
                    f'<div style="text-align:center;font-size:12px;color:#475569;padding-top:8px;">'
                    f'Página {st.session_state.ref_page + 1} de {total_pages} '
                    f'· {len(refs_filtered)} referencias</div>',
                    unsafe_allow_html=True,
                )
            with pcols[2]:
                if st.button("Siguiente →") and st.session_state.ref_page < total_pages - 1:
                    st.session_state.ref_page += 1
                    st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:48px;padding-top:16px;border-top:1px solid #1e2736;
     font-size:10px;color:#1e2736;text-align:center;">
    ITAÚ · GESTIÓN DE CATEGORÍAS
</div>""", unsafe_allow_html=True)
