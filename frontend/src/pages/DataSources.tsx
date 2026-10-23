import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import type { DataSource } from '@/types'
import { timeAgo } from '@/lib/utils'
import {
  Database, Play, Pause, Zap, Activity, CheckCircle2,
  AlertCircle, RefreshCw, Cpu, Radio, ShieldAlert,
  Server, FileText, Wifi, ArrowUpRight
} from 'lucide-react'

interface SourcesResponse {
  items: DataSource[]
}

interface SyntheticStatus {
  running: boolean
  paused: boolean
  events_per_second: number
  anomaly_rate: number
}

const SOURCE_TYPE_ICONS: Record<string, React.ElementType> = {
  zeek: FileText,
  syslog: Server,
  synthetic: Cpu,
  dhcp: Wifi,
  radius: Radio,
  netflow: Activity,
}

export default function DataSources() {
  const { data: sourcesData, loading: sourcesLoading, refetch: refetchSources } =
    useApi<SourcesResponse>('/api/sources')

  const { data: synthStatus, refetch: refetchSynth } =
    useApi<SyntheticStatus>('/api/synthetic/status')

  const [triggeringScenario, setTriggeringScenario] = useState<string | null>(null)
  const [triggerNotification, setTriggerNotification] = useState<string | null>(null)
  const [rateInput, setRateInput] = useState<number>(synthStatus?.events_per_second || 2)

  const isPaused = synthStatus?.paused ?? false
  const isRunning = synthStatus?.running ?? true

  const handleTogglePause = async () => {
    try {
      if (isPaused) {
        await api.post('/api/synthetic/resume')
      } else {
        await api.post('/api/synthetic/pause')
      }
      refetchSynth()
    } catch (err) {
      console.error('Failed to toggle generator status:', err)
    }
  }

  const handleUpdateRate = async (rate: number) => {
    try {
      setRateInput(rate)
      await api.post('/api/synthetic/rate', { events_per_second: rate })
      refetchSynth()
    } catch (err) {
      console.error('Failed to adjust generator rate:', err)
    }
  }

  const handleTrigger = async (
    endpoint: string,
    name: string,
    payload?: Record<string, unknown>
  ) => {
    setTriggeringScenario(name)
    try {
      const res = await api.post<{ triggered?: string; events_generated?: number }>(
        `/api/synthetic/trigger/${endpoint}`,
        payload || {}
      )
      const count = res.events_generated ? ` (${res.events_generated} events)` : ''
      setTriggerNotification(`Successfully triggered ${name}${count}!`)
      setTimeout(() => setTriggerNotification(null), 4000)
      refetchSources()
    } catch (err) {
      console.error(`Failed to trigger ${name}:`, err)
      setTriggerNotification(`Failed to trigger ${name}`)
      setTimeout(() => setTriggerNotification(null), 4000)
    } finally {
      setTriggeringScenario(null)
    }
  }

  const sources = sourcesData?.items ?? []
  const totalEvents = sources.reduce((acc, s) => acc + (s.events_total || 0), 0)
  const totalRate = sources.reduce((acc, s) => acc + (s.events_last_minute || 0), 0)

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Data Sources & Ingestion</h1>
          <p className="page-subtitle">
            Telemetry ingestion pipelines, log feeds, and synthetic network simulation engine
          </p>
        </div>
        <button
          onClick={() => {
            refetchSources()
            refetchSynth()
          }}
          className="btn btn-secondary text-xs"
          title="Refresh feeds"
        >
          <RefreshCw
            size={14}
            className={sourcesLoading ? 'animate-spin' : ''}
          />
          Refresh
        </button>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Active Sources</p>
              <p className="stat-value mt-1">{sources.length}</p>
              <p className="text-xs text-gray-500 mt-1">Configured adapters</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Database size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Total Events Processed</p>
              <p className="stat-value mt-1 text-green-400">
                {totalEvents.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-1">Across all feeds</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-green-500/10 text-green-400 flex items-center justify-center">
              <CheckCircle2 size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Ingestion Velocity</p>
              <p className="stat-value mt-1 text-purple-400">{totalRate}/min</p>
              <p className="text-xs text-gray-500 mt-1">Real-time throughput</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Activity size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Generator State</p>
              <p className="stat-value mt-1 text-yellow-400">
                {isPaused ? 'Paused' : isRunning ? 'Active' : 'Offline'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {synthStatus?.events_per_second ?? 0} eps target
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-yellow-500/10 text-yellow-400 flex items-center justify-center">
              <Cpu size={20} />
            </div>
          </div>
        </div>
      </div>

      {/* Synthetic Generator Command Console */}
      <div className="card border-blue-500/30 bg-gradient-to-r from-navy-800 via-navy-800 to-navy-900">
        <div className="card-header pb-2 border-b border-navy-700/60">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
                <Zap size={18} />
              </div>
              <div>
                <h3 className="font-semibold text-white text-base flex items-center gap-2">
                  Synthetic Generator Command Center
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      isPaused ? 'bg-yellow-400' : 'bg-green-400 animate-pulse'
                    }`}
                  />
                </h3>
                <p className="text-xs text-gray-400">
                  Simulate live college campus traffic and inject attack scenarios to test detection rules
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleTogglePause}
                className={`btn text-xs ${
                  isPaused ? 'btn-primary' : 'btn-secondary'
                }`}
              >
                {isPaused ? (
                  <>
                    <Play size={14} /> Resume Simulation
                  </>
                ) : (
                  <>
                    <Pause size={14} /> Pause Generator
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-4 space-y-4">
          {/* Rate Controller */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-navy-900/60 rounded-xl border border-navy-700/40">
            <div className="flex items-center gap-4">
              <span className="text-xs font-medium text-gray-300">
                Generation Rate:
              </span>
              <div className="flex items-center gap-2">
                {[1, 2, 5, 10, 20].map(rate => (
                  <button
                    key={rate}
                    onClick={() => handleUpdateRate(rate)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      rateInput === rate
                        ? 'bg-blue-600 text-white font-bold'
                        : 'bg-navy-700 text-gray-300 hover:bg-navy-600'
                    }`}
                  >
                    {rate} eps
                  </button>
                ))}
              </div>
            </div>
            <div className="text-xs text-gray-400">
              Anomaly inject rate:{' '}
              <span className="font-mono text-blue-400">
                {Math.round((synthStatus?.anomaly_rate ?? 0.05) * 100)}%
              </span>
            </div>
          </div>

          {/* Trigger Notification Toast */}
          {triggerNotification && (
            <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-xl text-xs text-green-300 flex items-center gap-2 animate-fade-in">
              <CheckCircle2 size={16} />
              <span>{triggerNotification}</span>
            </div>
          )}

          {/* Attack Scenario Trigger Buttons */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
              Inject Attack Scenarios (Instant Evaluation)
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <button
                onClick={() => handleTrigger('port-scan', 'Port Scan Attack')}
                disabled={triggeringScenario !== null}
                className="card p-3 hover:border-red-500/50 hover:bg-red-500/5 transition-all text-left group"
              >
                <div className="flex items-center justify-between text-red-400 mb-1">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    <ShieldAlert size={14} /> Port Scan
                  </span>
                  <ArrowUpRight
                    size={14}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  />
                </div>
                <p className="text-[11px] text-gray-400">
                  Rapid TCP probe across 40+ ports to trigger RULE-002
                </p>
              </button>

              <button
                onClick={() => handleTrigger('dns-spike', 'DNS Exfiltration Spike', { count: 80 })}
                disabled={triggeringScenario !== null}
                className="card p-3 hover:border-orange-500/50 hover:bg-orange-500/5 transition-all text-left group"
              >
                <div className="flex items-center justify-between text-orange-400 mb-1">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    <Radio size={14} /> DNS Exfil Spike
                  </span>
                  <ArrowUpRight
                    size={14}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  />
                </div>
                <p className="text-[11px] text-gray-400">
                  Subdomain tunneling flood to trigger RULE-001
                </p>
              </button>

              <button
                onClick={() => handleTrigger('brute-force', 'SSH/Web Brute Force', { count: 25 })}
                disabled={triggeringScenario !== null}
                className="card p-3 hover:border-yellow-500/50 hover:bg-yellow-500/5 transition-all text-left group"
              >
                <div className="flex items-center justify-between text-yellow-400 mb-1">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    <Zap size={14} /> Auth Brute Force
                  </span>
                  <ArrowUpRight
                    size={14}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  />
                </div>
                <p className="text-[11px] text-gray-400">
                  Multiple auth failures in short burst to trigger RULE-003
                </p>
              </button>

              <button
                onClick={() => handleTrigger('bandwidth-anomaly', 'Data Exfiltration Bandwidth')}
                disabled={triggeringScenario !== null}
                className="card p-3 hover:border-purple-500/50 hover:bg-purple-500/5 transition-all text-left group"
              >
                <div className="flex items-center justify-between text-purple-400 mb-1">
                  <span className="text-xs font-bold flex items-center gap-1.5">
                    <Activity size={14} /> Bandwidth Surge
                  </span>
                  <ArrowUpRight
                    size={14}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  />
                </div>
                <p className="text-[11px] text-gray-400">
                  Massive outbound payload transfer to trigger RULE-004
                </p>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Sources Table */}
      <div className="card p-0 overflow-hidden">
        <div className="p-4 border-b border-navy-700 bg-navy-900/60 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
            <Database size={16} className="text-blue-400" />
            Configured Data Feeds & Adapters
          </h2>
          <span className="text-xs text-gray-400">
            {sources.length} sources registered
          </span>
        </div>

        <div className="table-container">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-navy-700 bg-navy-900/40">
                <th className="table-head">Feed Name</th>
                <th className="table-head">Type</th>
                <th className="table-head">Simulation Mode</th>
                <th className="table-head">Status</th>
                <th className="table-head">Throughput</th>
                <th className="table-head">Total Ingested</th>
                <th className="table-head">Parse Errors</th>
                <th className="table-head">Last Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-700/50">
              {sourcesLoading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500 text-sm">
                    Loading telemetry sources…
                  </td>
                </tr>
              ) : sources.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-gray-500 text-sm">
                    No data sources configured.
                  </td>
                </tr>
              ) : (
                sources.map(s => {
                  const Icon = SOURCE_TYPE_ICONS[s.source_type] || Database
                  return (
                    <tr key={s.id} className="table-row">
                      <td className="table-cell">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-navy-700 border border-navy-600 flex items-center justify-center text-blue-400">
                            <Icon size={16} />
                          </div>
                          <div>
                            <p className="font-medium text-gray-200 text-sm">{s.name}</p>
                            <p className="text-[11px] font-mono text-gray-500">{s.id}</p>
                          </div>
                        </div>
                      </td>

                      <td className="table-cell">
                        <span className="font-mono text-xs text-gray-300 uppercase">
                          {s.source_type}
                        </span>
                      </td>

                      <td className="table-cell">
                        {s.is_simulated ? (
                          <span className="badge bg-yellow-500/10 text-yellow-400 border border-yellow-500/30">
                            Simulated Traffic
                          </span>
                        ) : (
                          <span className="badge bg-green-500/10 text-green-400 border border-green-500/30">
                            Real Telemetry
                          </span>
                        )}
                      </td>

                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              s.status === 'healthy' || s.status === 'online'
                                ? 'bg-green-400'
                                : 'bg-gray-500'
                            }`}
                          />
                          <span className="text-xs capitalize text-gray-300">
                            {s.status}
                          </span>
                        </div>
                      </td>

                      <td className="table-cell">
                        <span className="font-mono text-xs text-purple-400">
                          {s.events_last_minute}/min
                        </span>
                      </td>

                      <td className="table-cell">
                        <span className="font-mono text-xs text-gray-200">
                          {s.events_total?.toLocaleString() ?? 0}
                        </span>
                      </td>

                      <td className="table-cell">
                        <span
                          className={`font-mono text-xs ${
                            s.parse_failures > 0 ? 'text-red-400' : 'text-gray-500'
                          }`}
                        >
                          {s.parse_failures}
                        </span>
                      </td>

                      <td className="table-cell text-xs text-gray-400">
                        {timeAgo(s.last_event_at)}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* College Hybrid Ingestion Notice */}
      <div className="card bg-navy-800/60 border-navy-700 flex items-start gap-3 p-4">
        <AlertCircle size={20} className="text-blue-400 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-300 space-y-1">
          <p className="font-semibold text-white">Hybrid Telemetry Architecture</p>
          <p className="text-gray-400">
            NetSentinel supports dual-mode ingestion. During development and demonstration on Antigravity IDE,
            synthetic generation produces realistic college campus patterns (classes, dorm traffic, lab activity).
            Once the institution authorizes switch and firewall tap access, syslog and Zeek forwarders can be pointed
            directly at this instance with zero code changes.
          </p>
        </div>
      </div>
    </div>
  )
}
