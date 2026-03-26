"""Flask banking dashboard – migrated from Streamlit."""
from __future__ import annotations
import io
import json
import os

import pandas as pd
import plotly.graph_objects as go
import plotly.utils
from flask import (
    Flask, g, render_template, request,
    redirect, url_for, flash, Response, jsonify, send_file,
)

from utils import api_client as api

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fintrack-secret-2024")

PRIMARY = "#00c795"
MONTH_NAMES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
               "Jul", "Ago", "Set", "Oct", "Nov", "Dic"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_money(v) -> str:
    if v is None:
        return "—"
    try:
        return f"$ {float(v):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _fig_json(fig: go.Figure) -> str:
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def _chart_layout(**extra) -> dict:
    base: dict = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", size=10),
        margin=dict(l=0, r=0, t=28, b=0),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            font=dict(color="#94a3b8", size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(color="#64748b", showgrid=False, zeroline=False),
        yaxis=dict(
            color="#64748b", showgrid=True,
            gridcolor="rgba(30,39,54,0.8)", zeroline=False,
            tickformat="$,.0f",
        ),
        hoverlabel=dict(bgcolor="#161b27", font_size=11, font_color="#e2e8f0"),
    )
    base.update(extra)
    return base


# ── Context processors ────────────────────────────────────────────────────────

@app.before_request
def _check_api():
    g.api_ok = api.health()


@app.context_processor
def _inject_globals():
    return {
        "api_ok": getattr(g, "api_ok", False),
        "MONTH_NAMES": MONTH_NAMES,
        "fmt_money": fmt_money,
    }


