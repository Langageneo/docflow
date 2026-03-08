"""
Base de données SQLite pour DocFlow
"""

import sqlite3
import os
from datetime import datetime
from app.config import Config

DB_PATH = Config.DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL DEFAULT 'Utilisateur',
        email TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        language TEXT DEFAULT 'fr'
    )
    """)

    c.execute("SELECT COUNT(*) FROM users WHERE id = 1")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (id, name, email) VALUES (1, 'Utilisateur Demo', 'demo@docflow.fr')")

    c.execute("""
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        original_name TEXT NOT NULL,
        stored_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        row_count INTEGER DEFAULT 0,
        col_count INTEGER DEFAULT 0,
        uploaded_at TEXT DEFAULT (datetime('now'))
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        title TEXT NOT NULL,
        report_type TEXT NOT NULL,
        source_file_id INTEGER,
        file_path TEXT,
        template_type TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        file_id INTEGER NOT NULL DEFAULT 1,
        analysis_type TEXT DEFAULT 'full',
        results_json TEXT,
        insights_text TEXT,
        chart_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS conversions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        source_file TEXT NOT NULL,
        target_file TEXT,
        from_format TEXT NOT NULL,
        to_format TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)

    conn.commit()
    conn.close()


def save_file_record(user_id, original_name, stored_name, file_path, file_type, file_size=0, row_count=0, col_count=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO uploaded_files (user_id, original_name, stored_name, file_path, file_type, file_size, row_count, col_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, original_name, stored_name, file_path, file_type, file_size, row_count, col_count))
    file_id = c.lastrowid
    conn.commit()
    conn.close()
    return file_id


def get_user_files(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM uploaded_files WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def delete_file_record(file_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("SELECT file_path FROM uploaded_files WHERE id = ? AND user_id = ?", (file_id, user_id))
        row = c.fetchone()
        if row:
            file_path = row["file_path"]
            if os.path.exists(file_path):
                os.remove(file_path)
            c.execute("DELETE FROM analyses WHERE file_id = ?", (file_id,))
            c.execute("DELETE FROM reports WHERE source_file_id = ?", (file_id,))
            c.execute("DELETE FROM uploaded_files WHERE id = ?", (file_id,))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_file_by_id(file_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM uploaded_files WHERE id = ?", (file_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def save_report(user_id, title, report_type, file_path, source_file_id=None, template_type=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO reports (user_id, title, report_type, source_file_id, file_path, template_type)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, title, report_type, source_file_id, file_path, template_type))
    report_id = c.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_user_reports(user_id, limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM reports WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def save_analysis(user_id, file_id, results_json, insights_text="", chart_count=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO analyses (user_id, file_id, results_json, insights_text, chart_count)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, file_id, results_json, insights_text, chart_count))
    analysis_id = c.lastrowid
    conn.commit()
    conn.close()
    return analysis_id


def get_user_analyses(user_id, limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def save_conversion(user_id, source_file, from_format, to_format, target_file=None, status="done"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO conversions (user_id, source_file, target_file, from_format, to_format, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, source_file, target_file, from_format, to_format, status))
    conv_id = c.lastrowid
    conn.commit()
    conn.close()
    return conv_id


def get_user_stats(user_id):
    conn = get_connection()
    c = conn.cursor()
    stats = {}
    c.execute("SELECT COUNT(*) as n FROM uploaded_files WHERE user_id = ?", (user_id,))
    stats["files"] = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM reports WHERE user_id = ?", (user_id,))
    stats["reports"] = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM analyses WHERE user_id = ?", (user_id,))
    stats["analyses"] = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM conversions WHERE user_id = ?", (user_id,))
    stats["conversions"] = c.fetchone()["n"]
    conn.close()
    return stats
