import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import json

DB_PATH = "missions.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS missions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT,
            user_request     TEXT NOT NULL,
            mission_spec_json TEXT NOT NULL,   -- full JSON spec as text
            created_at       TEXT NOT NULL,
            status           TEXT NOT NULL
        );
        """
    )

    conn.commit()
    conn.close()


def create_mission_with_spec(
    user_request: str,
    mission_spec: Dict[str, Any],
    name: Optional[str] = None,
    status: str = "spec_generated",
) -> int:
    """Insert a mission row with full JSON spec; return mission_id."""
    conn = get_connection()
    cur = conn.cursor()

    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    mission_spec_json = json.dumps(mission_spec)

    cur.execute(
        """
        INSERT INTO missions (name, user_request, mission_spec_json, created_at, status)
        VALUES (?, ?, ?, ?, ?);
        """,
        (name, user_request, mission_spec_json, created_at, status),
    )

    mission_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mission_id


def get_mission_by_id(mission_id: int) -> Optional[Dict[str, Any]]:
    """Fetch mission row + parse JSON spec."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM missions WHERE id = ?;", (mission_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    mission_spec = json.loads(row["mission_spec_json"])

    return {
        "id": row["id"],
        "name": row["name"],
        "user_request": row["user_request"],
        "created_at": row["created_at"],
        "status": row["status"],
        "mission_spec": mission_spec,
    }


def list_missions() -> list[Dict[str, Any]]:
    """Lightweight list (no big JSON)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, user_request, created_at, status
        FROM missions
        ORDER BY id DESC;
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "user_request": row["user_request"],
            "created_at": row["created_at"],
            "status": row["status"],
        }
        for row in rows
    ]
