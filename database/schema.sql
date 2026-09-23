-- ==============================================================================
-- Mini Project 2026: Wireless Network Traffic Monitor Using Zeek
-- MySQL Relational Database Schema
--
-- Academic Context (Database Management Systems):
-- - 3NF Relational normalization.
-- - Foreign key relationships and cascade constraints.
-- - B-Tree indexes on query attributes (source_ip, timestamp, severity).
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS zeek_monitor
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE zeek_monitor;

-- ------------------------------------------------------------------------------
-- Table: network_logs
-- Stores structured Zeek connection events
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(64) NOT NULL DEFAULT '-',
    timestamp DOUBLE NOT NULL,
    source_ip VARCHAR(45) NOT NULL,
    source_port INT UNSIGNED NOT NULL DEFAULT 0,
    destination_ip VARCHAR(45) NOT NULL,
    destination_port INT UNSIGNED NOT NULL DEFAULT 0,
    protocol VARCHAR(16) NOT NULL DEFAULT 'tcp',
    service VARCHAR(32) NOT NULL DEFAULT '-',
    duration DOUBLE NOT NULL DEFAULT 0.0,
    orig_bytes BIGINT UNSIGNED NOT NULL DEFAULT 0,
    resp_bytes BIGINT UNSIGNED NOT NULL DEFAULT 0,
    conn_state VARCHAR(16) NOT NULL DEFAULT '-',
    history VARCHAR(32) NOT NULL DEFAULT '-',
    orig_pkts INT UNSIGNED NOT NULL DEFAULT 0,
    resp_pkts INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_netlog_source_ip (source_ip),
    INDEX idx_netlog_dest_ip (destination_ip),
    INDEX idx_netlog_timestamp (timestamp),
    INDEX idx_netlog_protocol (protocol),
    INDEX idx_netlog_service (service)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table: alerts
-- Stores security incidents and anomalies flagged by detection engines
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    alert_id VARCHAR(32) NOT NULL UNIQUE,
    log_id BIGINT NULL,
    timestamp DOUBLE NOT NULL,
    source_ip VARCHAR(45) NOT NULL,
    destination_ip VARCHAR(45) NOT NULL,
    alert_type VARCHAR(64) NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL DEFAULT 'LOW',
    detection_method ENUM('RULE', 'KMP', 'REGEX', 'DECISION_TREE') NOT NULL,
    description TEXT NOT NULL,
    evidence JSON NULL,
    status ENUM('OPEN', 'ACKNOWLEDGED', 'RESOLVED') NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (log_id) REFERENCES network_logs(id) ON DELETE SET NULL,
    INDEX idx_alerts_timestamp (timestamp),
    INDEX idx_alerts_source_ip (source_ip),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_method (detection_method)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- Table: system_metrics
-- Aggregated buffer, queue, and traffic telemetry over time
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(64) NOT NULL,
    metric_value DOUBLE NOT NULL,
    metric_metadata JSON NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_metrics_name (metric_name),
    INDEX idx_metrics_recorded (recorded_at)
) ENGINE=InnoDB;
