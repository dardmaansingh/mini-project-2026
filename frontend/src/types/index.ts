/**
 * NetSentinel — TypeScript type definitions for API responses.
 */

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'informational'
export type AlertStatus = 'new' | 'acknowledged' | 'investigating' | 'resolved' | 'false_positive'
export type Confidence = 'high' | 'medium' | 'low'

export interface NetworkEvent {
  id: string
  timestamp_utc: string
  event_type: string
  source_type: string
  source_ip?: string
  source_port?: number
  destination_ip?: string
  destination_port?: number
  protocol?: string
  domain?: string
  dns_record_type?: string
  dns_response_code?: string
  ap_id?: string
  switch_id?: string
  switch_port?: string
  vlan_id?: string
  username?: string
  authentication_result?: string
  bytes_sent?: number
  bytes_received?: number
  packets?: number
  client_mac?: string
  simulated: boolean
  extra_metadata?: Record<string, unknown>
}

export interface Alert {
  id: string
  rule_id: string
  rule_name: string
  title: string
  description?: string
  severity: Severity
  confidence?: Confidence
  status: AlertStatus
  first_seen: string
  last_seen: string
  source_ip?: string
  destination_ip?: string
  ap_id?: string
  switch_id?: string
  event_count: number
  assigned_to?: string
  simulated: boolean
  evidence?: Record<string, unknown>
  recommended_steps?: string
  notes?: AlertNote[]
  acknowledged_at?: string
  resolved_at?: string
}

export interface AlertNote {
  author: string
  content: string
  created_at: string
}

export interface NetworkAsset {
  id: string
  asset_type: string
  name: string
  hostname?: string
  ip_address?: string
  mac_address?: string
  vendor?: string
  location?: string
  ap_id?: string
  ssid?: string
  switch_id?: string
  switch_port?: string
  vlan_id?: string
  is_authorized: boolean
  status: string
  last_seen?: string
  recent_event_count?: number
  open_alert_count?: number
}

export interface DetectionRule {
  id: string
  name: string
  description?: string
  category?: string
  enabled: boolean
  severity: Severity
  confidence: Confidence
  detection_window_seconds: number
  threshold?: number
  cooldown_seconds: number
  alert_count: number
  last_triggered?: string
  extra_config?: Record<string, unknown>
}

export interface DataSource {
  id: string
  name: string
  source_type: string
  is_simulated: boolean
  is_enabled: boolean
  status: string
  last_event_at?: string
  events_total: number
  events_last_minute: number
  parse_failures: number
}

export interface OverviewMetrics {
  total_events: number
  events_per_minute: number
  new_alerts: number
  high_critical_alerts: number
  monitored_aps: number
  monitored_switches: number
  event_volume_24h: { hour: string; count: number }[]
  recent_alerts: Alert[]
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

export interface AlertSummary {
  total: number
  high_critical_unresolved: number
  by_severity: Record<string, number>
  by_status: Record<string, number>
  top_rules: { rule: string; count: number }[]
}

export interface WsMessage {
  type: 'event.new' | 'alert.new' | 'alert.updated'
  data: Partial<NetworkEvent & Alert>
}
