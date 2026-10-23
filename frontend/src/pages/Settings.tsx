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
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">System Settings & Governance</h1>
          <p className="page-subtitle">
            NetSentinel configuration, audit logs, notification channels, and college deployment policies
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-800 border border-navy-700 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
              }`}
            />
            <span className="text-gray-400">Backend:</span>
            <span className="font-semibold text-gray-200">
              {health?.status ?? 'Connecting…'} (v{health?.version ?? '2.0'})
            </span>
          </div>
        </div>
      </div>

      {/* Settings Navigation Tabs */}
      <div className="flex border-b border-navy-700/80 gap-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab('general')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'general'
              ? 'border-blue-500 text-blue-400 font-semibold'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <SettingsIcon size={16} />
          General & Retention
        </button>

        <button
          onClick={() => setActiveTab('notifications')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'notifications'
              ? 'border-blue-500 text-blue-400 font-semibold'
              : 'border-transparent text-gray-400 hover:text-gray-200'
          }`}
        >
          <Bell size={16} />
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
              <div className="flex items-center justify-between p-3 bg-navy-900/60 rounded-xl border border-navy-700/50">
                <div>
                  <p className="text-sm font-medium text-gray-200">Email Notifications</p>
                  <p className="text-xs text-gray-400">
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
                  className="rounded border-navy-600 bg-navy-700 text-blue-500 h-5 w-5"
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
          <div className="card p-0 overflow-hidden">
            <div className="p-4 border-b border-navy-700 bg-navy-900/60 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                  <Terminal size={16} className="text-blue-400" />
                  SecOps Audit Trail
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Tamper-evident record of analyst actions, rule modifications, and alert resolutions
                </p>
              </div>
              <button
                onClick={() => refetchAudit()}
                className="btn btn-secondary text-xs"
              >
                <RefreshCw size={12} className={auditLoading ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>

            <div className="table-container">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-navy-700 bg-navy-900/40">
                    <th className="table-head">Timestamp</th>
                    <th className="table-head">Actor</th>
                    <th className="table-head">Action</th>
                    <th className="table-head">Target Resource</th>
                    <th className="table-head">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-navy-700/50">
                  {auditLoading ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-gray-500 text-sm">
                        Loading audit log trail…
                      </td>
                    </tr>
                  ) : (auditData?.items ?? []).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-gray-500 text-sm">
                        No audit events logged yet.
                      </td>
                    </tr>
                  ) : (
                    auditData?.items.map(log => (
                      <tr key={log.id} className="table-row">
                        <td className="table-cell font-mono text-xs text-gray-400">
                          {formatTs(log.created_at)}
                        </td>
                        <td className="table-cell">
                          <span className="font-medium text-gray-200 text-xs flex items-center gap-1.5">
                            <UserCheck size={12} className="text-blue-400" />
                            {log.actor}
                          </span>
                        </td>
                        <td className="table-cell">
                          <span className="badge bg-navy-700 text-gray-300 border border-navy-600 font-mono text-[11px]">
                            {log.action}
                          </span>
                        </td>
                        <td className="table-cell">
                          <span className="text-xs text-gray-400">
                            {log.resource_type ? `${log.resource_type}: ` : ''}
                            <span className="font-mono text-gray-300">
                              {log.resource_id || '—'}
                            </span>
                          </span>
                        </td>
                        <td className="table-cell text-xs text-gray-400 font-mono max-w-xs truncate">
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
        <div className="card space-y-4 max-w-4xl border-blue-500/30">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0">
              <Shield size={22} />
            </div>
            <div className="space-y-2">
              <h3 className="text-base font-bold text-white">
                Institutional Deployment & Compliance Notice
              </h3>
              <p className="text-xs text-gray-300 leading-relaxed">
                NetSentinel is architected to operate within strict academic compliance guidelines (FERPA, GDPR, and institutional acceptable use policies).
              </p>
            </div>
          </div>

          <div className="p-4 bg-navy-900/60 rounded-xl border border-navy-700 space-y-3 text-xs text-gray-300">
            <div className="flex items-center gap-2 text-yellow-400 font-semibold">
              <AlertTriangle size={16} />
              Current Status: Local Development & Synthetic Demonstration Phase
            </div>
            <p className="text-gray-400 leading-relaxed">
              In accordance with project guidelines, live capture from physical switches, wireless controllers,
              and authentication radius logs remains isolated until explicit written authorization and log delegation
              is granted by the university IT security committee.
            </p>
            <p className="text-gray-400 leading-relaxed">
              All alerts, anomalies, and traffic streams visible in this demonstration are synthesized through
              the high-fidelity simulation engine to mirror real-world campus scenarios (e.g. library WiFi roaming,
              lab port scans, and dormitory brute force attempts) without collecting student personally identifiable
              information (PII).
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-navy-800 rounded-xl border border-navy-700/60">
              <p className="font-semibold text-gray-200 mb-1">Approved Telemetry Profiles</p>
              <ul className="list-disc list-inside text-gray-400 space-y-1">
                <li>Zeek conn.log, dns.log, dhcp.log</li>
                <li>Syslog UDP:514 (RFC 5424)</li>
                <li>NetFlow v9 / IPFIX (Sampled)</li>
                <li>802.1X RADIUS Auth Accounting</li>
              </ul>
            </div>

            <div className="p-3 bg-navy-800 rounded-xl border border-navy-700/60">
              <p className="font-semibold text-gray-200 mb-1">Security Governance</p>
              <ul className="list-disc list-inside text-gray-400 space-y-1">
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
