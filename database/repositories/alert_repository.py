"""
Alert Repository.

Academic Context (DBMS):
- Implements DAO pattern for security alerts.
- Relational mapping with JSON serialization for dynamic evidence payload.
"""

import json
from typing import List, Dict, Any, Optional
from database.connection import DatabaseConnectionPool


class AlertRepository:
    """
    CRUD and analytical queries on alerts table.
    """

    def insert_alert(self, alert: Dict[str, Any]) -> Optional[int]:
        """Inserts an alert record into MySQL with JSON evidence."""
        sql = """
            INSERT INTO alerts (
                alert_id, log_id, timestamp, source_ip, destination_ip,
                alert_type, severity, detection_method, description, evidence, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor()
            evidence_json = json.dumps(alert.get("evidence", {}))
            params = (
                alert.get("alert_id"),
                alert.get("log_id"),
                float(alert.get("timestamp", 0.0)),
                alert.get("source_ip", "0.0.0.0"),
                alert.get("destination_ip", "0.0.0.0"),
                alert.get("alert_type", "UNKNOWN"),
                alert.get("severity", "LOW"),
                alert.get("detection_method", "RULE"),
                alert.get("description", ""),
                evidence_json,
                alert.get("status", "OPEN"),
            )
            cursor.execute(sql, params)
            row_id = cursor.lastrowid
            cursor.close()
            return row_id
        finally:
            conn.close()

    def get_recent_alerts(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent alerts with optional severity filtering."""
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            if severity:
                sql = "SELECT * FROM alerts WHERE severity = %s ORDER BY timestamp DESC LIMIT %s;"
                cursor.execute(sql, (severity.upper(), limit))
            else:
                sql = "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT %s;"
                cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            conn.close()

    def get_severity_counts(self) -> Dict[str, int]:
        """Calculates breakdown of alerts across severity categories."""
        sql = "SELECT severity, COUNT(*) AS count FROM alerts GROUP BY severity;"
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            for r in rows:
                counts[r["severity"]] = r["count"]
            return counts
        finally:
            conn.close()
