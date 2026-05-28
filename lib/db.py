"""MariaDB/MySQL engine (direct connection only)."""

from __future__ import annotations

import os
from configparser import ConfigParser
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

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
    """Load direct connection settings from st.secrets, env, or db.ini."""
    secret_cfg = _config_from_streamlit_secrets()
    if secret_cfg is not None:
        return secret_cfg

    if os.environ.get("DB_HOST"):
        return _config_direct_from_env()

    cfg = _read_ini()
    db = cfg["database"]
    base = {
        "db_host": db.get("host", ""),
        "db_port": cfg.getint("database", "port", fallback=3306),
        "db_user": db.get("user", ""),
        "db_password": db.get("password", ""),
        "db_name": db.get("name", "defaultdb"),
        "charset": db.get("charset", "utf8mb4"),
        "connect_timeout": cfg.getint("database", "connect_timeout", fallback=10),
        "read_timeout": cfg.getint("database", "read_timeout", fallback=10),
        "write_timeout": cfg.getint("database", "write_timeout", fallback=10),
        "ssl_ca": resolve_ssl_ca(db.get("ssl_ca"), auto_default=True),
    }
    if not base["db_host"]:
        raise DbConfigError("database.host is required in db.ini.")
    if not base["db_user"]:
        raise DbConfigError("database.user is required in db.ini.")
    return base


def _config_from_streamlit_secrets() -> Optional[dict[str, Any]]:
    """
    Read DB config from st.secrets if available.
    Expected shape:
      [database] host, port, user, password, name, ...
    """
    try:
        import streamlit as st
    except ImportError:
        return None

    secrets = getattr(st, "secrets", None)
    if not secrets:
        return None
    if "database" not in secrets:
        return None

    db = secrets["database"]
    base: dict[str, Any] = {
        "db_user": str(db["user"]),
        "db_password": str(db.get("password", "")),
        "db_name": str(db.get("name", "defaultdb")),
        "charset": str(db.get("charset", "utf8mb4")),
        "connect_timeout": int(db.get("connect_timeout", 10)),
        "read_timeout": int(db.get("read_timeout", 10)),
        "write_timeout": int(db.get("write_timeout", 10)),
    }

    # Supports either file path (ssl_ca) or inline PEM (ca_pem) in secrets.
    ssl_ca_secret = db.get("ssl_ca")
    ca_pem = db.get("ca_pem")
    if ca_pem:
        base["ssl_ca"] = _write_temp_ca_pem(str(ca_pem))
    else:
        base["ssl_ca"] = resolve_ssl_ca(
            str(ssl_ca_secret) if ssl_ca_secret is not None else None,
            auto_default=True,
        )

    base.update(
        {
            "db_host": str(db.get("host", "")),
            "db_port": int(db.get("port", 3306)),
        }
    )
    if not base["db_host"]:
        raise DbConfigError("database.host is required in st.secrets.")
    return base


def _write_temp_ca_pem(ca_pem: str) -> str:
    """Persist inline CA PEM from secrets to a local file path."""
    pem_path = ROOT / ".streamlit" / ".runtime-ca.pem"
    pem_path.parent.mkdir(parents=True, exist_ok=True)
    pem_path.write_text(ca_pem, encoding="utf-8")
    return str(pem_path)


def _config_direct_from_env() -> dict[str, Any]:
    ssl_env = os.environ.get("DB_SSL_CA")
    return {
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


def config_cache_key() -> str:
    parts: list[str] = []
    if os.environ.get("DB_HOST"):
        parts.append("env")
    elif _has_streamlit_secrets():
        parts.append("secrets")
    elif CONFIG_PATH.is_file():
        parts.append(str(CONFIG_PATH.stat().st_mtime))
    else:
        parts.append("missing")
    if DEFAULT_SSL_CA.is_file():
        parts.append(str(DEFAULT_SSL_CA.stat().st_mtime))
    return ":".join(parts)


def _has_streamlit_secrets() -> bool:
    try:
        import streamlit as st
    except ImportError:
        return False
    secrets = getattr(st, "secrets", None)
    return bool(secrets and "database" in secrets)


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


def create_engine_from_config(cfg: dict[str, Any]) -> Engine:
    return create_direct_engine(cfg)


_engine: Optional[Engine] = None


def get_engine() -> Engine:
    """Return a shared engine (Streamlit cache or process-local singleton)."""
    global _engine
    try:
        import streamlit as st

        @st.cache_resource(show_spinner="Connecting to database…")
        def _cached_engine(cache_key: str) -> Engine:
            cfg = load_db_config()
            return create_engine_from_config(cfg)

        return _cached_engine(config_cache_key())
    except ImportError:
        if _engine is None:
            cfg = load_db_config()
            _engine = create_engine_from_config(cfg)
        return _engine
