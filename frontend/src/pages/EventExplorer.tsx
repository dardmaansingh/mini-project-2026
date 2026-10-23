import { useState, useCallback, useRef } from 'react'
import { useApi } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { NetworkEvent, PaginatedResponse, WsMessage } from '@/types'
import { formatTs, eventTypeIcon, formatBytes } from '@/lib/utils'
import { Search, RefreshCw, Filter, ChevronLeft, ChevronRight } from 'lucide-react'

const EVENT_TYPES = ['all', 'dns_query', 'connection', 'auth_failure', 'auth_success', 'dhcp', 'flow', 'ap_event', 'switch_event']

export default function EventExplorer() {
  const [page, setPage] = useState(1)
  const [eventType, setEventType] = useState('all')
  const [sourceIp, setSourceIp] = useState('')
  const [apId, setApId] = useState('')
  const [selected, setSelected] = useState<NetworkEvent | null>(null)
  const [liveCount, setLiveCount] = useState(0)

  const buildPath = () => {
    const params = new URLSearchParams({ page: String(page), page_size: '50' })
    if (eventType !== 'all') params.set('event_type', eventType)
    if (sourceIp) params.set('source_ip', sourceIp)
    if (apId) params.set('ap_id', apId)
    return `/api/events?${params}`
  }

  const { data, loading, refetch } = useApi<PaginatedResponse<NetworkEvent>>(buildPath(), { deps: [page, eventType, sourceIp, apId] })

  const onMessage = useCallback((msg: WsMessage) => {
    if (msg.type === 'event.new') setLiveCount(c => c + 1)
  }, [])
  useWebSocket(onMessage)

  const totalPages = data ? Math.ceil(data.total / 50) : 1

  return (
    <div className="p-6 space-y-4 animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Live Event Explorer</h2>
          <p className="page-subtitle">
            Search and filter all network events
            {liveCount > 0 && <span className="ml-2 text-blue-400">(+{liveCount} new since load)</span>}
          </p>
        </div>
        <button onClick={() => { refetch(); setLiveCount(0) }} className="btn-secondary">
          <RefreshCw size={14} />Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-48">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input className="input w-full pl-9" placeholder="Filter source IP…" value={sourceIp}
              onChange={e => { setSourceIp(e.target.value); setPage(1) }} />
          </div>
          <input className="input min-w-40" placeholder="AP ID…" value={apId}
            onChange={e => { setApId(e.target.value); setPage(1) }} />
          <select className="select" value={eventType} onChange={e => { setEventType(e.target.value); setPage(1) }}>
            {EVENT_TYPES.map(t => <option key={t} value={t}>{t === 'all' ? 'All types' : t}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0">
        <div className="table-container">
          <table className="w-full">
            <thead>
              <tr className="border-b border-navy-700">
                <th className="table-head">Type</th>
                <th className="table-head">Timestamp</th>
                <th className="table-head">Source IP</th>
                <th className="table-head">Destination</th>
                <th className="table-head">Protocol</th>
                <th className="table-head">Domain / Info</th>
                <th className="table-head">AP</th>
                <th className="table-head">Src</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={8} className="py-12 text-center text-gray-500 text-sm">Loading events…</td></tr>
              )}
              {!loading && data?.items.map(ev => (
                <tr key={ev.id} className="table-row cursor-pointer" onClick={() => setSelected(ev)}>
                  <td className="table-cell">
                    <span className="font-mono text-xs bg-navy-700 px-1.5 py-0.5 rounded">
                      {eventTypeIcon(ev.event_type)} {ev.event_type}
                    </span>
                  </td>
                  <td className="table-cell font-mono text-xs text-gray-400">{formatTs(ev.timestamp_utc)}</td>
                  <td className="table-cell font-mono text-xs">{ev.source_ip ?? '—'}</td>
                  <td className="table-cell font-mono text-xs text-gray-400">
                    {ev.destination_ip ?? '—'}{ev.destination_port ? `:${ev.destination_port}` : ''}
                  </td>
                  <td className="table-cell text-xs">{ev.protocol ?? '—'}</td>
                  <td className="table-cell text-xs text-gray-300 max-w-xs truncate">
                    {ev.domain ?? (ev.bytes_sent ? formatBytes(ev.bytes_sent) + ' sent' : '—')}
                  </td>
                  <td className="table-cell text-xs text-blue-400">{ev.ap_id ?? '—'}</td>
                  <td className="table-cell">
                    {ev.simulated
                      ? <span className="sim-dot" title="Simulated" />
                      : <span className="live-dot" title="Live" />}
                  </td>
                </tr>
              ))}
              {!loading && !data?.items.length && (
                <tr><td colSpan={8} className="py-12 text-center text-gray-500 text-sm">No events match your filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-navy-700">
          <span className="text-xs text-gray-500">
            {data?.total.toLocaleString() ?? 0} total events
          </span>
          <div className="flex items-center gap-2">
            <button className="btn-secondary py-1 px-2" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft size={14} />
            </button>
            <span className="text-sm text-gray-400">Page {page} / {totalPages}</span>
            <button className="btn-secondary py-1 px-2" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="card border-blue-500/30">
          <div className="card-header">
            <span className="card-title">Event Detail — {selected.id}</span>
            <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-gray-300 text-xs">✕ Close</button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(selected).filter(([, v]) => v != null && v !== '' && typeof v !== 'object').map(([k, v]) => (
              <div key={k} className="bg-navy-700/50 rounded-lg p-2">
                <p className="text-[10px] text-gray-500 uppercase tracking-wider">{k.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-200 font-mono mt-0.5 break-all">{String(v)}</p>
              </div>
            ))}
          </div>
          {selected.extra_metadata && (
            <div className="mt-3 bg-navy-700/30 rounded-lg p-3">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Extra Metadata</p>
              <pre className="text-xs text-gray-300 font-mono overflow-x-auto">
                {JSON.stringify(selected.extra_metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
