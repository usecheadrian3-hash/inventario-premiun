# -*- coding: utf-8 -*-
"""Capa de datos SQLite compatible con la interfaz mysql-connector que usa app.py."""
import os
import sqlite3

DB_FILE = os.environ.get("SQLITE_DB") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "inventario.db"
)

_TRANSLATIONS = [
    ("DATE_SUB(NOW(), INTERVAL 1 HOUR)", "datetime('now','-1 hour')"),
    ("DATE_SUB(NOW(), INTERVAL 30 DAY)", "datetime('now','-30 days')"),
    ("DATE_SUB(NOW(), INTERVAL 7 DAY)", "datetime('now','-7 days')"),
    ("DATE_SUB(NOW(), INTERVAL 1 DAY)", "datetime('now','-1 day')"),
    ("DATE_FORMAT(fecha, '%%Y-%%m')", "strftime('%Y-%m', fecha)"),
    ("CURDATE()", "date('now')"),
    ("NOW()", "CURRENT_TIMESTAMP"),
    ("VERSION()", "sqlite_version()"),
]


def _translate(sql):
    for a, b in _TRANSLATIONS:
        sql = sql.replace(a, b)
    return sql.replace("%s", "?")


_conn = None


def _conectar():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        _conn.isolation_level = None
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout=5000")
    return _conn


class _Cursor:
    def __init__(self, conn):
        self._c = conn.cursor()

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        self._c.execute(_translate(sql), params)
        return self

    def executemany(self, sql, seq):
        self._c.executemany(_translate(sql), seq)
        return self

    def fetchone(self):
        return self._c.fetchone()

    def fetchall(self):
        return self._c.fetchall()

    @property
    def lastrowid(self):
        return self._c.lastrowid

    @property
    def rowcount(self):
        return self._c.rowcount

    def close(self):
        self._c.close()


class _ModuleCursor:
    def __init__(self):
        self._last = None

    def execute(self, sql, params=None):
        self._last = _Cursor(_conectar())
        return self._last.execute(sql, params)

    def executemany(self, sql, seq):
        self._last = _Cursor(_conectar())
        return self._last.executemany(sql, seq)

    def fetchone(self):
        return self._last.fetchone()

    def fetchall(self):
        return self._last.fetchall()

    @property
    def lastrowid(self):
        return self._last.lastrowid

    @property
    def rowcount(self):
        return self._last.rowcount


class _Conexion:
    def commit(self):
        _conectar().commit()

    def rollback(self):
        _conectar().rollback()

    def close(self):
        _conectar().close()


conexion = _Conexion()
cursor = _ModuleCursor()
