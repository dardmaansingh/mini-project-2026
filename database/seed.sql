-- ==============================================================================
-- Mini Project 2026: Database Baseline Seed Data
-- ==============================================================================

USE zeek_monitor;

-- Insert baseline sample logs
INSERT INTO network_logs (uid, timestamp, source_ip, source_port, destination_ip, destination_port, protocol, service, duration, orig_bytes, resp_bytes, conn_state, history, orig_pkts, resp_pkts)
VALUES
('Cseed001', UNIX_TIMESTAMP() - 120, '192.168.1.10', 49152, '192.168.1.1', 53, 'udp', 'dns', 0.005, 45, 120, 'SF', 'Dd', 1, 1),
('Cseed002', UNIX_TIMESTAMP() - 90, '192.168.1.25', 52310, '192.168.1.1', 80, 'tcp', 'http', 0.120, 240, 1420, 'SF', 'ShADadfF', 5, 8),
('Cseed003', UNIX_TIMESTAMP() - 60, '10.0.0.99', 41200, '192.168.1.1', 22, 'tcp', 'ssh', 0.002, 0, 0, 'S0', 'S', 1, 0),
('Cseed004', UNIX_TIMESTAMP() - 30, '10.0.0.99', 41201, '192.168.1.1', 23, 'tcp', '-', 0.001, 0, 0, 'REJ', 'Sr', 1, 1),
('Cseed005', UNIX_TIMESTAMP() - 10, '192.168.1.50', 58120, '192.168.1.200', 443, 'tcp', 'ssl', 1.500, 1200, 8500, 'SF', 'ShADadFf', 12, 18);

-- Insert baseline sample alerts
INSERT INTO alerts (alert_id, log_id, timestamp, source_ip, destination_ip, alert_type, severity, detection_method, description, evidence, status)
VALUES
('ALT-SEED-01', 3, UNIX_TIMESTAMP() - 60, '10.0.0.99', '192.168.1.1', 'FAILED_CONNECTION_FLOOD', 'HIGH', 'RULE', 'Host accumulated repeated SYN connection failures.', '{"failed_count": 12, "threshold": 10}', 'OPEN'),
('ALT-SEED-02', 4, UNIX_TIMESTAMP() - 30, '10.0.0.99', '192.168.1.1', 'ML_SUSPICIOUS_PROBE_OR_SCAN', 'HIGH', 'DECISION_TREE', 'Decision tree classified probe based on S0 state and 1 packet.', '{"confidence": 0.95}', 'OPEN');
