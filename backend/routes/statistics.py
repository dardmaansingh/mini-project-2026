"""
Statistics REST API Route Blueprint.

Provides aggregated network metrics, protocol distributions, and top source IPs.
"""

from flask import Blueprint, jsonify
from backend.services.pipeline_service import PipelineService

stats_bp = Blueprint("statistics", __name__, url_prefix="/api/v1/statistics")


@stats_bp.route("/summary", methods=["GET"])
def get_summary():
    """Returns top-level dashboard telemetry and MySQL connection status."""
    service = PipelineService.get_instance()
    summary = service.log_repo.get_traffic_summary()
    severity_counts = service.alert_repo.get_severity_counts()
    telemetry = service.manager.get_telemetry()

    return jsonify({
        "status": "success",
        "data": {
            "total_connections": summary.get("total_connections", 0),
            "total_bytes": summary.get("total_bytes", 0),
            "avg_duration": summary.get("avg_duration", 0.0),
            "total_alerts": telemetry.get("total_alerts_generated", 0),
            "severity_counts": severity_counts,
            "database_connected": service.db_available,
            "database_message": service.db_status_message,
        }
    })


@stats_bp.route("/protocols", methods=["GET"])
def get_protocols():
    """Returns connection counts grouped by protocol."""
    service = PipelineService.get_instance()
    distribution = service.log_repo.get_protocol_distribution()
    return jsonify({
        "status": "success",
        "data": distribution
    })


@stats_bp.route("/top-sources", methods=["GET"])
def get_top_sources():
    """Returns top active source IPs using SQL aggregation (GROUP BY source_ip)."""
    service = PipelineService.get_instance()
    top_ips = service.log_repo.get_top_source_ips(limit=10)
    return jsonify({
        "status": "success",
        "data": top_ips
    })
