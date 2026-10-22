"""
Flask REST API Backend Application Server.

Academic Context (Web & Computer Networks):
- Exposes standardized RESTful JSON API endpoints over HTTP.
- Serves static frontend dashboard presentation assets.
- Provides CORS compliance and uniform error responses.
"""

import os
from flask import Flask, jsonify, send_from_directory
from backend.routes.statistics import stats_bp
from backend.routes.alerts import alerts_bp
from backend.routes.events import events_bp
from backend.routes.pipeline import pipeline_bp
from backend.routes.wireless import wireless_bp


def create_app() -> Flask:
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")

    # Register Route Blueprints
    app.register_blueprint(stats_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(wireless_bp)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    @app.route("/")
    def index():
        """Serves the dashboard presentation interface."""
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/api/v1/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "Zeek Network Traffic Monitor REST API",
            "version": "1.0.0",
        })

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("FLASK_PORT", 5000))
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    print(f"[*] Starting Flask REST Backend on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
