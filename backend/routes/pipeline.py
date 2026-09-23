"""
Pipeline & Concurrency Telemetry REST API Blueprint.

Exposes real-time OS synchronization primitives, buffer capacity, pointers,
worker thread states, and high water mark.
"""

from flask import Blueprint, jsonify
from backend.services.pipeline_service import PipelineService

pipeline_bp = Blueprint("pipeline", __name__, url_prefix="/api/v1/pipeline")


@pipeline_bp.route("/telemetry", methods=["GET"])
def get_telemetry():
    """Returns real-time concurrency and buffer metrics."""
    service = PipelineService.get_instance()
    telemetry = service.manager.get_telemetry()
    return jsonify({
        "status": "success",
        "data": telemetry
    })
