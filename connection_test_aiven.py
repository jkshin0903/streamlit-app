"""
Aiven / direct MySQL connection test (uses db.ini with connection.mode = direct).

Run:
    python connection_test_aiven.py
"""

from sqlalchemy import text

from lib.db import create_direct_engine, load_db_config


def main() -> None:
    cfg = load_db_config()
    if cfg["mode"] != "direct":
        raise SystemExit(
            "Set connection.mode = direct in db.ini (see db.ini.example)."
        )
    engine = create_direct_engine(cfg)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT 1 AS ok")).one()
    print(f"Connected to {cfg['db_host']}:{cfg['db_port']}/{cfg['db_name']} — {row}")


if __name__ == "__main__":
    main()
