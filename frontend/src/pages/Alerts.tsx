import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import type { Alert, PaginatedResponse } from '@/types'
import { formatTs, timeAgo, severityClass, statusClass } from '@/lib/utils'
import { AlertTriangle, ChevronLeft, ChevronRight, RefreshCw, FileText, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'

const SEVERITIES = ['all', 'critical', 'high', 'medium', 'low', 'informational']
const STATUSES   = ['all', 'new', 'acknowledged', 'investigating', 'resolved', 'false_positive']

const SEV_BORDER: Record<string, string> = {
  critical:      '#DC2626',
  high:          '#EA580C',
  medium:        '#D97706',
  low:           '#0284C7',
  informational: '#64748B',
}

export default function Alerts() {
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState('all')
  const [status, setStatus] = useState('all')
  const [selected, setSelected] = useState<Alert | null>(null)
  const [updating, setUpdating] = useState(false)
  const [note, setNote] = useState('')

  const buildPath = () => {
    const p = new URLSearchParams({ page: String(page), page_size: '50' })
    if (severity !== 'all') p.set('severity', severity)
    if (status !== 'all')   p.set('status', status)
    return `/api/alerts?${p}`
  }

  const { data, loading, refetch } = useApi<PaginatedResponse<Alert>>(
    buildPath(), { deps: [page, severity, status] }
  )
  const totalPages = data ? Math.ceil(data.total / 50) : 1

  async function updateAlert(alertId: string, body: Record<string, unknown>) {
    setUpdating(true)
    try {
      const updated = await api.patch<Alert>(`/api/alerts/${alertId}`, body)
      setSelected(updated)
      refetch()
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className="p-4 space-y-3 animate-fade-in text-gray-900">

      {/* Filter Ribbon (White Card) */}
      <div className="card shadow-sm flex flex-wrap items-center justify-between gap-3 py-2 px-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-gray-600">Filters:</span>
          <select
            className="select w-auto text-xs py-1 px-2 shadow-sm"
            value={severity}
            onChange={e => { setSeverity(e.target.value); setPage(1) }}
          >
            {SEVERITIES.map(s => (
              <option key={s} value={s}>{s === 'all' ? 'All severities' : s.toUpperCase()}</option>
            ))}
          </select>
          <select
            className="select w-auto text-xs py-1 px-2 shadow-sm"
            value={status}
            onChange={e => { setStatus(e.target.value); setPage(1) }}
          >
            {STATUSES.map(s => (
              <option key={s} value={s}>{s === 'all' ? 'All statuses' : s.replace('_', ' ').toUpperCase()}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono font-medium">
            {data?.total ?? 0} total incidents
          </span>
          <button onClick={refetch} className="btn btn-secondary text-xs py-1 px-2.5 shadow-sm">
            <RefreshCw size={12} className={loading ? 'animate-spin text-green-600' : 'text-gray-500'} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">

        {/* ── Alert table (Crisp White Card) ────────────────────── */}
        <div className="card xl:col-span-2 shadow-sm p-0 overflow-hidden flex flex-col justify-between">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 85 }}>Severity</th>
                  <th>Threat & Alert Title</th>
                  <th style={{ width: 120 }}>Source IP</th>
                  <th style={{ width: 70 }}>Events</th>
                  <th style={{ width: 90 }}>First Seen</th>
                  <th style={{ width: 95 }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr>
                    <td colSpan={6} className="text-center py-10 text-gray-400">
                      Loading alert queue…
                    </td>
                  </tr>
                )}
                {!loading && data?.items.map(a => (
                  <tr
                    key={a.id}
                    style={{
                      cursor: 'pointer',
                      borderLeft: selected?.id === a.id
                        ? `3px solid ${SEV_BORDER[a.severity] ?? '#237A3B'}`
                        : '3px solid transparent',
                      backgroundColor: selected?.id === a.id ? '#F0FDF4' : undefined,
                    }}
                    onClick={() => setSelected(a)}
                  >
                    <td>
                      <span className={severityClass(a.severity)}>{a.severity}</span>
                    </td>
                    <td style={{ maxWidth: 220 }}>
                      <span className="truncate font-semibold text-gray-800 block text-xs">
                        {a.title}
                      </span>
                      <span className="text-[10px] text-gray-500 block truncate">
                        {a.rule_id}
                      </span>
                    </td>
                    <td className="font-mono text-gray-800 font-medium text-xs">
                      {a.source_ip ?? '—'}
                    </td>
                    <td className="font-mono text-gray-600 text-xs text-center font-semibold">
                      {a.event_count}
                    </td>
                    <td className="font-mono text-gray-500 text-[11px]">
                      {timeAgo(a.first_seen)}
                    </td>
                    <td>
                      <span className={statusClass(a.status)}>
                        {a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination bar */}
          <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-t border-gray-200 text-xs">
            <span className="text-gray-500 font-mono">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-1">
              <button
                className="btn btn-secondary text-xs py-0.5 px-2"
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft size={12} />
              </button>
              <button
                className="btn btn-secondary text-xs py-0.5 px-2"
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight size={12} />
              </button>
            </div>
          </div>
        </div>

        {/* ── Detail / triage panel (White Card) ────────────────── */}
        <div className="card shadow-sm p-0 overflow-hidden flex flex-col">
          <div className="flex items-center gap-2 px-3 py-2.5 bg-[#F8FAFC] border-b border-[#D8DEE4]">
            <FileText size={13} className="text-gray-500" />
            <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Alert Inspection & Remediation
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-3">
            {!selected ? (
              <div className="flex flex-col items-center justify-center gap-2 h-48 text-gray-400">
                <AlertTriangle size={24} className="text-gray-300" />
                <span className="text-xs">Select an alert from the table to inspect</span>
              </div>
            ) : (
              <div className="space-y-3">

                {/* Title + severity */}
                <div
                  style={{
                    borderLeft: `3px solid ${SEV_BORDER[selected.severity] ?? '#237A3B'}`,
                    paddingLeft: 10,
                  }}
                >
                  <span className={severityClass(selected.severity)}>{selected.severity}</span>
                  <h3 className="text-xs font-bold text-gray-900 mt-1 leading-snug">
                    {selected.title}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1">{selected.description}</p>
                </div>

                {/* Metadata grid */}
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    ['Rule ID',    selected.rule_id],
                    ['Confidence', selected.confidence],
                    ['Source IP',  selected.source_ip],
                    ['Dest IP',    selected.destination_ip],
                    ['AP / Sensor', selected.ap_id],
                    ['Events',     String(selected.event_count)],
                    ['First Seen', formatTs(selected.first_seen)],
                    ['Last Seen',  formatTs(selected.last_seen)],
                  ].map(([k, v]) => (
                    <div
                      key={k}
                      className="bg-gray-50 border border-gray-200 rounded p-1.5"
                    >
                      <p className="text-[9px] text-gray-500 uppercase font-semibold">{k}</p>
                      <p className="font-mono text-gray-900 text-xs mt-0.5 break-all">{v ?? '—'}</p>
                    </div>
                  ))}
                </div>

                {/* Evidence */}
                {selected.evidence && (
                  <div>
                    <p className="text-[10px] text-gray-500 uppercase font-semibold mb-1">
                      Evidence Telemetry
                    </p>
                    <pre className="text-[10px] text-gray-800 font-mono bg-gray-50 border border-gray-200 rounded p-2 overflow-x-auto leading-relaxed">
                      {JSON.stringify(selected.evidence, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Recommended steps */}
                {selected.recommended_steps && (
                  <div>
                    <p className="text-[10px] text-gray-500 uppercase font-semibold mb-1">
                      Recommended Remediation Steps
                    </p>
                    <ol className="space-y-1">
                      {selected.recommended_steps.split('\n').filter(Boolean).map((s, i) => (
                        <li key={i} className="flex gap-2 text-xs text-gray-700">
                          <span className="text-green-700 font-bold shrink-0">{i + 1}.</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Status actions */}
                <div>
                  <p className="text-[10px] text-gray-500 uppercase font-semibold mb-1.5">
                    Update Workflow Status
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {['acknowledged', 'investigating', 'resolved', 'false_positive'].map(s => (
                      <button
                        key={s}
                        disabled={updating || selected.status === s}
                        className="btn btn-secondary text-xs py-1 px-2.5 shadow-sm"
                        onClick={() => updateAlert(selected.id, { status: s })}
                      >
                        {s === 'resolved' && <CheckCircle size={11} className="text-green-600 mr-1" />}
                        {s.replace('_', ' ').toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Add analyst note */}
                <div>
                  <p className="text-[10px] text-gray-500 uppercase font-semibold mb-1">
                    Analyst Investigation Note
                  </p>
                  <textarea
                    className="input h-16 text-xs resize-none"
                    placeholder="Enter analyst triage notes…"
                    value={note}
                    onChange={e => setNote(e.target.value)}
                  />
                  <button
                    className="btn btn-primary mt-1.5 text-xs py-1 px-3 shadow-sm"
                    disabled={!note.trim() || updating}
                    onClick={() => { updateAlert(selected.id, { note, author: 'analyst' }); setNote('') }}
                  >
                    Save Note
                  </button>
                </div>

                {/* Existing notes */}
                {selected.notes?.length ? (
                  <div>
                    <p className="text-[10px] text-gray-500 uppercase font-semibold mb-1">
                      Case Notes ({selected.notes.length})
                    </p>
                    <div className="space-y-1.5">
                      {selected.notes.map((n, i) => (
                        <div
                          key={i}
                          className="bg-gray-50 border border-gray-200 rounded p-2 text-xs"
                        >
                          <p className="text-[10px] text-gray-500 font-semibold">{n.author} · {formatTs(n.created_at)}</p>
                          <p className="text-gray-800 mt-1">{n.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  )
}
