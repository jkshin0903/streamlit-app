"""SSH tunnel + MariaDB engine for mng_db."""

from __future__ import annotations

import os
from configparser import ConfigParser
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sshtunnel import SSHTunnelForwarder

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "db.ini"


class DbConfigError(Exception):
    pass


def _read_ini() -> ConfigParser:
    if not CONFIG_PATH.is_file():
        raise DbConfigError(
            f"Missing {CONFIG_PATH.name}. Copy db.ini.example to db.ini and set credentials."
        )
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH, encoding="utf-8")
    return cfg


def load_db_config() -> dict[str, Any]:
    """Load SSH/DB settings from environment variables or db.ini."""
    env_host = os.environ.get("DB_SSH_HOST")
    if env_host:
        return {
            "ssh_host": env_host,
            "ssh_port": int(os.environ.get("DB_SSH_PORT", "22")),
            "ssh_username": os.environ["DB_SSH_USER"],
            "ssh_password": os.environ.get("DB_SSH_PASSWORD", ""),
            "db_user": os.environ["DB_USER"],
            "db_password": os.environ.get("DB_PASSWORD", ""),
            "db_name": os.environ.get("DB_NAME", "mng_db"),
            "remote_host": os.environ.get("DB_REMOTE_HOST", "127.0.0.1"),
            "remote_port": int(os.environ.get("DB_REMOTE_PORT", "3306")),
        }

    cfg = _read_ini()
    return {
        "ssh_host": cfg.get("ssh", "host"),
        "ssh_port": cfg.getint("ssh", "port", fallback=22),
        "ssh_username": cfg.get("ssh", "username"),
        "ssh_password": cfg.get("ssh", "password"),
        "db_user": cfg.get("database", "user"),
        "db_password": cfg.get("database", "password"),
        "db_name": cfg.get("database", "name", fallback="mng_db"),
        "remote_host": cfg.get("database", "remote_host", fallback="127.0.0.1"),
        "remote_port": cfg.getint("database", "remote_port", fallback=3306),
    }


def config_cache_key() -> str:
    if os.environ.get("DB_SSH_HOST"):
        return "env"
    if CONFIG_PATH.is_file():
        return str(CONFIG_PATH.stat().st_mtime)
    return "missing"


def quote_table(name: str) -> str:
    return f"`{name}`"


def normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {k: normalize_value(v) for k, v in row.items()}


def create_engine_and_tunnel(cfg: dict[str, Any]) -> tuple[Engine, SSHTunnelForwarder]:
    server = SSHTunnelForwarder(
        (cfg["ssh_host"], cfg["ssh_port"]),
        ssh_username=cfg["ssh_username"],
        ssh_password=cfg["ssh_password"],
        remote_bind_address=(cfg["remote_host"], cfg["remote_port"]),
    )
    server.start()
    engine = create_engine(
        (
            f"mariadb+pymysql://{cfg['db_user']}:{cfg['db_password']}"
            f"@127.0.0.1:{server.local_bind_port}/{cfg['db_name']}"
        ),
        pool_pre_ping=True,
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine, server


_engine: Optional[Engine] = None
_tunnel: Optional[SSHTunnelForwarder] = None


def get_engine() -> Engine:
    """Return a shared engine (Streamlit cache or process-local singleton)."""
    global _engine, _tunnel
    try:
        import streamlit as st

        @st.cache_resource(show_spinner="Connecting to database…")
        def _cached_engine(cache_key: str) -> Engine:
            cfg = load_db_config()
            engine, server = create_engine_and_tunnel(cfg)
            st.session_state["_db_tunnel"] = server
            return engine

        return _cached_engine(config_cache_key())
    except ImportError:
        if _engine is None:
            cfg = load_db_config()
            _engine, _tunnel = create_engine_and_tunnel(cfg)
        return _engine
