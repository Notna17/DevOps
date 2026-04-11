#!/usr/bin/env python3
# Purpose: Run mywebapp Flask service with inventory endpoints, health checks, and TOML config.

"""Main Flask application for the mywebapp inventory service."""

from __future__ import annotations

import os
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from flask import Flask, Response, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.serving import make_server

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - Ubuntu 22.04 uses Python 3.10
    import tomli as tomllib  # type: ignore

CONFIG_PATH = "/etc/mywebapp/config.toml"


@dataclass(frozen=True)
class ServerConfig:
    """Application listener settings."""

    host: str
    port: int


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL connection settings."""

    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class AppConfig:
    """Full application configuration."""

    server: ServerConfig
    database: DatabaseConfig


def load_config(path: str = CONFIG_PATH) -> AppConfig:
    """Load and validate TOML configuration file."""

    if not os.path.exists(path):
        raise RuntimeError(f"Missing configuration file: {path}")

    try:
        with open(path, "rb") as config_file:
            raw = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(f"Invalid TOML in configuration file {path}: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not read configuration file {path}: {exc}") from exc

    try:
        server = raw["server"]
        database = raw["database"]
        return AppConfig(
            server=ServerConfig(
                host=str(server["host"]),
                port=int(server["port"]),
            ),
            database=DatabaseConfig(
                host=str(database["host"]),
                port=int(database["port"]),
                name=str(database["name"]),
                user=str(database["user"]),
                password=str(database["password"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "Invalid configuration structure. Required sections: [server] and [database] with all keys."
        ) from exc


def get_db_connection(config: AppConfig):
    """Open a PostgreSQL connection using loaded configuration."""

    return psycopg2.connect(
        host=config.database.host,
        port=config.database.port,
        dbname=config.database.name,
        user=config.database.user,
        password=config.database.password,
    )


def wants_html() -> bool:
    """Return True when client explicitly requests HTML output."""

    accept = request.headers.get("Accept", "")
    return "text/html" in accept and "application/json" not in accept


def render_index() -> str:
    """Render root endpoint describing available API routes."""

    return """<!doctype html>
<html>
  <head><title>mywebapp endpoints</title></head>
  <body>
    <h1>mywebapp - Simple Inventory</h1>
    <ul>
      <li>GET /items</li>
      <li>POST /items</li>
      <li>GET /items/&lt;id&gt;</li>
      <li>GET /health/alive</li>
      <li>GET /health/ready</li>
    </ul>
  </body>
</html>
"""


def items_to_html(items: list[dict[str, Any]]) -> str:
    """Render inventory list as an HTML table."""

    rows = "\n".join(
        f"      <tr><td>{item['id']}</td><td>{item['name']}</td></tr>" for item in items
    )
    return f"""<!doctype html>
<html>
  <head><title>Inventory items</title></head>
  <body>
    <h1>Inventory items</h1>
    <table border=\"1\">
      <thead><tr><th>id</th><th>name</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
  </body>
</html>
"""


def item_to_html(item: dict[str, Any]) -> str:
    """Render single inventory item details as plain HTML."""

    created_at = item["created_at"]
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    return f"""<!doctype html>
<html>
  <head><title>Inventory item {item['id']}</title></head>
  <body>
    <h1>Inventory item {item['id']}</h1>
    <table border=\"1\">
      <tbody>
        <tr><th>id</th><td>{item['id']}</td></tr>
        <tr><th>name</th><td>{item['name']}</td></tr>
        <tr><th>quantity</th><td>{item['quantity']}</td></tr>
        <tr><th>created_at</th><td>{created_at}</td></tr>
      </tbody>
    </table>
  </body>
</html>
"""


def create_app(config: AppConfig) -> Flask:
    """Create and configure Flask application instance."""

    app = Flask(__name__)

    @app.get("/health/alive")
    def health_alive() -> Response:
        return Response("OK", status=200, mimetype="text/plain")

    @app.get("/health/ready")
    def health_ready() -> Response:
        try:
            with get_db_connection(config) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return Response("OK", status=200, mimetype="text/plain")
        except Exception as exc:  # pylint: disable=broad-except
            return Response(f"Database not ready: {exc}", status=500, mimetype="text/plain")

    @app.get("/")
    def root() -> Response:
        return Response(render_index(), status=200, mimetype="text/html")

    @app.get("/items")
    def list_items() -> Response:
        try:
            with get_db_connection(config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT id, name FROM items ORDER BY id")
                    items = [dict(row) for row in cur.fetchall()]
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({"error": "Database query failed", "details": str(exc)}), 500

        if wants_html():
            return Response(items_to_html(items), status=200, mimetype="text/html")
        return jsonify(items), 200

    @app.post("/items")
    def create_item() -> Response:
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        quantity = data.get("quantity")

        if not isinstance(name, str) or not name.strip():
            return jsonify({"error": "Field 'name' must be a non-empty string"}), 400
        if not isinstance(quantity, int):
            return jsonify({"error": "Field 'quantity' must be an integer"}), 400

        try:
            with get_db_connection(config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        INSERT INTO items (name, quantity)
                        VALUES (%s, %s)
                        RETURNING id, name, quantity, created_at
                        """,
                        (name.strip(), quantity),
                    )
                    created = dict(cur.fetchone())
                conn.commit()
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({"error": "Failed to create item", "details": str(exc)}), 500

        if wants_html():
            return Response(item_to_html(created), status=201, mimetype="text/html")
        return jsonify(created), 201

    @app.get("/items/<int:item_id>")
    def get_item(item_id: int) -> Response:
        try:
            with get_db_connection(config) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT id, name, quantity, created_at FROM items WHERE id = %s",
                        (item_id,),
                    )
                    row = cur.fetchone()
        except Exception as exc:  # pylint: disable=broad-except
            return jsonify({"error": "Database query failed", "details": str(exc)}), 500

        if row is None:
            return jsonify({"error": "Item not found"}), 404

        item = dict(row)
        if wants_html():
            return Response(item_to_html(item), status=200, mimetype="text/html")
        return jsonify(item), 200

    return app


def run_with_optional_socket_activation(app: Flask, config: AppConfig) -> None:
    """Start WSGI server on socket-activated FD when available, else bind host/port."""

    listen_fds = int(os.environ.get("LISTEN_FDS", "0"))
    listen_pid = int(os.environ.get("LISTEN_PID", "0"))

    if listen_fds >= 1 and listen_pid == os.getpid():
        server = make_server(config.server.host, config.server.port, app, fd=3)
        server.serve_forever()
        return

    server = make_server(config.server.host, config.server.port, app)
    server.serve_forever()


def main() -> int:
    """Entrypoint for application startup."""

    try:
        config = load_config()
        _ = socket.gethostbyname(config.database.host)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Configuration validation failed: {exc}", file=sys.stderr)
        return 2

    app = create_app(config)
    run_with_optional_socket_activation(app, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
