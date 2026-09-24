"""Deterministic local demo store for the AirIndex public portal.

The production path can later swap this store for PostgreSQL without changing
the public API contract. SQLite keeps the full demo backend runnable without
Docker while preserving real reads/writes during local development.
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEMO_JSON = ROOT / "data" / "demo" / "portal_demo.json"
LOCAL_DB = ROOT / "data" / "runtime" / "airindex_demo.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sources (
    name TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    status TEXT NOT NULL,
    official INTEGER NOT NULL DEFAULT 0,
    url TEXT,
    role TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS routes (
    route TEXT PRIMARY KEY,
    weight REAL NOT NULL,
    index_value REAL NOT NULL,
    change_percent REAL NOT NULL,
    avg_fare REAL NOT NULL,
    min_fare REAL NOT NULL,
    p90_fare REAL NOT NULL,
    observations INTEGER NOT NULL,
    quality REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS airlines (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    index_value REAL NOT NULL,
    change_percent REAL NOT NULL,
    avg_fare REAL NOT NULL,
    observations INTEGER NOT NULL,
    quality REAL NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS airports (
    code TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    index_value REAL NOT NULL,
    change_percent REAL NOT NULL,
    avg_fare REAL NOT NULL,
    observations INTEGER NOT NULL,
    quality REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route TEXT NOT NULL,
    carrier_code TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    travel_date TEXT NOT NULL,
    advance_days INTEGER NOT NULL,
    total_fare REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    source TEXT NOT NULL,
    quality_score REAL NOT NULL,
    quality_status TEXT NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_observations_route ON observations(route);
CREATE INDEX IF NOT EXISTS idx_observations_carrier ON observations(carrier_code);
CREATE INDEX IF NOT EXISTS idx_observations_observed ON observations(observed_at);
CREATE INDEX IF NOT EXISTS idx_observations_travel ON observations(travel_date);

CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_date TEXT NOT NULL,
    title TEXT NOT NULL,
    publication_type TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_date TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_index (
    index_date TEXT PRIMARY KEY,
    index_value REAL NOT NULL,
    change_percent REAL NOT NULL,
    observation_count INTEGER NOT NULL
);
"""


