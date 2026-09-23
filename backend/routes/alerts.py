"""
Alerts REST API Route Blueprint.

Provides security alert queries and the local mock webhook receiver endpoint.
"""

from flask import Blueprint, jsonify, request
from backend.services.pipeline_service import PipelineService

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")


@alerts_bp.route("", methods=["GET"])
def get_alerts():
    """Retrieves list of recent alerts with optional severity filtering."""
    service = PipelineService.get_instance()
    severity = request.args.get("severity")
    limit = int(request.args.get("limit", 50))

    alerts = service.alert_repo.get_recent_alerts(limit=limit, severity=severity)
    return jsonify({
        "status": "success",
        "count": len(alerts),
        "data": alerts
    })


@alerts_bp.route("/severity-counts", methods=["GET"])
def get_severity_counts():
    """Returns alert counts classified by severity."""
    service = PipelineService.get_instance()
    counts = service.alert_repo.get_severity_counts()
    return jsonify({
        "status": "success",
        "data": counts
    })


@alerts_bp.route("/webhook/test", methods=["POST"])
def mock_webhook_receiver():
    """
    Mock Webhook receiver endpoint.
    Verifies that HTTP POST alerts dispatched by WebhookDispatcher arrive with valid JSON.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "status": "received",
        "message": "Alert notification received successfully via HTTP Webhook.",
        "alert_id": payload.get("alert_id"),
        "severity": payload.get("severity"),
        "received_at": payload.get("timestamp"),
    }), 200