# ── Home ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    stmts: list = []
    try:
        stmts = api.get_statements()
    except Exception:
        pass
    total_tx = sum(s.get("transaction_count", 0) for s in stmts)
    return render_template("index.html", stmts=stmts, total_tx=total_tx)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    year_f  = request.args.get("year",  type=int)
    month_f = request.args.get("month", type=int)

    stmts: list = []
    try:
        stmts = api.get_statements()
    except Exception:
        pass

    years = sorted({s["year"] for s in stmts}, reverse=True) if stmts else []

    # Fetch all analytics
    bal_evo = yearly_avg = cat_break = avg_close = heatmap_data = proj = None
    try:
        bal_evo      = api.get_balance_evolution()
        yearly_avg   = api.get_yearly_credits_avg()
        cat_break    = api.get_category_breakdown(year_f, month_f)
        avg_close    = api.get_avg_vs_closing()
        heatmap_data = api.get_heatmap(year_f, month_f)
        proj         = api.get_projection(year_f, month_f)
    except Exception:
        pass

    # KPIs
    kpi_apertura = kpi_cierre = None
    total_deb = total_cre = 0
    last_period = "—"
    try:
        if stmts:
            last = stmts[0]
            kpi_apertura = last.get("saldo_apertura")
            kpi_cierre   = last.get("saldo_cierre")
            m = last.get("month", 1)
            last_period  = f"{MONTH_NAMES[m]} {last.get('year', '')}"
        all_tx = api.get_transactions(year=year_f, month=month_f, limit=2000)
        total_deb = sum(float(t.get("debito")  or 0) for t in all_tx)
        total_cre = sum(float(t.get("credito") or 0) for t in all_tx)
    except Exception:
        pass

    charts: dict[str, str] = {}

    # 1. Balance evolution
    if bal_evo:
        df = pd.DataFrame(bal_evo)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["month_label"], y=df["saldo_apertura"].astype(float),
            name="Saldo apertura", mode="lines+markers",
            line=dict(color=PRIMARY, width=2),
            fill="tozeroy", fillcolor="rgba(0,199,149,0.06)",
            marker=dict(size=6, color=PRIMARY),
            hovertemplate="<b>%{x}</b><br>Apertura: %{y:$,.2f}<extra></extra>",
        ))
        if "saldo_cierre" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["month_label"], y=df["saldo_cierre"].astype(float),
                name="Saldo cierre", mode="lines+markers",
                line=dict(color="#8b5cf6", width=2, dash="dot"),
                marker=dict(size=5, color="#8b5cf6"),
                hovertemplate="<b>%{x}</b><br>Cierre: %{y:$,.2f}<extra></extra>",
            ))
        fig.update_layout(**_chart_layout(height=280))
        charts["balance_evo"] = _fig_json(fig)

    # 2. Category breakdown
    if cat_break:
        df_cat = pd.DataFrame(cat_break)
        df_cat = df_cat[df_cat["total_debito"] + df_cat["total_credito"] > 0]
        if not df_cat.empty:
            fig_cat = go.Figure()
            fig_cat.add_trace(go.Bar(
                name="Débitos", x=df_cat["category"],
                y=df_cat["total_debito"].astype(float),
                marker_color="#ef4444",
                hovertemplate="<b>%{x}</b><br>Débitos: %{y:$,.2f}<extra></extra>",
            ))
            fig_cat.add_trace(go.Bar(
                name="Créditos", x=df_cat["category"],
                y=df_cat["total_credito"].astype(float),
                marker_color=PRIMARY,
                hovertemplate="<b>%{x}</b><br>Créditos: %{y:$,.2f}<extra></extra>",
            ))
            fig_cat.update_layout(**_chart_layout(barmode="group", height=300))
            charts["cat_break"] = _fig_json(fig_cat)

    # 3. Yearly credits avg
    if yearly_avg:
        df_yr = pd.DataFrame(yearly_avg)
        vals = df_yr["avg_credito"].astype(float)
        fig_yr = go.Figure(go.Bar(
            x=df_yr["year"].astype(str), y=vals,
            marker=dict(
                color=vals,
                colorscale=[[0, "rgba(0,199,149,.3)"], [1, PRIMARY]],
                showscale=False,
            ),
            text=[fmt_money(v) for v in vals],
            textposition="outside",
            textfont=dict(size=9, color="#64748b"),
            hovertemplate="<b>%{x}</b><br>Prom. crédito: %{y:$,.2f}<extra></extra>",
        ))
        fig_yr.update_layout(**_chart_layout(height=300))
        charts["yearly_avg"] = _fig_json(fig_yr)

    # 4. Avg vs closing
    if avg_close:
        df_avc = pd.DataFrame(avg_close).dropna(subset=["saldo_promedio", "saldo_cierre"])
        if not df_avc.empty:
            fig_avc = go.Figure()
            fig_avc.add_trace(go.Bar(
                name="Saldo promedio", x=df_avc["month_label"],
                y=df_avc["saldo_promedio"].astype(float), marker_color="#3b82f6",
                hovertemplate="<b>%{x}</b><br>Promedio: %{y:$,.2f}<extra></extra>",
            ))
            fig_avc.add_trace(go.Bar(
                name="Saldo cierre", x=df_avc["month_label"],
                y=df_avc["saldo_cierre"].astype(float), marker_color=PRIMARY,
                hovertemplate="<b>%{x}</b><br>Cierre: %{y:$,.2f}<extra></extra>",
            ))
            fig_avc.update_layout(**_chart_layout(barmode="group", height=300))
            charts["avg_close"] = _fig_json(fig_avc)

    # 5. Projection
    if proj and proj.get("data"):
        df_proj   = pd.DataFrame(proj["data"])
        actual    = df_proj[df_proj["is_actual"]]
        projected = df_proj[~df_proj["is_actual"]]
        fig_proj  = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=actual["day"], y=actual["balance"].astype(float),
            name="Real", mode="lines+markers",
            line=dict(color=PRIMARY, width=2),
            marker=dict(size=5, color=PRIMARY),
            hovertemplate="Día %{x}: %{y:$,.2f}<extra>Real</extra>",
        ))
        if not projected.empty:
            last_a  = actual.iloc[-1]
            conn_x  = [last_a["day"]] + projected["day"].tolist()
            conn_y  = [float(last_a["balance"])] + projected["balance"].astype(float).tolist()
            fig_proj.add_trace(go.Scatter(
                x=conn_x, y=conn_y, name="Proyección", mode="lines",
                line=dict(color=PRIMARY, width=2, dash="dot"),
                hovertemplate="Día %{x}: %{y:$,.2f}<extra>Proyección</extra>",
            ))
            fig_proj.add_annotation(
                x=conn_x[-1], y=conn_y[-1],
                text=f"Cierre est.<br>{fmt_money(proj.get('projected_closing'))}",
                showarrow=True, arrowhead=2,
                font=dict(size=10, color="#64748b"),
                arrowcolor="#475569",
                bgcolor="rgba(22,27,39,0.9)",
                bordercolor="#1e2736", borderwidth=1,
            )
        layout = _chart_layout(height=300)
        layout["xaxis"]["title"] = dict(text="Día del mes", font=dict(size=10))
        fig_proj.update_layout(**layout)
        charts["projection"] = _fig_json(fig_proj)

    # 6. Heatmap
    if heatmap_data:
        DOW_MAP   = {0: "Dom", 1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb"}
        DOW_ORDER = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        df_heat = pd.DataFrame(heatmap_data)
        df_heat["day_name"] = df_heat["day_of_week"].map(DOW_MAP)
        pivot = df_heat.pivot_table(
            values="total", index="category", columns="day_name",
            aggfunc="sum", fill_value=0,
        )
        existing = [d for d in DOW_ORDER if d in pivot.columns]
        pivot = pivot.reindex(columns=existing, fill_value=0)
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
            colorbar=dict(tickfont=dict(color="#64748b", size=9), bgcolor="rgba(0,0,0,0)"),
        ))
        h_layout = _chart_layout(height=max(280, 45 * len(pivot)))
        h_layout["yaxis"] = dict(color="#64748b", showgrid=False, zeroline=False)
        h_layout["xaxis"] = dict(color="#64748b", showgrid=False, zeroline=False)
        fig_heat.update_layout(**h_layout)
        charts["heatmap"] = _fig_json(fig_heat)

    return render_template(
        "dashboard.html",
        stmts=stmts,
        years=years,
        year_f=year_f,
        month_f=month_f,
        kpi_apertura=fmt_money(kpi_apertura),
        kpi_cierre=fmt_money(kpi_cierre),
        total_deb=fmt_money(total_deb),
        total_cre=fmt_money(total_cre),
        last_period=last_period,
        charts=charts,
        proj=proj,
    )