class DemoStore:
    """Small database-backed store used by the public demo and local development."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path:
            self.path = Path(db_path)
        elif os.getenv("VERCEL"):
            self.path = Path("/tmp/airindex_demo.sqlite3")
        else:
            self.path = LOCAL_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def ensure_seeded(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)
            seeded = connection.execute(
                "SELECT value FROM meta WHERE key = 'seed_version'"
            ).fetchone()
            if seeded:
                return
            payload = json.loads(DEMO_JSON.read_text(encoding="utf-8"))
            self._seed(connection, payload)
            connection.execute(
                "INSERT INTO meta(key, value) VALUES('seed_version', 'portal-demo-v2')"
            )
            connection.commit()

    def _seed(self, connection: sqlite3.Connection, payload: dict[str, Any]) -> None:
        for item in payload["source_registry"]:
            connection.execute(
                """
                INSERT INTO sources(name, source_type, status, official, url, role, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["name"],
                    item["type"],
                    item["status"],
                    int(bool(item.get("official"))),
                    item.get("url"),
                    item.get("role"),
                    item.get("note"),
                ),
            )

        for item in payload["routes"]:
            connection.execute(
                """
                INSERT INTO routes(
                    route, weight, index_value, change_percent, avg_fare,
                    min_fare, p90_fare, observations, quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["route"],
                    item["weight"],
                    item["index"],
                    item["change_percent"],
                    item["avg_fare"],
                    item["min_fare"],
                    item["p90_fare"],
                    0,
                    item["quality"],
                ),
            )

        for item in payload["airlines"]:
            connection.execute(
                """
                INSERT INTO airlines(
                    code, name, index_value, change_percent, avg_fare,
                    observations, quality, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["code"],
                    item["name"],
                    item["index"],
                    item["change_percent"],
                    item["avg_fare"],
                    0,
                    item["quality"],
                    item["status"],
                ),
            )

        for item in payload["airports"]:
            connection.execute(
                """
                INSERT INTO airports(
                    code, city, state, index_value, change_percent,
                    avg_fare, observations, quality
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["code"],
                    item["city"],
                    item["state"],
                    item["index"],
                    item["change_percent"],
                    item["avg_fare"],
                    0,
                    item["quality"],
                ),
            )

        for item in payload["releases"]:
            connection.execute(
                """
                INSERT INTO releases(release_date, title, publication_type, status)
                VALUES (?, ?, ?, ?)
                """,
                (item["date"], item["title"], item["type"], item["status"]),
            )

        for item in payload["alerts"]:
            connection.execute(
                """
                INSERT INTO alerts(alert_date, severity, title, text)
                VALUES (?, ?, ?, ?)
                """,
                (item["date"], item["severity"], item["title"], item["text"]),
            )

        self._seed_observations(connection, payload)
        self._seed_daily_series(connection, payload)
        self._refresh_aggregates(connection)

    def _seed_observations(
        self,
        connection: sqlite3.Connection,
        payload: dict[str, Any],
    ) -> None:
        rng = random.Random(20260925)
        base_date = date(2026, 8, 27)
        route_rows = payload["routes"]
        airline_rows = payload["airlines"][:6]

        carriers = [
            (item["code"], 0.31 if item["code"] == "6E" else 0.18)
            for item in airline_rows
        ]
        carrier_codes = [item[0] for item in carriers]
        carrier_weights = [item[1] for item in carriers]

        observations: list[tuple[Any, ...]] = []
        for day_index in range(30):
            observed_date = base_date + timedelta(days=day_index)
            observed_at = datetime(
                observed_date.year,
                observed_date.month,
                observed_date.day,
                8,
                30,
                tzinfo=UTC,
            )
            for route in route_rows:
                route_index = float(route["index"])
                avg_fare = float(route["avg_fare"])
                for sample in range(50):
                    advance_days = [1, 3, 7, 15, 30, 45][
                        (sample + day_index) % 6
                    ]
                    carrier = rng.choices(carrier_codes, weights=carrier_weights, k=1)[0]
                    seasonal = 1 + 0.025 * random.Random(
                        day_index * 1000 + sample
                    ).uniform(-1, 1)
                    carrier_effect = 1 + (
                        {
                            "6E": -0.015,
                            "AI": 0.025,
                            "IX": 0.008,
                            "QP": 0.045,
                            "SG": 0.03,
                            "9I": -0.02,
                        }.get(carrier, 0.0)
                    )
                    horizon_effect = 1 + (0.018 if advance_days <= 3 else 0.0)
                    fare = max(
                        1800,
                        avg_fare
                        * (route_index / 100)
                        * seasonal
                        * carrier_effect
                        * horizon_effect
                        * rng.uniform(0.91, 1.09),
                    )
                    quality = max(0.72, min(0.995, float(route["quality"]) / 100 + rng.uniform(-0.025, 0.02)))
                    anomaly = int(fare > avg_fare * 1.28 or fare < avg_fare * 0.72)
                    observations.append(
                        (
                            route["route"],
                            carrier,
                            observed_at.isoformat(),
                            (observed_date + timedelta(days=advance_days)).isoformat(),
                            advance_days,
                            round(fare, 2),
                            "INR",
                            "synthetic-demo-replay",
                            round(quality, 4),
                            "flagged" if anomaly else "accepted",
                            anomaly,
                        )
                    )

        connection.executemany(
            """
            INSERT INTO observations(
                route, carrier_code, observed_at, travel_date, advance_days,
                total_fare, currency, source, quality_score, quality_status, anomaly_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            observations,
        )

    def _seed_daily_series(
        self,
        connection: sqlite3.Connection,
        payload: dict[str, Any],
    ) -> None:
        daily_counts = {
            row["date"]: 0
            for row in payload["daily_series"]
        }
        for value in daily_counts:
            daily_counts[value] = 600

        connection.executemany(
            """
            INSERT INTO daily_index(index_date, index_value, change_percent, observation_count)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    row["date"],
                    row["index"],
                    row["change_percent"],
                    daily_counts.get(row["date"], 600),
                )
                for row in payload["daily_series"]
            ],
        )

    def _refresh_aggregates(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            UPDATE routes
            SET observations = (
                SELECT COUNT(*) FROM observations o WHERE o.route = routes.route
            ),
            avg_fare = COALESCE((
                SELECT AVG(o.total_fare) FROM observations o WHERE o.route = routes.route
            ), avg_fare),
            min_fare = COALESCE((
                SELECT MIN(o.total_fare) FROM observations o WHERE o.route = routes.route
            ), min_fare),
            p90_fare = COALESCE((
                SELECT MAX(o.total_fare) FROM observations o WHERE o.route = routes.route
            ), p90_fare),
            quality = COALESCE((
                SELECT AVG(o.quality_score) * 100 FROM observations o WHERE o.route = routes.route
            ), quality)
            """
        )
        connection.execute(
            """
            UPDATE airlines
            SET observations = (
                SELECT COUNT(*) FROM observations o WHERE o.carrier_code = airlines.code
            ),
            avg_fare = COALESCE((
                SELECT AVG(o.total_fare) FROM observations o WHERE o.carrier_code = airlines.code
            ), avg_fare),
            quality = COALESCE((
                SELECT AVG(o.quality_score) * 100 FROM observations o WHERE o.carrier_code = airlines.code
            ), quality)
            """
        )

        for airport in connection.execute("SELECT code FROM airports").fetchall():
            code = str(airport["code"])
            count = connection.execute(
                """
                SELECT COUNT(*) FROM observations
                WHERE substr(route, 1, 3) = ? OR substr(route, 5, 3) = ?
                """,
                (code, code),
            ).fetchone()[0]
            connection.execute(
                "UPDATE airports SET observations = ? WHERE code = ?",
                (int(count), code),
            )

    def summary(self) -> dict[str, Any]:
        self.ensure_seeded()
        with self._connect() as c:
            total = int(c.execute("SELECT COUNT(*) FROM observations").fetchone()[0])
            accepted = int(
                c.execute(
                    "SELECT COUNT(*) FROM observations WHERE quality_status = 'accepted'"
                ).fetchone()[0]
            )
            anomalies = int(c.execute("SELECT COUNT(*) FROM observations WHERE anomaly_flag = 1").fetchone()[0])
            quality = float(c.execute("SELECT AVG(quality_score) FROM observations").fetchone()[0] or 0)
            duplicate_like = int(
                c.execute(
                    """
                    SELECT COUNT(*) FROM (
                        SELECT route, carrier_code, travel_date, total_fare, COUNT(*) AS n
                        FROM observations GROUP BY route, carrier_code, travel_date, total_fare
                        HAVING n > 1
                    )
                    """
                ).fetchone()[0]
            )
            return {
                "observation_count": total,
                "accepted_count": accepted,
                "rejected_count": total - accepted,
                "anomaly_count": anomalies,
                "anomaly_rate_pct": round(anomalies / total * 100, 2) if total else 0,
                "quality_avg": round(quality, 4),
                "duplicate_groups": duplicate_like,
                "route_count": int(c.execute("SELECT COUNT(*) FROM routes").fetchone()[0]),
                "airline_count": int(c.execute("SELECT COUNT(*) FROM airlines").fetchone()[0]),
                "airport_count": int(c.execute("SELECT COUNT(*) FROM airports").fetchone()[0]),
            }

    def all_rows(self, table: str, search: str | None = None) -> list[dict[str, Any]]:
        self.ensure_seeded()
        allowed = {"routes", "airlines", "airports", "sources", "releases", "alerts", "daily_index"}
        if table not in allowed:
            raise ValueError("Unsupported table")
        with self._connect() as c:
            if search and table == "routes":
                rows = c.execute(
                    "SELECT * FROM routes WHERE route LIKE ? ORDER BY index_value DESC",
                    (f"%{search.upper()}%",),
                ).fetchall()
            elif search and table == "airlines":
                rows = c.execute(
                    "SELECT * FROM airlines WHERE name LIKE ? OR code LIKE ? ORDER BY index_value DESC",
                    (f"%{search}%", f"%{search.upper()}%"),
                ).fetchall()
            else:
                order = {
                    "routes": "index_value DESC",
                    "airlines": "index_value DESC",
                    "airports": "index_value DESC",
                    "sources": "name ASC",
                    "releases": "id DESC",
                    "alerts": "id DESC",
                    "daily_index": "index_date ASC",
                }[table]
                rows = c.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
            return [dict(row) for row in rows]

    def add_observations(self, rows: Iterable[dict[str, Any]]) -> int:
        self.ensure_seeded()
        inserted = 0
        with self._connect() as c:
            for row in rows:
                fare = float(row["total_fare"])
                quality = 0.96
                anomaly = 0
                if fare <= 0:
                    raise ValueError("total_fare must be positive")
                if fare > 1_000_000:
                    raise ValueError("total_fare exceeds configured safety bound")
                connection_source = str(row["source"])
                observed_at = str(row["observed_at"])
                travel_date = str(row["travel_date"])
                advance_days = int(row["advance_days"])
                if not 1 <= advance_days <= 365:
                    raise ValueError("advance_days must be between 1 and 365")
                c.execute(
                    """
                    INSERT INTO observations(
                        route, carrier_code, observed_at, travel_date, advance_days,
                        total_fare, currency, source, quality_score, quality_status, anomaly_flag
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(row["route"]).upper(),
                        str(row["carrier_code"]).upper(),
                        observed_at,
                        travel_date,
                        advance_days,
                        fare,
                        "INR",
                        connection_source,
                        quality,
                        "accepted",
                        anomaly,
                    ),
                )
                inserted += 1
            self._refresh_aggregates(c)
            c.commit()
        return inserted

    def portal_payload(self) -> dict[str, Any]:
        self.ensure_seeded()
        payload = json.loads(DEMO_JSON.read_text(encoding="utf-8"))
        stats = self.summary()
        payload["data_mode"] = "DEMO DATABASE"
        payload["storage_mode"] = "SQLite demo backend"
        payload["generated_observations"] = stats["observation_count"]
        payload["observation_count"] = stats["observation_count"]
        payload["accepted_count"] = stats["accepted_count"]
        payload["rejected_count"] = stats["rejected_count"]
        payload["anomaly_rate_pct"] = stats["anomaly_rate_pct"]
        payload["quality_avg"] = stats["quality_avg"]
        payload["duplicate_groups"] = stats["duplicate_groups"]
        payload["distinct_routes"] = stats["route_count"]
        payload["distinct_airports"] = stats["airport_count"]
        payload["distinct_carriers"] = stats["airline_count"]
        payload["routes"] = self.all_rows("routes")
        payload["airlines"] = self.all_rows("airlines")
        payload["airports"] = self.all_rows("airports")
        payload["source_registry"] = self.all_rows("sources")
        payload["releases"] = [
            {
                "date": row["release_date"],
                "title": row["title"],
                "type": row["publication_type"],
                "status": row["status"],
            }
            for row in self.all_rows("releases")
        ]
        payload["alerts"] = [
            {
                "date": row["alert_date"],
                "severity": row["severity"],
                "title": row["title"],
                "text": row["text"],
            }
            for row in self.all_rows("alerts")
        ]
        payload["daily_series"] = self.all_rows("daily_index")
        return payload

    def observation_detail(
        self,
        route: str | None = None,
        carrier: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self.ensure_seeded()
        filters = []
        values: list[Any] = []
        if route:
            filters.append("route = ?")
            values.append(route.upper())
        if carrier:
            filters.append("carrier_code = ?")
            values.append(carrier.upper())
        where = " WHERE " + " AND ".join(filters) if filters else ""
        values.append(min(max(limit, 1), 500))
        with self._connect() as c:
            rows = c.execute(
                f"""
                SELECT id, route, carrier_code, observed_at, travel_date,
                       advance_days, total_fare, currency, source,
                       quality_score, quality_status, anomaly_flag
                FROM observations
                {where}
                ORDER BY observed_at DESC, id DESC
                LIMIT ?
                """,
                values,
            ).fetchall()
            return [dict(row) for row in rows]
