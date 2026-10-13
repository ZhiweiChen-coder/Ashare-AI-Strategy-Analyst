"""The shared workspace watchlist used by the sidebar and agent tools."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ashare.stock_pool import normalize_stock_code
from api.supabase_store import SupabaseWorkspaceStore, SupabaseStoreError


MAX_ITEMS = 200


def clean_item(code: str, name: str = "") -> dict[str, str]:
    normalized = normalize_stock_code(code.strip())
    if not normalized or len(normalized) > 40:
        raise ValueError("A valid stock code is required.")
    return {"code": normalized, "name": (name.strip() or normalized)[:120]}


class LocalWatchlistStore:
    """One local workspace, independent of chat sessions. Writes are atomic."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS watchlist_state (id INTEGER PRIMARY KEY CHECK(id=1))")
            db.execute("CREATE TABLE IF NOT EXISTS watchlist_items (code TEXT PRIMARY KEY COLLATE NOCASE, name TEXT NOT NULL, position INTEGER NOT NULL)")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    @staticmethod
    def _snapshot(db):
        return {"initialized": db.execute("SELECT 1 FROM watchlist_state").fetchone() is not None,
                "items": [{"code": code, "name": name} for code, name in db.execute("SELECT code, name FROM watchlist_items ORDER BY position, code")]}

    def get(self):
        with self._connect() as db:
            return self._snapshot(db)

    def initialize(self, items):
        """Import an existing browser list once; an empty saved list stays empty."""
        if len(items) > MAX_ITEMS:
            raise ValueError(f"Watchlists support up to {MAX_ITEMS} stocks.")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if not self._snapshot(db)["initialized"]:
                for index, item in enumerate(items):
                    row = clean_item(item["code"], item.get("name", ""))
                    db.execute("INSERT OR IGNORE INTO watchlist_items VALUES (?, ?, ?)", (row["code"], row["name"], index))
                db.execute("INSERT INTO watchlist_state VALUES (1)")
            return self._snapshot(db)

    def mutate(self, action, code, name=""):
        row = clean_item(code, name)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            found = db.execute("SELECT 1 FROM watchlist_items WHERE code = ?", (row["code"],)).fetchone() is not None
            if action == "add":
                if not found:
                    if db.execute("SELECT COUNT(*) FROM watchlist_items").fetchone()[0] >= MAX_ITEMS:
                        raise ValueError(f"Watchlist is full ({MAX_ITEMS} stocks). Remove a stock first.")
                    db.execute("INSERT INTO watchlist_items VALUES (?, ?, COALESCE((SELECT MIN(position)-1 FROM watchlist_items), 0))", (row["code"], row["name"]))
            elif action == "remove":
                db.execute("DELETE FROM watchlist_items WHERE code = ?", (row["code"],))
            else:
                raise ValueError("Use add or remove.")
            db.execute("INSERT OR IGNORE INTO watchlist_state VALUES (1)")
            return {**self._snapshot(db), "action": action, "stock_code": row["code"], "stock_name": row["name"], "changed": not found if action == "add" else found}


class CloudWatchlistStore:
    """Use the existing authenticated Supabase tables and owner RLS policies."""

    def __init__(self, config, user):
        self.client = SupabaseWorkspaceStore(config, user.access_token).client
        self.user_id = str(user.id)

    def _list(self, create=False):
        rows = self.client.select("watchlists", filters={"user_id": self.user_id}, order="is_default.desc,created_at.asc", limit=1)
        if rows or not create:
            return rows[0] if rows else None
        try:
            return self.client.upsert("watchlists", {"user_id": self.user_id, "name": "Research", "is_default": True}, on_conflict="user_id,name")
        except SupabaseStoreError:
            rows = self.client.select("watchlists", filters={"user_id": self.user_id}, order="is_default.desc,created_at.asc", limit=1)
            if rows:
                return rows[0]
            raise

    def get(self):
        watchlist = self._list()
        rows = self.client.select("watchlist_items", filters={"user_id": self.user_id, "watchlist_id": watchlist["id"]}, order="sort_order.asc,created_at.asc") if watchlist else []
        return {"initialized": True, "items": [{"code": r["symbol"], "name": r.get("display_name") or r["symbol"]} for r in rows]}

    def initialize(self, items):
        # Never copy anonymous browser holdings into an authenticated account.
        return self.get()

    def mutate(self, action, code, name=""):
        row = clean_item(code, name)
        watchlist = self._list(create=action == "add")
        before = self.get()["items"]
        found = any(r["code"].upper() == row["code"].upper() for r in before)
        if action == "add" and not found:
            if len(before) >= MAX_ITEMS:
                raise ValueError(f"Watchlist is full ({MAX_ITEMS} stocks). Remove a stock first.")
            self.client.upsert("watchlist_items", {"user_id": self.user_id, "watchlist_id": watchlist["id"], "symbol": row["code"], "display_name": row["name"], "sort_order": -len(before)-1}, on_conflict="watchlist_id,symbol")
        elif action == "remove" and found:
            self.client.request("DELETE", "watchlist_items", params={"user_id": f"eq.{self.user_id}", "watchlist_id": f"eq.{watchlist['id']}", "symbol": f"eq.{row['code']}"})
        elif action not in {"add", "remove"}:
            raise ValueError("Use add or remove.")
        return {**self.get(), "action": action, "stock_code": row["code"], "stock_name": row["name"], "changed": not found if action == "add" else found}
