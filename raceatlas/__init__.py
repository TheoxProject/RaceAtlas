from pathlib import Path
from uuid import uuid4

import click
from flask import Flask, g, jsonify, request, send_from_directory
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from werkzeug.exceptions import HTTPException

from raceatlas.catalog import CatalogError, parse_query, select_page
from raceatlas.config import database_url, environment
from raceatlas.models import Category, Race
from raceatlas.seed import demo_id, seed_synthetic
from raceatlas.serialization import race_document

DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(ENVIRONMENT=environment(), DATABASE_URL=database_url(), FRONTEND_DIST=DIST)
    if config:
        app.config.update(config)
    engine = create_engine(
        app.config["DATABASE_URL"], pool_pre_ping=True, connect_args={"connect_timeout": 3}
    )
    app.extensions["database"] = engine

    @app.before_request
    def request_context():
        g.request_id = str(uuid4())

    @app.after_request
    def response_headers(response):
        response.headers["X-Request-ID"] = g.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        if response.is_json:
            response.headers["Cache-Control"] = "no-store"
        return response

    def error(code, message, status):
        return jsonify(code=code, message=message, fields=[], request_id=g.request_id), status

    @app.errorhandler(SQLAlchemyError)
    def database_failure(_error):
        # Never include SQL, connection URLs or exception strings in public output/logs.
        app.logger.error("Database unavailable; request_id=%s", g.request_id)
        return error("unavailable", "Service temporairement indisponible.", 503)

    @app.errorhandler(CatalogError)
    def catalog_failure(exc):
        message = {
            "invalid_filter": "Paramètres de sélection invalides.",
            "stale_cursor": "Le catalogue a changé. Actualisez la sélection.",
            "unavailable": "Service temporairement indisponible.",
        }[exc.code]
        return jsonify(
            code=exc.code, message=message, fields=exc.fields, request_id=g.request_id
        ), exc.status

    @app.get("/api/v1/races")
    def races():
        return jsonify(select_page(engine, parse_query(request.args)))

    @app.get("/api/v1/map")
    def map_page():
        return jsonify(select_page(engine, parse_query(request.args), map_projection=True))

    @app.get("/api/v1/catalog/options")
    def catalog_options():
        with Session(engine) as session:
            categories = session.scalars(select(Category).order_by(Category.code)).all()
            return jsonify(
                contract_version="1.0.0",
                categories=[{"code": item.code, "label": item.label} for item in categories],
            )

    @app.errorhandler(HTTPException)
    def http_failure(exc):
        if exc.code == 404:
            return error("not_found", "Ressource introuvable.", 404)
        return error("unavailable", "Requête non disponible.", exc.code or 500)

    @app.get("/api/health/live")
    def live():
        return jsonify(status="ok")

    @app.get("/api/health/ready")
    def ready():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1 FROM race LIMIT 1"))
        return jsonify(status="ready")

    @app.get("/api/foundation/demo")
    def demo():
        with Session(engine) as session:
            return jsonify(synthetic=True, race_id=demo_id(session))

    @app.get("/api/v1/races/<race_id>")
    def detail(race_id):
        with Session(engine) as session:
            race = session.get(Race, race_id)
            if race is None:
                return error("not_found", "Épreuve introuvable.", 404)
            return jsonify(race_document(race))

    @app.get("/")
    def index():
        directory = Path(app.config["FRONTEND_DIST"])
        if not (directory / "index.html").is_file():
            return error("unavailable", "Interface non compilée. Exécutez le build frontend.", 503)
        response = send_from_directory(directory, "index.html")
        response.headers["Cache-Control"] = "no-cache"
        return response

    @app.get("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(Path(app.config["FRONTEND_DIST"]) / "assets", filename)

    @app.cli.command("seed-synthetic")
    def seed_command():
        if app.config["ENVIRONMENT"] == "production":
            raise click.ClickException("Synthetic seed is disabled in production.")
        with Session(engine) as session, session.begin():
            count = seed_synthetic(session)
        click.echo(f"Synthetic races added: {count}")

    return app
