"""HTTP client wrapper for the banking API."""
from __future__ import annotations
import os
from typing import Optional, Any

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT = 30.0


def _get(path: str, params: dict | None = None) -> Any:
    r = httpx.get(f"{API_URL}{path}", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path: str, **kwargs) -> Any:
    r = httpx.post(f"{API_URL}{path}", timeout=TIMEOUT, **kwargs)
    r.raise_for_status()
    return r.json()


def _put(path: str, json: dict) -> Any:
    r = httpx.put(f"{API_URL}{path}", json=json, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _delete(path: str) -> None:
    r = httpx.delete(f"{API_URL}{path}", timeout=TIMEOUT)
    r.raise_for_status()


# ── Statements ────────────────────────────────────────────────────────────────

def get_statements() -> list[dict]:
    return _get("/statements/")


def get_statement(statement_id: int) -> dict:
    return _get(f"/statements/{statement_id}")


def upload_statement(filename: str, content: bytes) -> dict:
    return _post(
        "/statements/upload",
        files={"file": (filename, content, "application/pdf")},
    )


def delete_statement(statement_id: int) -> None:
    _delete(f"/statements/{statement_id}")


# ── Transactions ──────────────────────────────────────────────────────────────

def get_transactions(
    year: Optional[int] = None,
    month: Optional[int] = None,
    category_id: Optional[int] = None,
    tipo: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 2000,
) -> list[dict]:
    params = {"limit": limit}
    if year:        params["year"]        = year
    if month:       params["month"]       = month
    if category_id: params["category_id"] = category_id
    if tipo:        params["tipo"]        = tipo
    if search:      params["search"]      = search
    return _get("/transactions/", params=params)


# ── Categories ────────────────────────────────────────────────────────────────

def get_categories() -> list[dict]:
    return _get("/categories/")


def create_category(name: str, color: str = "#00c795") -> dict:
    return _post("/categories/", json={"name": name, "color": color})


def update_category(category_id: int, name: str | None = None, color: str | None = None) -> dict:
    payload = {}
    if name:  payload["name"]  = name
    if color: payload["color"] = color
    return _put(f"/categories/{category_id}", json=payload)


def delete_category(category_id: int) -> None:
    _delete(f"/categories/{category_id}")


def get_references(unclassified_only: bool = False) -> list[dict]:
    return _get("/categories/references", params={"unclassified_only": unclassified_only})


def assign_reference_category(reference_id: int, category_id: Optional[int]) -> dict:
    return _put(f"/categories/references/{reference_id}", json={"category_id": category_id})


# ── Analytics ─────────────────────────────────────────────────────────────────

def get_balance_evolution() -> list[dict]:
    return _get("/analytics/balance-evolution")


def get_yearly_credits_avg() -> list[dict]:
    return _get("/analytics/yearly-credits-avg")


def get_category_breakdown(year: Optional[int] = None, month: Optional[int] = None) -> list[dict]:
    params = {}
    if year:  params["year"]  = year
    if month: params["month"] = month
    return _get("/analytics/category-breakdown", params=params)


def get_avg_vs_closing() -> list[dict]:
    return _get("/analytics/avg-vs-closing")


def get_heatmap(year: Optional[int] = None, month: Optional[int] = None) -> list[dict]:
    params = {}
    if year:  params["year"]  = year
    if month: params["month"] = month
    return _get("/analytics/heatmap", params=params)


def get_projection(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    params = {}
    if year:  params["year"]  = year
    if month: params["month"] = month
    return _get("/analytics/projection", params=params)


def health() -> bool:
    try:
        r = httpx.get(f"{API_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False
