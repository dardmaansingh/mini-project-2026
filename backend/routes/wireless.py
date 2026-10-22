"""
Wireless Monitoring & Suspicious Network REST API Route Blueprint.

Academic & Operational Context:
- Provides RESTful JSON endpoints for real-time 802.11 / Wi-Fi physical layer telemetry.
- Delivers RSSI signal strength tracking, spectrum channel distribution, and rogue AP forensics.
- Enables interactive threat simulation and administrative mitigation.
"""

from flask import Blueprint, jsonify, request
from detection.wireless.wireless_analyzer import get_wireless_scanner

wireless_bp = Blueprint("wireless", __name__, url_prefix="/api/v1/wireless")


@wireless_bp.route("/summary", methods=["GET"])
def get_wireless_summary():
    """Returns top-level RF telemetry, suspicious AP counts, and active interface status."""
    scanner = get_wireless_scanner()
    summary = scanner.get_summary()
    return jsonify({
        "status": "success",
        "data": summary
    })


@wireless_bp.route("/networks", methods=["GET"])
def get_networks():
    """
    Returns list of discovered wireless access points.
    Optional query params:
    - suspicious: 'true' to filter only flagged rogue APs
    - query / q: substring search across SSID, BSSID, or Vendor
    - band: '2.4' or '5' to filter by frequency band
    """
    scanner = get_wireless_scanner()
    suspicious_only = request.args.get("suspicious", "").lower() in ["true", "1"]
    search_query = request.args.get("q", "").strip().lower()
    band_filter = request.args.get("band", "").strip()

    networks = scanner.get_all_networks(suspicious_only=suspicious_only)

    if search_query:
        networks = [
            n for n in networks
            if search_query in n["ssid"].lower()
            or search_query in n["bssid"].lower()
            or search_query in n["vendor"].lower()
        ]

    if band_filter:
        networks = [n for n in networks if band_filter in n["band"]]

    return jsonify({
        "status": "success",
        "count": len(networks),
        "data": networks
    })


@wireless_bp.route("/suspicious", methods=["GET"])
def get_suspicious_networks():
    """Returns dedicated list of rogue APs and security anomalies with threat forensics."""
    scanner = get_wireless_scanner()
    suspicious = scanner.get_suspicious_networks()
    return jsonify({
        "status": "success",
        "count": len(suspicious),
        "data": suspicious
    })


@wireless_bp.route("/spectrum", methods=["GET"])
def get_spectrum():
    """Returns channel occupancy and strongest RSSI distributions across 2.4 GHz and 5 GHz."""
    scanner = get_wireless_scanner()
    spectrum = scanner.get_spectrum_data()
    return jsonify({
        "status": "success",
        "data": spectrum
    })


@wireless_bp.route("/rssi-timeline", methods=["GET"])
def get_rssi_timeline():
    """Returns rolling RSSI time-series data for charting signal strength dynamics."""
    scanner = get_wireless_scanner()
    timeline = scanner.get_rssi_history_timeline()
    return jsonify({
        "status": "success",
        "data": timeline
    })


@wireless_bp.route("/interfaces", methods=["GET"])
def get_interfaces():
    """Returns discovered network adapters and live packet throughput stats."""
    scanner = get_wireless_scanner()
    summary = scanner.get_summary()
    return jsonify({
        "status": "success",
        "active_interface": summary["active_interface"],
        "hardware_mode": summary["hardware_mode"],
        "interfaces": summary["system_interfaces"],
    })


@wireless_bp.route("/scan", methods=["POST"])
def trigger_scan():
    """Triggers an immediate live RF environment scan cycle."""
    scanner = get_wireless_scanner()
    summary = scanner.trigger_scan()
    return jsonify({
        "status": "success",
        "message": "Live network RF scan completed successfully.",
        "data": summary
    })


@wireless_bp.route("/toggle-scan", methods=["POST"])
def toggle_scan():
    """Enables or pauses continuous autonomous scanning."""
    scanner = get_wireless_scanner()
    scanner.is_scanning = not scanner.is_scanning
    state_str = "resumed" if scanner.is_scanning else "paused"
    return jsonify({
        "status": "success",
        "is_scanning": scanner.is_scanning,
        "message": f"Autonomous live wireless scanning {state_str}."
    })


@wireless_bp.route("/inject-threat", methods=["POST"])
def inject_threat():
    """
    Injects a live wireless threat scenario (EVIL_TWIN, DEAUTH_STORM, HIGH_POWER_ROGUE, WEP_LEGACY)
    for interactive verification and viva defense demonstrations.
    """
    data = request.get_json(silent=True) or {}
    threat_type = data.get("threat_type", "EVIL_TWIN").upper()

    scanner = get_wireless_scanner()
    result = scanner.inject_threat(threat_type)

    if result.get("status") == "error":
        return jsonify(result), 400

    return jsonify({
        "status": "success",
        "message": f"Simulated {threat_type} wireless threat successfully injected.",
        "data": result
    })


@wireless_bp.route("/mitigate", methods=["POST"])
def mitigate_ap():
    """Marks a rogue BSSID as mitigated/quarantined."""
    data = request.get_json(silent=True) or {}
    bssid = data.get("bssid", "").strip()
    if not bssid:
        return jsonify({"status": "error", "message": "BSSID parameter is required."}), 400

    scanner = get_wireless_scanner()
    success = scanner.mitigate_network(bssid)
    if not success:
        return jsonify({"status": "error", "message": f"Network with BSSID '{bssid}' not found."}), 404

    return jsonify({
        "status": "success",
        "message": f"Network {bssid} successfully quarantined and mitigated."
    })
