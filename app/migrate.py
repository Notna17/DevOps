#!/usr/bin/env python3
"""Database migration script for mywebapp."""

from __future__ import annotations

import os
import sys

import psycopg2

try:
    import tomllib  
except ModuleNotFoundError: 
    import tomli as tomllib  

CONFIG_PATH = "/etc/mywebapp/config.toml"


def load_database_config(path: str = CONFIG_PATH) -> dict[str, str | int]:
    """Load database connection settings from TOML config file."""

    if not os.path.exists(path):
        raise RuntimeError(f"Missing configuration file: {path}")

    try:
        with open(path, "rb") as config_file:
            raw = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(
            f"Invalid TOML in configuration file {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"Could not read configuration file {path}: {exc}"
        ) from exc

    try:
        db = raw["database"]
        return {
            "host": str(db["host"]),
            "port": int(db["port"]),
            "dbname": str(db["name"]),
            "user": str(db["user"]),
            "password": str(db["password"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "Invalid [database] section in configuration."
        ) from exc


def migrate() -> None:
    """Create schema objects if they do not already exist."""

    db_config = load_database_config()

    with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_items_name ON items (name)"
            )
        conn.commit()


def main() -> int:
    """CLI entrypoint for migration script."""

    try:
        migrate()
        print("Migration completed successfully.")
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
