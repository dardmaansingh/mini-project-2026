from flask import Blueprint, jsonify, request
from backend.services.pipeline_service import PipelineService

events_bp = Blueprint("events", __name__, url_prefix="/api/v1/events")


@events_bp.route("/recent", methods=["GET"])
def get_recent_events():
    service = PipelineService.get_instance()
    limit = int(request.args.get("limit", 50))
    events = service.log_repo.get_recent_logs(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(events),
        "data": events
    })


@events_bp.route("/inject-burst", methods=["POST"])
def inject_burst():
    data = request.get_json(silent=True) or {}
    burst_size = int(data.get("count", 100))
    if burst_size <= 0 or burst_size > 2000:
        return jsonify({"status": "error", "message": "Burst count must be between 1 and 2000."}), 400

    service = PipelineService.get_instance()
    result = service.inject_traffic_burst(count=burst_size)
    return jsonify({
        "status": "success",
        "message": f"Successfully injected {result['enqueued']} events into Circular Buffer.",
        "data": result
    })


@events_bp.route("/inject-dns-flood", methods=["POST"])
def inject_dns_flood():
    data = request.get_json(silent=True) or {}
    count = int(data.get("count", 35))
    attacker_ip = str(data.get("attacker_ip", "192.168.1.155"))
    if count <= 0 or count > 500:
        return jsonify({"status": "error", "message": "DNS query count must be between 1 and 500."}), 400

    service = PipelineService.get_instance()
    result = service.inject_dns_flood(count=count, attacker_ip=attacker_ip)
    return jsonify({
        "status": "success",
        "message": f"Successfully wrote {result['written_to_disk']} live DNS queries to disk and Circular Buffer.",
        "data": result
    })

