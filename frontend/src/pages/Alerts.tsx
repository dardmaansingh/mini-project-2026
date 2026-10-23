import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import type { Alert, PaginatedResponse } from '@/types'
import { formatTs, timeAgo, severityClass, statusClass } from '@/lib/utils'
import { AlertTriangle, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import { api } from '@/lib/api'

const SEVERITIES = ['all', 'critical', 'high', 'medium', 'low', 'informational']
const STATUSES = ['all', 'new', 'acknowledged', 'investigating', 'resolved', 'false_positive']

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
    if (status !== 'all') p.set('status', status)
    return `/api/alerts?${p}`
  }

  const { data, loading, refetch } = useApi<PaginatedResponse<Alert>>(buildPath(), { deps: [page, severity, status] })
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
    <div className="p-6 space-y-4 animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Security Alerts</h2>
          <p className="page-subtitle">Investigate and manage security detections</p>
        </div>
        <button onClick={refetch} className="btn-secondary"><RefreshCw size={14} />Refresh</button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap gap-3">
          <select className="select" value={severity} onChange={e => { setSeverity(e.target.value); setPage(1) }}>
            {SEVERITIES.map(s => <option key={s} value={s}>{s === 'all' ? 'All severities' : s}</option>)}
          </select>
          <select className="select" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}>
            {STATUSES.map(s => <option key={s} value={s}>{s === 'all' ? 'All statuses' : s.replace('_', ' ')}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Alerts table */}
        <div className="xl:col-span-2 card p-0">
          <div className="table-container">
            <table className="w-full">
              <thead>
                <tr className="border-b border-navy-700">
                  <th className="table-head">Severity</th>
                  <th className="table-head">Title</th>
                  <th className="table-head">Source IP</th>
                  <th className="table-head">Rule</th>
                  <th className="table-head">Events</th>
                  <th className="table-head">First Seen</th>
                  <th className="table-head">Status</th>
                </tr>
              </thead>
              <tbody>
                {loading && <tr><td colSpan={7} className="py-12 text-center text-gray-500 text-sm">Loading…</td></tr>}
                {!loading && data?.items.map(a => (
                  <tr key={a.id}
                    className={`table-row cursor-pointer ${selected?.id === a.id ? 'bg-blue-500/5 border-l-2 border-blue-500' : ''}`}
                    onClick={() => setSelected(a)}>
                    <td className="table-cell"><span className={severityClass(a.severity)}>{a.severity}</span></td>
                    <td className="table-cell max-w-xs">
                      <div className="flex items-center gap-1.5">
                        {a.simulated && <span className="sim-dot" title="Simulated" />}
                        <span className="truncate font-medium text-gray-200 text-xs">{a.title}</span>
                      </div>
                    </td>
                    <td className="table-cell font-mono text-xs">{a.source_ip ?? '—'}</td>
                    <td className="table-cell text-xs text-gray-400">{a.rule_id}</td>
                    <td className="table-cell text-xs">{a.event_count}</td>
                    <td className="table-cell text-xs text-gray-400">{timeAgo(a.first_seen)}</td>
                    <td className="table-cell"><span className={statusClass(a.status)}>{a.status}</span></td>
                  </tr>
                ))}
                {!loading && !data?.items.length && (
                  <tr><td colSpan={7} className="py-12 text-center text-gray-500 text-sm">
                    <AlertTriangle size={28} className="mx-auto mb-2 text-gray-600" />No alerts match filters.
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between px-4 py-3 border-t border-navy-700">
            <span className="text-xs text-gray-500">{data?.total ?? 0} total</span>
            <div className="flex items-center gap-2">
              <button className="btn-secondary py-1 px-2" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={14} /></button>
              <span className="text-sm text-gray-400">{page} / {totalPages}</span>
              <button className="btn-secondary py-1 px-2" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}><ChevronRight size={14} /></button>
            </div>
          </div>
        </div>

        {/* Detail panel */}
        <div className="card space-y-4">
          {!selected ? (
            <div className="py-12 text-center text-gray-500 text-sm">
              <AlertTriangle size={28} className="mx-auto mb-2 text-gray-600" />
              Click an alert to investigate
            </div>
          ) : (
            <>
              <div>
                <span className={severityClass(selected.severity)}>{selected.severity}</span>
                <h3 className="text-base font-semibold text-white mt-2">{selected.title}</h3>
                <p className="text-xs text-gray-400 mt-1">{selected.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  ['Rule', selected.rule_id],
                  ['Confidence', selected.confidence],
                  ['Source IP', selected.source_ip],
                  ['Dest IP', selected.destination_ip],
                  ['AP', selected.ap_id],
                  ['Events', String(selected.event_count)],
                  ['First Seen', formatTs(selected.first_seen)],
                  ['Last Seen', formatTs(selected.last_seen)],
                ].map(([k, v]) => (
                  <div key={k} className="bg-navy-700/40 rounded p-2">
                    <p className="text-gray-500 text-[10px] uppercase">{k}</p>
                    <p className="text-gray-200 font-mono mt-0.5 truncate">{v ?? '—'}</p>
                  </div>
                ))}
              </div>

              {selected.evidence && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Evidence</p>
                  <pre className="text-xs text-gray-300 font-mono bg-navy-700/30 rounded p-2 overflow-x-auto">
                    {JSON.stringify(selected.evidence, null, 2)}
                  </pre>
                </div>
              )}

              {selected.recommended_steps && (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Recommended Steps</p>
                  <ul className="space-y-1">
                    {selected.recommended_steps.split('\n').filter(Boolean).map((s, i) => (
                      <li key={i} className="text-xs text-gray-300 flex gap-2">
                        <span className="text-blue-400 shrink-0">{i + 1}.</span>{s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Status actions */}
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Update Status</p>
                <div className="flex flex-wrap gap-2">
                  {['acknowledged', 'investigating', 'resolved', 'false_positive'].map(s => (
                    <button key={s} disabled={updating || selected.status === s}
                      className="btn-secondary text-xs py-1"
                      onClick={() => updateAlert(selected.id, { status: s })}>
                      {s.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Add note */}
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Add Note</p>
                <textarea className="input w-full h-16 resize-none text-xs" placeholder="Investigation notes…"
                  value={note} onChange={e => setNote(e.target.value)} />
                <button className="btn-primary mt-2 text-xs py-1"
                  disabled={!note.trim() || updating}
                  onClick={() => { updateAlert(selected.id, { note, author: 'analyst' }); setNote('') }}>
                  Save Note
                </button>
              </div>

              {selected.notes?.length ? (
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Notes</p>
                  <div className="space-y-2">
                    {selected.notes.map((n, i) => (
                      <div key={i} className="bg-navy-700/30 rounded p-2">
                        <p className="text-[10px] text-gray-500">{n.author} · {formatTs(n.created_at)}</p>
                        <p className="text-xs text-gray-300 mt-0.5">{n.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