# ── Movimientos ───────────────────────────────────────────────────────────────

PAGE_SIZE_TX = 50


@app.route("/movimientos")
def movimientos():
    year_f  = request.args.get("year",   type=int)
    month_f = request.args.get("month",  type=int)
    search  = request.args.get("search", "").strip() or None
    page    = request.args.get("page",   type=int, default=1)

    stmts: list = []
    try:
        stmts = api.get_statements()
    except Exception:
        pass

    txs: list = []
    try:
        txs = api.get_transactions(year=year_f, month=month_f, search=search, limit=2000)
    except Exception:
        pass

    years = sorted({s["year"] for s in stmts}, reverse=True) if stmts else []

    total_deb = sum(float(t.get("debito")  or 0) for t in txs)
    total_cre = sum(float(t.get("credito") or 0) for t in txs)

    total_pages = max(1, (len(txs) - 1) // PAGE_SIZE_TX + 1)
    page = max(1, min(page, total_pages))
    txs_page = txs[(page - 1) * PAGE_SIZE_TX: page * PAGE_SIZE_TX]

    return render_template(
        "movimientos.html",
        stmts=stmts,
        txs=txs_page,
        years=years,
        year_f=year_f,
        month_f=month_f,
        search=search or "",
        page=page,
        total_pages=total_pages,
        total_deb=fmt_money(total_deb),
        total_cre=fmt_money(total_cre),
        tx_count=len(txs),
    )


@app.route("/movimientos/upload", methods=["POST"])
def movimientos_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        flash("No se seleccionó ningún archivo.", "error")
        return redirect(url_for("movimientos"))
    try:
        result  = api.upload_statement(f.filename, f.read())
        inserted = result.get("inserted", 0)
        msg      = result.get("message", "Procesado")
        flash(msg, "success" if inserted > 0 else "info")
    except Exception as e:
        flash(f"Error al procesar: {e}", "error")
    return redirect(url_for("movimientos"))


@app.route("/movimientos/delete/<int:stmt_id>", methods=["POST"])
def movimientos_delete(stmt_id: int):
    try:
        api.delete_statement(stmt_id)
        flash("Extracto eliminado.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("movimientos"))


@app.route("/movimientos/<int:tx_id>/nota", methods=["POST"])
def movimientos_nota(tx_id: int):
    nota = request.form.get("nota", "").strip() or None
    try:
        api.update_transaction_nota(tx_id, nota)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/movimientos/export")
def movimientos_export():
    year_f  = request.args.get("year",   type=int)
    month_f = request.args.get("month",  type=int)
    search  = request.args.get("search", "").strip() or None
    fmt     = request.args.get("fmt", "csv")

    txs: list = []
    try:
        txs = api.get_transactions(year=year_f, month=month_f, search=search, limit=10000)
    except Exception:
        pass

    rows = []
    for t in txs:
        cat = t.get("category")
        rows.append({
            "Fecha":       t.get("fecha_completa") or t.get("fecha", ""),
            "Tipo":        t.get("tipo", ""),
            "Descripción": t.get("descripcion", ""),
            "Categoría":   cat["name"] if cat else "Sin categoría",
            "Débito":      t.get("debito"),
            "Crédito":     t.get("credito"),
            "Saldo":       t.get("saldo"),
            "Nota":        t.get("nota") or "",
        })
    df = pd.DataFrame(rows)

    if fmt == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Movimientos")
        buf.seek(0)
        return send_file(
            buf, as_attachment=True, download_name="movimientos.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    return Response(
        df.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=movimientos.csv"},
    )


# ── Categorías ────────────────────────────────────────────────────────────────

PAGE_SIZE_REF = 50


@app.route("/categorias")
def categorias():
    search_ref        = request.args.get("search", "").strip()
    only_unclassified = request.args.get("unclassified") == "1"
    ref_page          = request.args.get("ref_page", type=int, default=1)

    categories: list = []
    references: list = []
    try:
        categories = api.get_categories()
        references = api.get_references()
    except Exception:
        pass

    refs_filtered = references
    if only_unclassified:
        refs_filtered = [r for r in references if r.get("category_id") is None]
    if search_ref:
        refs_filtered = [r for r in refs_filtered
                         if search_ref.upper() in r["descripcion"].upper()]

    total_refs        = len(references)
    classified_refs   = sum(1 for r in references if r.get("category_id"))
    unclassified_refs = total_refs - classified_refs

    total_ref_pages = max(1, (len(refs_filtered) - 1) // PAGE_SIZE_REF + 1)
    ref_page = max(1, min(ref_page, total_ref_pages))
    refs_page = refs_filtered[(ref_page - 1) * PAGE_SIZE_REF: ref_page * PAGE_SIZE_REF]

    cat_map = {c["id"]: c for c in categories}

    return render_template(
        "categorias.html",
        categories=categories,
        refs_page=refs_page,
        cat_map=cat_map,
        total_refs=total_refs,
        classified_refs=classified_refs,
        unclassified_refs=unclassified_refs,
        ref_page=ref_page,
        total_ref_pages=total_ref_pages,
        refs_total_filtered=len(refs_filtered),
        search_ref=search_ref,
        only_unclassified=only_unclassified,
    )


@app.route("/categorias/new", methods=["POST"])
def categorias_new():
    name  = request.form.get("name", "").strip()
    color = request.form.get("color", PRIMARY)
    if name:
        try:
            api.create_category(name, color)
            flash(f"Categoría '{name}' creada.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
    return redirect(url_for("categorias"))


@app.route("/categorias/<int:cat_id>/edit", methods=["POST"])
def categorias_edit(cat_id: int):
    name  = request.form.get("name", "").strip() or None
    color = request.form.get("color", "").strip() or None
    try:
        api.update_category(cat_id, name=name, color=color)
        flash("Categoría actualizada.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("categorias"))


@app.route("/categorias/<int:cat_id>/delete", methods=["POST"])
def categorias_delete(cat_id: int):
    try:
        api.delete_category(cat_id)
        flash("Categoría eliminada.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("categorias"))


@app.route("/categorias/references/<int:ref_id>/assign", methods=["POST"])
def categorias_assign(ref_id: int):
    raw = request.form.get("category_id", "")
    cat_id = int(raw) if raw.isdigit() else None
    try:
        api.assign_reference_category(ref_id, cat_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
