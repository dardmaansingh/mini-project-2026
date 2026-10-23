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
    <div className="p-4 space-y-4 animate-fade-in">
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
      <div className="card shadow-sm">
        <div className="card-header pb-2 border-b border-gray-100">
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded bg-green-50 text-green-700 flex items-center justify-center">
                <Zap size={16} />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm flex items-center gap-2">
                  Synthetic Generator Command Center
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${
                      isPaused ? 'bg-yellow-500' : 'bg-green-500 animate-pulse'
                    }`}
                  />
                </h3>
                <p className="text-xs text-gray-500">
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

        <div className="mt-3 space-y-3">
          {/* Rate Controller */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-3 bg-gray-50 rounded border border-gray-200">
            <div className="flex items-center gap-4">
              <span className="text-xs font-semibold text-gray-700">
                Generation Rate:
              </span>
              <div className="flex items-center gap-2">
                {[1, 2, 5, 10, 20].map(rate => (
                  <button
                    key={rate}
                    onClick={() => handleUpdateRate(rate)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-colors ${
                      rateInput === rate
                        ? 'bg-green-700 text-white font-bold'
                        : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100'
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
      <div className="card shadow-sm p-0 overflow-hidden">
        <div className="p-3 border-b border-[#EDF0F4] bg-[#F8FAFC] flex items-center justify-between">
          <h2 className="text-xs font-semibold text-gray-700 uppercase tracking-wider flex items-center gap-2">
            <Database size={14} className="text-gray-500" />
            Configured Data Feeds & Adapters
          </h2>
          <span className="text-xs text-gray-500 font-mono">
            {sources.length} sources registered
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 220 }}>Feed Name</th>
                <th style={{ width: 110 }}>Type</th>
                <th style={{ width: 130 }}>Simulation Mode</th>
                <th style={{ width: 100 }}>Status</th>
                <th style={{ width: 110 }}>Throughput</th>
                <th style={{ width: 120 }}>Total Ingested</th>
                <th style={{ width: 90 }}>Errors</th>
                <th>Last Active</th>
              </tr>
            </thead>
            <tbody>
              {sourcesLoading ? (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-gray-400 text-xs">
                    Loading telemetry sources…
                  </td>
                </tr>
              ) : sources.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-10 text-center text-gray-400 text-xs">
                    No data sources configured.
                  </td>
                </tr>
              ) : (
                sources.map(s => {
                  const Icon = SOURCE_TYPE_ICONS[s.source_type] || Database
                  return (
                    <tr key={s.id}>
                      <td>
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded bg-gray-100 border border-gray-200 flex items-center justify-center text-green-700 shrink-0">
                            <Icon size={14} />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 text-xs">{s.name}</p>
                            <p className="text-[10px] font-mono text-gray-400">{s.id}</p>
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="font-mono text-xs text-gray-700 uppercase">
                          {s.source_type}
                        </span>
                      </td>

                      <td>
                        {s.is_simulated ? (
                          <span className="badge badge-medium">
                            Simulated
                          </span>
                        ) : (
                          <span className="badge badge-green">
                            Real Wire
                          </span>
                        )}
                      </td>

                      <td>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              s.status === 'healthy' || s.status === 'online'
                                ? 'bg-green-500'
                                : 'bg-gray-400'
                            }`}
                          />
                          <span className="text-xs capitalize text-gray-700 font-medium">
                            {s.status}
                          </span>
                        </div>
                      </td>

                      <td>
                        <span className="font-mono text-xs text-purple-700 font-semibold">
                          {s.events_last_minute}/min
                        </span>
                      </td>

                      <td>
                        <span className="font-mono text-xs text-gray-900 font-semibold">
                          {s.events_total?.toLocaleString() ?? 0}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`font-mono text-xs font-semibold ${
                            s.parse_failures > 0 ? 'text-red-600' : 'text-gray-400'
                          }`}
                        >
                          {s.parse_failures}
                        </span>
                      </td>

                      <td className="text-xs text-gray-500 font-mono">
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
      <div className="card shadow-sm flex items-start gap-3 p-4">
        <AlertCircle size={18} className="text-green-700 shrink-0 mt-0.5" />
        <div className="text-xs text-gray-700 space-y-1">
          <p className="font-semibold text-gray-900">Hybrid Telemetry Architecture</p>
          <p className="text-gray-600">
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
