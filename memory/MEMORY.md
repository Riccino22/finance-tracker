# Dashboard Banco – Project Memory

## Stack
- Streamlit (port 8501) + FastAPI (port 8000) + MCP (port 8002) + PostgreSQL (port 5432)
- Docker Compose: services = db, api, app, mcp

## Key file paths
- `api/pdf_parser.py` – parses Itaú Uruguay PDF statements
- `api/routers/analytics.py` – all 6 chart data endpoints
- `app/utils/api_client.py` – Streamlit → API HTTP calls (httpx)
- `app/utils/styles.py` – CSS, kpi_card(), fmt_money(), chart_layout()
- `mcp/server.py` – FastMCP server with tools + prompts + resources

## DB schema (PostgreSQL)
- categories(id, name, color)
- statements(id, account_name, year, month, fecha_estado, saldo_apertura, saldo_cierre, saldo_promedio, filename) UNIQUE(year, month)
- references_catalog(id, descripcion UNIQUE, category_id→categories)
- transactions(id, statement_id→statements, fecha, fecha_completa DATE, tipo, descripcion, reference_id→references_catalog, debito, credito, saldo)

## Conventions
- Money format: `$ X.XXX,XX` (Spanish/Uruguayan, via fmt_money())
- Month abbr (Spanish): ENE,FEB,MAR,ABR,MAY,JUN,JUL,AGO,SET,OCT,NOV,DIC
- Primary color: #00c795 (Itaú green)
- Heatmap DOW: PostgreSQL 0=Sunday

## MCP prompts (slash commands)
- analizar_mes(year, month)
- comparar_anios(year1, year2)
- donde_gasto_mas(year, month) — includes elicitation if no period given

## User preferences
- Spanish language throughout
- Dark theme UI
- Itaú Uruguay bank format (PDFs)
