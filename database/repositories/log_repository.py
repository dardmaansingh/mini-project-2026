"""
Network Log Repository.

Academic Context (DBMS):
- Implements DAO (Data Access Object) pattern.
- Performs parameterized SQL queries to prevent SQL Injection.
- Implements analytical aggregations (GROUP BY, SUM, COUNT) for network telemetry.
"""

import json
from typing import List, Dict, Any, Optional
from database.connection import DatabaseConnectionPool


class LogRepository:
    """
    CRUD and analytical queries on network_logs table.
    """

    def insert_log(self, event: Dict[str, Any]) -> Optional[int]:
        """Inserts a normalized Zeek connection record into MySQL."""
        sql = """
            INSERT INTO network_logs (
                uid, timestamp, source_ip, source_port, destination_ip, destination_port,
                protocol, service, duration, orig_bytes, resp_bytes, conn_state,
                history, orig_pkts, resp_pkts
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor()
            params = (
                event.get("uid", "-"),
                float(event.get("timestamp", 0.0)),
                event.get("source_ip", "0.0.0.0"),
                int(event.get("source_port", 0)),
                event.get("destination_ip", "0.0.0.0"),
                int(event.get("destination_port", 0)),
                event.get("protocol", "tcp"),
                event.get("service", "-"),
                float(event.get("duration", 0.0)),
                int(event.get("orig_bytes", 0)),
                int(event.get("resp_bytes", 0)),
                event.get("conn_state", "-"),
                event.get("history", "-"),
                int(event.get("orig_pkts", 0)),
                int(event.get("resp_pkts", 0)),
            )
            cursor.execute(sql, params)
            log_id = cursor.lastrowid
            cursor.close()
            return log_id
        finally:
            conn.close()

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves most recent log records."""
        sql = "SELECT * FROM network_logs ORDER BY timestamp DESC LIMIT %s;"
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor(dictionary=True) if hasattr(conn, "cursor") else conn.cursor()
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            conn.close()

    def get_top_source_ips(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Required Project Query:
        SELECT source_ip, COUNT(*) as connection_count
        FROM network_logs
        GROUP BY source_ip
        ORDER BY connection_count DESC
        LIMIT %s;
        """
        sql = """
            SELECT source_ip, COUNT(*) AS connection_count
            FROM network_logs
            GROUP BY source_ip
            ORDER BY connection_count DESC
            LIMIT %s;
        """
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            conn.close()

    def get_protocol_distribution(self) -> List[Dict[str, Any]]:
        """Retrieves breakdown of connections grouped by protocol."""
        sql = """
            SELECT protocol, COUNT(*) AS count
            FROM network_logs
            GROUP BY protocol;
        """
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        finally:
            conn.close()

    def get_traffic_summary(self) -> Dict[str, Any]:
        """Retrieves aggregated network telemetry."""
        sql = """
            SELECT
                COUNT(*) AS total_connections,
                COALESCE(SUM(orig_bytes + resp_bytes), 0) AS total_bytes,
                COALESCE(AVG(duration), 0) AS avg_duration
            FROM network_logs;
        """
        conn = DatabaseConnectionPool.get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            row = cursor.fetchone()
            cursor.close()
            return row or {"total_connections": 0, "total_bytes": 0, "avg_duration": 0.0}
        finally:
            conn.close()
