import sqlite3
import os
from datetime import datetime

from openpyxl import Workbook

DB_DIR = os.environ.get("DATA_DIR", ".")
DB_PATH = os.path.join(DB_DIR, "evaluations.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT    NOT NULL,
            nickname        TEXT    NOT NULL,
            prompt          TEXT    NOT NULL,
            left_model_name TEXT    NOT NULL,
            left_model_endpoint TEXT NOT NULL,
            left_response   TEXT    NOT NULL,
            left_comment    TEXT    NOT NULL DEFAULT '',
            left_grade      INTEGER NOT NULL,
            right_model_name TEXT   NOT NULL,
            right_provider  TEXT    NOT NULL,
            right_response  TEXT    NOT NULL,
            right_comment   TEXT    NOT NULL DEFAULT '',
            right_grade     INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_evaluation(
    nickname: str,
    prompt: str,
    left_model_name: str,
    left_model_endpoint: str,
    left_response: str,
    left_comment: str,
    left_grade: int,
    right_model_name: str,
    right_provider: str,
    right_response: str,
    right_comment: str,
    right_grade: int,
) -> None:
    conn = _get_conn()
    conn.execute(
        """
        INSERT INTO evaluations (
            timestamp, nickname, prompt,
            left_model_name, left_model_endpoint, left_response, left_comment, left_grade,
            right_model_name, right_provider, right_response, right_comment, right_grade
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            nickname,
            prompt,
            left_model_name,
            left_model_endpoint,
            left_response,
            left_comment,
            left_grade,
            right_model_name,
            right_provider,
            right_response,
            right_comment,
            right_grade,
        ),
    )
    conn.commit()
    conn.close()


def export_to_excel(filepath: str) -> str:
    conn = _get_conn()
    cursor = conn.execute("SELECT * FROM evaluations ORDER BY id")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Evaluations"
    ws.append(columns)
    for row in rows:
        ws.append(list(row))
    wb.save(filepath)
    return filepath
