"""MariaDB/MySQL engine — direct (e.g. Aiven) or SSH tunnel."""

from __future__ import annotations

import os
from configparser import ConfigParser
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sshtunnel import SSHTunnelForwarder

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "db.ini"
DEFAULT_SSL_CA = ROOT / "ca.pem"


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


def resolve_ssl_ca(path: Optional[str], *, auto_default: bool = False) -> Optional[str]:
    """Resolve SSL CA path relative to project root. None disables SSL."""
    if path is not None and path.strip().lower() in ("", "false", "none", "0"):
        return None
    if path is None or not str(path).strip():
        if auto_default and DEFAULT_SSL_CA.is_file():
            return str(DEFAULT_SSL_CA)
        return None
    p = Path(path.strip())
    if not p.is_absolute():
        p = ROOT / p
    if not p.is_file():
        raise DbConfigError(f"SSL CA file not found: {p}")
    return str(p)


def load_db_config() -> dict[str, Any]:
    """Load connection settings from environment variables or db.ini."""
    if os.environ.get("DB_HOST"):
        return _config_direct_from_env()

    if os.environ.get("DB_SSH_HOST"):
        return _config_ssh_from_env()

    cfg = _read_ini()
    mode = cfg.get("connection", "mode", fallback="direct").strip().lower()
    if mode not in ("direct", "ssh"):
        raise DbConfigError(
            f"Invalid connection mode {mode!r} in db.ini — use 'direct' or 'ssh'."
        )

    base = {
        "mode": mode,
        "db_user": cfg.get("database", "user"),
        "db_password": cfg.get("database", "password"),
        "db_name": cfg.get("database", "name", fallback="defaultdb"),
        "charset": cfg.get("database", "charset", fallback="utf8mb4"),
        "connect_timeout": cfg.getint("database", "connect_timeout", fallback=10),
        "read_timeout": cfg.getint("database", "read_timeout", fallback=10),
        "write_timeout": cfg.getint("database", "write_timeout", fallback=10),
    }

    if mode == "direct":
        ssl_ca_ini = cfg.get("database", "ssl_ca", fallback="ca.pem")
        base.update(
            {
                "db_host": cfg.get("database", "host"),
                "db_port": cfg.getint("database", "port"),
                "ssl_ca": resolve_ssl_ca(ssl_ca_ini, auto_default=True),
            }
        )
        if not base["db_host"]:
            raise DbConfigError("database.host is required when connection.mode = direct.")
        return base

    base.update(
        {
            "ssh_host": cfg.get("ssh", "host"),
            "ssh_port": cfg.getint("ssh", "port", fallback=22),
            "ssh_username": cfg.get("ssh", "username"),
            "ssh_password": cfg.get("ssh", "password"),
            "remote_host": cfg.get("database", "remote_host", fallback="127.0.0.1"),
            "remote_port": cfg.getint("database", "remote_port", fallback=3306),
        }
    )
    return base


def _config_direct_from_env() -> dict[str, Any]:
    ssl_env = os.environ.get("DB_SSL_CA")
    return {
        "mode": "direct",
        "db_host": os.environ["DB_HOST"],
        "db_port": int(os.environ.get("DB_PORT", "3306")),
        "db_user": os.environ["DB_USER"],
        "db_password": os.environ.get("DB_PASSWORD", ""),
        "db_name": os.environ.get("DB_NAME", "defaultdb"),
        "charset": os.environ.get("DB_CHARSET", "utf8mb4"),
        "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "10")),
        "read_timeout": int(os.environ.get("DB_READ_TIMEOUT", "10")),
        "write_timeout": int(os.environ.get("DB_WRITE_TIMEOUT", "10")),
        "ssl_ca": resolve_ssl_ca(ssl_env, auto_default=True),
    }


def _config_ssh_from_env() -> dict[str, Any]:
    return {
        "mode": "ssh",
        "ssh_host": os.environ["DB_SSH_HOST"],
        "ssh_port": int(os.environ.get("DB_SSH_PORT", "22")),
        "ssh_username": os.environ["DB_SSH_USER"],
        "ssh_password": os.environ.get("DB_SSH_PASSWORD", ""),
        "db_user": os.environ["DB_USER"],
        "db_password": os.environ.get("DB_PASSWORD", ""),
        "db_name": os.environ.get("DB_NAME", "mng_db"),
        "remote_host": os.environ.get("DB_REMOTE_HOST", "127.0.0.1"),
        "remote_port": int(os.environ.get("DB_REMOTE_PORT", "3306")),
        "charset": "utf8mb4",
        "connect_timeout": 10,
        "read_timeout": 10,
        "write_timeout": 10,
    }


def config_cache_key() -> str:
    parts: list[str] = []
    if os.environ.get("DB_HOST") or os.environ.get("DB_SSH_HOST"):
        parts.append("env")
    elif CONFIG_PATH.is_file():
        parts.append(str(CONFIG_PATH.stat().st_mtime))
    else:
        parts.append("missing")
    if DEFAULT_SSL_CA.is_file():
        parts.append(str(DEFAULT_SSL_CA.stat().st_mtime))
    return ":".join(parts)


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


def _pymysql_connect_args(cfg: dict[str, Any]) -> dict[str, Any]:
    args: dict[str, Any] = {
        "connect_timeout": cfg["connect_timeout"],
        "read_timeout": cfg["read_timeout"],
        "write_timeout": cfg["write_timeout"],
        "charset": cfg.get("charset", "utf8mb4"),
    }
    ssl_ca = cfg.get("ssl_ca")
    if ssl_ca:
        args["ssl"] = {"ca": ssl_ca}
    return args


def _sqlalchemy_url(cfg: dict[str, Any], host: str, port: int) -> URL:
    return URL.create(
        drivername="mysql+pymysql",
        username=cfg["db_user"],
        password=cfg["db_password"],
        host=host,
        port=port,
        database=cfg["db_name"],
    )


def create_direct_engine(cfg: dict[str, Any]) -> Engine:
    engine = create_engine(
        _sqlalchemy_url(cfg, cfg["db_host"], cfg["db_port"]),
        pool_pre_ping=True,
        connect_args=_pymysql_connect_args(cfg),
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def create_engine_and_tunnel(cfg: dict[str, Any]) -> tuple[Engine, SSHTunnelForwarder]:
    server = SSHTunnelForwarder(
        (cfg["ssh_host"], cfg["ssh_port"]),
        ssh_username=cfg["ssh_username"],
        ssh_password=cfg["ssh_password"],
        remote_bind_address=(cfg["remote_host"], cfg["remote_port"]),
    )
    server.start()
    engine = create_engine(
        _sqlalchemy_url(cfg, "127.0.0.1", server.local_bind_port),
        pool_pre_ping=True,
        connect_args=_pymysql_connect_args(cfg),
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine, server


def create_engine_from_config(cfg: dict[str, Any]) -> tuple[Engine, Optional[SSHTunnelForwarder]]:
    if cfg["mode"] == "direct":
        return create_direct_engine(cfg), None
    engine, tunnel = create_engine_and_tunnel(cfg)
    return engine, tunnel


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
            engine, tunnel = create_engine_from_config(cfg)
            if tunnel is not None:
                st.session_state["_db_tunnel"] = tunnel
            else:
                st.session_state.pop("_db_tunnel", None)
            return engine

        return _cached_engine(config_cache_key())
    except ImportError:
        if _engine is None:
            cfg = load_db_config()
            _engine, _tunnel = create_engine_from_config(cfg)
        return _engine
