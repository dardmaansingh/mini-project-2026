import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import { timeAgo, formatTs } from '@/lib/utils'
import {
  Settings as SettingsIcon, Shield, Server, Bell, Database,
  Terminal, CheckCircle2, AlertTriangle, RefreshCw, Save,
  Key, Radio, Clock, UserCheck
} from 'lucide-react'

interface HealthResponse {
  status: string
  service: string
  version: string
  timestamp: string
}

interface AuditResponse {
  total: number
  items: {
    id: string
    actor: string
    action: string
    resource_type?: string
    resource_id?: string
    details?: Record<string, unknown>
    created_at: string
  }[]
}

export default function Settings() {
  const { data: health, loading: healthLoading, refetch: refetchHealth } =
    useApi<HealthResponse>('/api/health')

  const { data: auditData, loading: auditLoading, refetch: refetchAudit } =
    useApi<AuditResponse>('/api/audit-logs?page_size=15')

  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'audit' | 'authorization'>('general')
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Demo settings form state
  const [settingsForm, setSettingsForm] = useState({
    collegeName: 'Campus University Institute of Technology',
    socAnalystName: 'Lead SOC Analyst (SecOps)',
    eventRetentionDays: 30,
    alertRetentionDays: 90,
    wsBufferLimit: 500,
    emailAlertsEnabled: true,
    emailRecipients: 'soc-team@college.edu',
    slackWebhook: 'https://hooks.slack.com/services/T00/B00/XXXX',
    discordWebhook: '',
    minAlertSeverity: 'high',
  })

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSaveSuccess(true)
    setTimeout(() => setSaveSuccess(false), 3000)
  }

  return (
    <div className="p-4 space-y-4 animate-fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">System Settings & Governance</h1>
          <p className="page-subtitle">
            NetSentinel configuration, audit logs, notification channels, and college deployment policies
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-white border border-[#D8DEE4] text-xs shadow-sm">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-gray-500">Backend:</span>
            <span className="font-semibold text-gray-900 font-mono">
              {health?.status ?? 'Connecting…'} (v{health?.version ?? '2.0'})
            </span>
          </div>
        </div>
      </div>

      {/* Settings Navigation Tabs */}
      <div className="flex border-b border-[#D8DEE4] gap-6 text-xs font-semibold uppercase tracking-wider">
        <button
          onClick={() => setActiveTab('general')}
          className={`pb-2.5 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'general'
              ? 'border-green-700 text-green-700 font-bold'
              : 'border-transparent text-gray-500 hover:text-gray-900'
          }`}
        >
          <SettingsIcon size={14} />
          General & Retention
        </button>

        <button
          onClick={() => setActiveTab('notifications')}
          className={`pb-2.5 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'notifications'
              ? 'border-green-700 text-green-700 font-bold'
              : 'border-transparent text-gray-500 hover:text-gray-900'
          }`}
        >
          <Bell size={14} />
          Alert Channels
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'audit'
              ? 'border-blue-500 text-blue-400 font-semibold'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <Terminal size={16} />
          SOC Audit Trail
        </button>

        <button
          onClick={() => setActiveTab('authorization')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'authorization'
              ? 'border-blue-500 text-blue-400 font-semibold'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <Shield size={16} />
          Institutional Scope & Disclaimer
        </button>
      </div>

      {/* Tab: General Settings */}
      {activeTab === 'general' && (
        <form onSubmit={handleSave} className="space-y-6 max-w-4xl">
          <div className="card space-y-4">
            <h3 className="card-title">
              <Server size={16} className="text-blue-400" />
              Instance Identity & Organization
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Institution / Organization Name
                </label>
                <input
                  type="text"
                  value={settingsForm.collegeName}
                  onChange={e =>
                    setSettingsForm({ ...settingsForm, collegeName: e.target.value })
                  }
                  className="input w-full"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Default SOC Operator Alias
                </label>
                <input
                  type="text"
                  value={settingsForm.socAnalystName}
                  onChange={e =>
                    setSettingsForm({ ...settingsForm, socAnalystName: e.target.value })
                  }
                  className="input w-full"
                />
              </div>
            </div>
          </div>

          <div className="card space-y-4">
            <h3 className="card-title">
              <Database size={16} className="text-purple-400" />
              Data Retention & Memory Limits
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Raw Event Retention (Days)
                </label>
                <input
                  type="number"
                  min="7"
                  max="365"
                  value={settingsForm.eventRetentionDays}
                  onChange={e =>
                    setSettingsForm({
                      ...settingsForm,
                      eventRetentionDays: parseInt(e.target.value) || 30,
                    })
                  }
                  className="input w-full font-mono text-xs"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Stored in PostgreSQL partitions.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Security Alerts Retention (Days)
                </label>
                <input
                  type="number"
                  min="30"
                  max="730"
                  value={settingsForm.alertRetentionDays}
                  onChange={e =>
                    setSettingsForm({
                      ...settingsForm,
                      alertRetentionDays: parseInt(e.target.value) || 90,
                    })
                  }
                  className="input w-full font-mono text-xs"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Incident triage records & evidence.
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  WebSocket Ring Buffer
                </label>
                <input
                  type="number"
                  min="100"
                  max="5000"
                  value={settingsForm.wsBufferLimit}
                  onChange={e =>
                    setSettingsForm({
                      ...settingsForm,
                      wsBufferLimit: parseInt(e.target.value) || 500,
                    })
                  }
                  className="input w-full font-mono text-xs"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  In-memory queue size for connected browsers.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {saveSuccess ? (
              <span className="text-xs text-green-400 flex items-center gap-1.5 bg-green-500/10 px-3 py-1.5 rounded-lg border border-green-500/20">
                <CheckCircle2 size={14} /> Settings updated successfully
              </span>
            ) : (
              <span />
            )}
            <button type="submit" className="btn btn-primary text-xs">
              <Save size={14} />
              Save Configuration
            </button>
          </div>
        </form>
      )}

      {/* Tab: Alert Notifications */}
      {activeTab === 'notifications' && (
        <form onSubmit={handleSave} className="space-y-6 max-w-4xl">
          <div className="card space-y-4">
            <h3 className="card-title">
              <Bell size={16} className="text-yellow-400" />
              Automated Alert Dispatch
            </h3>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded border border-gray-200">
                <div>
                  <p className="text-xs font-semibold text-gray-900">Email Notifications</p>
                  <p className="text-xs text-gray-500">
                    Send immediate incident digests when critical or high severity alerts fire
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={settingsForm.emailAlertsEnabled}
                  onChange={e =>
                    setSettingsForm({
                      ...settingsForm,
                      emailAlertsEnabled: e.target.checked,
                    })
                  }
                  className="rounded border-gray-300 bg-white text-green-700 h-4 w-4"
                />
              </div>

              {settingsForm.emailAlertsEnabled && (
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    SOC Dispatch Mailing List
                  </label>
                  <input
                    type="email"
                    value={settingsForm.emailRecipients}
                    onChange={e =>
                      setSettingsForm({ ...settingsForm, emailRecipients: e.target.value })
                    }
                    className="input w-full"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Slack Webhook Endpoint
                </label>
                <input
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  value={settingsForm.slackWebhook}
                  onChange={e =>
                    setSettingsForm({ ...settingsForm, slackWebhook: e.target.value })
                  }
                  className="input w-full font-mono text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">
                  Minimum Severity for Webhook Dispatch
                </label>
                <select
                  value={settingsForm.minAlertSeverity}
                  onChange={e =>
                    setSettingsForm({ ...settingsForm, minAlertSeverity: e.target.value })
                  }
                  className="select w-full capitalize"
                >
                  <option value="critical">Critical Only</option>
                  <option value="high">High & Critical</option>
                  <option value="medium">Medium, High & Critical</option>
                  <option value="low">All Severities</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            {saveSuccess ? (
              <span className="text-xs text-green-400 flex items-center gap-1.5 bg-green-500/10 px-3 py-1.5 rounded-lg border border-green-500/20">
                <CheckCircle2 size={14} /> Notification channels saved
              </span>
            ) : (
              <span />
            )}
            <button type="submit" className="btn btn-primary text-xs">
              <Save size={14} />
              Save Notification Settings
            </button>
          </div>
        </form>
      )}

      {/* Tab: SOC Audit Trail */}
      {activeTab === 'audit' && (
        <div className="space-y-4">
          <div className="card shadow-sm p-0 overflow-hidden">
            <div className="p-3 border-b border-[#EDF0F4] bg-[#F8FAFC] flex items-center justify-between">
              <div>
                <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider flex items-center gap-2">
                  <Terminal size={14} className="text-gray-500" />
                  SecOps Audit Trail
                </h3>
                <p className="text-[11px] text-gray-500 mt-0.5">
                  Tamper-evident record of analyst actions, rule modifications, and alert resolutions
                </p>
              </div>
              <button
                onClick={() => refetchAudit()}
                className="btn btn-secondary text-xs py-1 px-2.5 shadow-sm"
              >
                <RefreshCw size={12} className={auditLoading ? 'animate-spin text-green-700' : 'text-gray-500'} />
                Refresh
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: 140 }}>Timestamp</th>
                    <th style={{ width: 120 }}>Actor</th>
                    <th style={{ width: 120 }}>Action</th>
                    <th style={{ width: 160 }}>Target Resource</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLoading ? (
                    <tr>
                      <td colSpan={5} className="py-10 text-center text-gray-400 text-xs">
                        Loading audit log trail…
                      </td>
                    </tr>
                  ) : (auditData?.items ?? []).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-10 text-center text-gray-400 text-xs">
                        No audit events logged yet.
                      </td>
                    </tr>
                  ) : (
                    auditData?.items.map(log => (
                      <tr key={log.id}>
                        <td className="font-mono text-gray-500 text-[11px]">
                          {formatTs(log.created_at)}
                        </td>
                        <td>
                          <span className="font-semibold text-gray-900 text-xs flex items-center gap-1.5">
                            <UserCheck size={13} className="text-green-700" />
                            {log.actor}
                          </span>
                        </td>
                        <td>
                          <span className="badge badge-info">
                            {log.action}
                          </span>
                        </td>
                        <td className="text-xs text-gray-600">
                          {log.resource_type ? `${log.resource_type}: ` : ''}
                          <span className="font-mono text-gray-800 font-medium">
                            {log.resource_id || '—'}
                          </span>
                        </td>
                        <td className="text-xs text-gray-500 font-mono max-w-xs truncate">
                          {log.details ? JSON.stringify(log.details) : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Institutional Authorization & Scope */}
      {activeTab === 'authorization' && (
        <div className="card shadow-sm space-y-4 max-w-4xl border-[#D8DEE4]">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-green-50 text-green-700 flex items-center justify-center shrink-0">
              <Shield size={22} />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-gray-900">
                Institutional Deployment & Compliance Notice
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                NetSentinel is architected to operate within strict academic compliance guidelines (FERPA, GDPR, and institutional acceptable use policies).
              </p>
            </div>
          </div>

          <div className="p-4 bg-amber-50 rounded border border-amber-200 space-y-2 text-xs text-amber-900">
            <div className="flex items-center gap-2 text-amber-800 font-bold">
              <AlertTriangle size={15} />
              Current Status: Local Development & Synthetic Demonstration Phase
            </div>
            <p className="leading-relaxed text-amber-800/90">
              In accordance with project guidelines, live capture from physical switches, wireless controllers,
              and authentication radius logs remains isolated until explicit written authorization and log delegation
              is granted by the university IT security committee.
            </p>
            <p className="leading-relaxed text-amber-800/90">
              All alerts, anomalies, and traffic streams visible in this demonstration are synthesized through
              the high-fidelity simulation engine to mirror real-world campus scenarios (e.g. library WiFi roaming,
              lab port scans, and dormitory brute force attempts) without collecting student personally identifiable
              information (PII).
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="font-semibold text-gray-900 mb-1">Approved Telemetry Profiles</p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>Zeek conn.log, dns.log, dhcp.log</li>
                <li>Syslog UDP:514 (RFC 5424)</li>
                <li>NetFlow v9 / IPFIX (Sampled)</li>
                <li>802.1X RADIUS Auth Accounting</li>
              </ul>
            </div>

            <div className="p-3 bg-gray-50 rounded border border-gray-200">
              <p className="font-semibold text-gray-900 mb-1">Security Governance</p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>No student packet payloads stored</li>
                <li>DNS queries hashed after 30 days</li>
                <li>Full audit logging on alert changes</li>
                <li>Role-based SOC access controls</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
