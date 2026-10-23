import { useState, useCallback } from 'react'
import { useApi } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { NetworkEvent, PaginatedResponse, WsMessage } from '@/types'
import { formatTs, eventTypeIcon, formatBytes } from '@/lib/utils'
import { Search, ChevronLeft, ChevronRight, RefreshCw, X, Radio, Eye } from 'lucide-react'

const EVENT_TYPES = [
  'all', 'dns_query', 'flow_record', 'auth_attempt',
  'dhcp_lease', 'snmp_trap', 'wireless_probe', 'threat_intel', 'syslog_entry',
]

const EVENT_TYPE_COLORS: Record<string, string> = {
  dns_query:      '#0284C7',
  flow_record:    '#16A34A',
  auth_attempt:   '#EA580C',
  dhcp_lease:     '#9333EA',
  snmp_trap:      '#D97706',
  wireless_probe: '#0D9488',
  threat_intel:   '#DC2626',
  syslog_entry:   '#64748B',
}

export default function EventExplorer() {
  const [page, setPage] = useState(1)
  const [eventType, setEventType] = useState('all')
  const [sourceIp, setSourceIp] = useState('')
  const [apId, setApId] = useState('')
  const [selected, setSelected] = useState<NetworkEvent | null>(null)
  const [liveCount, setLiveCount] = useState(0)

  const buildPath = () => {
    const p = new URLSearchParams({ page: String(page), page_size: '50' })
    if (eventType !== 'all') p.set('event_type', eventType)
    if (sourceIp)            p.set('source_ip', sourceIp)
    if (apId)                p.set('ap_id', apId)
    return `/api/events?${p}`
  }

  const { data, loading, refetch } = useApi<PaginatedResponse<NetworkEvent>>(
    buildPath(), { deps: [page, eventType, sourceIp, apId] }
  )

  const totalPages = data ? Math.ceil(data.total / 50) : 1

  const onMessage = useCallback((msg: WsMessage) => {
    if (msg.type === 'event.new') {
      setLiveCount(c => c + 1)
    }
  }, [])

  useWebSocket(onMessage)

  return (
    <div className="p-4 space-y-3 animate-fade-in text-gray-900">

      {/* Filter Ribbon (White Card) */}
      <div className="card shadow-sm flex flex-wrap items-center justify-between gap-3 py-2 px-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-2 text-gray-400" />
            <input
              className="input pl-7 text-xs py-1 w-44 shadow-sm"
              placeholder="Source IP (e.g. 10.10.1.1)..."
              value={sourceIp}
              onChange={e => { setSourceIp(e.target.value); setPage(1) }}
            />
          </div>

          <input
            className="input text-xs py-1 w-32 shadow-sm"
            placeholder="AP ID (e.g. AP-01)..."
            value={apId}
            onChange={e => { setApId(e.target.value); setPage(1) }}
          />

          <select
            className="select w-auto text-xs py-1 px-2 shadow-sm"
            value={eventType}
            onChange={e => { setEventType(e.target.value); setPage(1) }}
          >
            {EVENT_TYPES.map(t => (
              <option key={t} value={t}>
                {t === 'all' ? 'All Event Types' : t.replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>

          {(sourceIp || apId || eventType !== 'all') && (
            <button
              className="btn btn-ghost text-xs py-1 px-2 text-gray-500 hover:text-gray-900"
              onClick={() => { setSourceIp(''); setApId(''); setEventType('all'); setPage(1) }}
            >
              <X size={12} className="mr-1" />
              Clear
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 font-mono font-medium">
            {data?.total ?? 0} total events
          </span>
          {liveCount > 0 && (
            <span className="badge badge-green">
              +{liveCount} live
            </span>
          )}
          <button
            onClick={() => { refetch(); setLiveCount(0) }}
            className="btn btn-secondary text-xs py-1 px-2.5 shadow-sm"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin text-green-600' : 'text-gray-500'} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Event table (Crisp White Card) */}
      <div className="card shadow-sm p-0 overflow-hidden flex flex-col justify-between">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 140 }}>Event Type</th>
                <th style={{ width: 140 }}>Timestamp</th>
                <th style={{ width: 130 }}>Source IP</th>
                <th style={{ width: 150 }}>Destination IP:Port</th>
                <th style={{ width: 70 }}>Proto</th>
                <th>Domain / Activity Info</th>
                <th style={{ width: 110 }}>AP / Switch</th>
                <th style={{ width: 50 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-gray-400">
                    Loading live events…
                  </td>
                </tr>
              )}
              {!loading && data?.items.map(ev => {
                const color = EVENT_TYPE_COLORS[ev.event_type] ?? '#64748B'
                const isSelected = selected?.id === ev.id
                return (
                  <tr
                    key={ev.id}
                    style={{
                      cursor: 'pointer',
                      borderLeft: isSelected ? '3px solid #237A3B' : '3px solid transparent',
                      backgroundColor: isSelected ? '#F0FDF4' : undefined,
                    }}
                    onClick={() => setSelected(isSelected ? null : ev)}
                  >
                    <td>
                      <div className="flex items-center gap-1.5">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: color }}
                        />
                        <span
                          className="font-medium text-xs truncate"
                          style={{ color }}
                        >
                          {ev.event_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                    </td>
                    <td className="font-mono text-gray-500 text-[11px]">
                      {formatTs(ev.timestamp_utc)}
                    </td>
                    <td className="font-mono text-gray-900 font-semibold text-xs">
                      {ev.source_ip ?? '—'}
                    </td>
                    <td className="font-mono text-gray-600 text-xs">
                      {ev.destination_ip ? `${ev.destination_ip}:${ev.destination_port ?? 0}` : '—'}
                    </td>
                    <td className="font-mono text-gray-500 text-xs uppercase font-semibold">
                      {ev.protocol ?? '—'}
                    </td>
                    <td className="text-gray-800 text-xs">
                      <span className="truncate block max-w-sm">
                        {ev.domain || ev.username || (ev.bytes_sent ? formatBytes(ev.bytes_sent + (ev.bytes_received ?? 0)) : '—')}
                      </span>
                    </td>
                    <td className="font-mono text-gray-600 text-xs">
                      {ev.ap_id ?? ev.switch_id ?? '—'}
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost text-xs p-1 text-gray-400 hover:text-green-700"
                        title="Inspect Event"
                      >
                        <Eye size={12} />
                      </button>
                    </td>
                  </tr>
                )
              })}
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

      {/* Inline event detail drawer (White Card) */}
      {selected && (
        <div className="card shadow-sm p-0 overflow-hidden animate-slide-down">
          <div className="flex items-center justify-between px-3 py-2 bg-[#F8FAFC] border-b border-[#D8DEE4]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-800 uppercase tracking-wide">
                Packet & Payload Inspection
              </span>
              <span className="font-mono text-[10px] text-gray-500">({selected.id})</span>
            </div>
            <button
              className="btn btn-ghost text-xs p-1 text-gray-400 hover:text-gray-700"
              onClick={() => setSelected(null)}
            >
              <X size={13} />
            </button>
          </div>

          <div className="p-3 grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-2">
            {Object.entries(selected)
              .filter(([, v]) => v != null && v !== '' && typeof v !== 'object')
              .map(([k, v]) => (
                <div key={k} className="bg-gray-50 border border-gray-200 rounded p-1.5">
                  <p className="text-[9px] text-gray-500 uppercase font-semibold">
                    {k.replace(/_/g, ' ')}
                  </p>
                  <p className="font-mono text-gray-900 text-xs mt-0.5 break-all">
                    {String(v)}
                  </p>
                </div>
              ))
            }
          </div>

          {selected.extra_metadata && (
            <div className="px-3 pb-3">
              <p className="text-[10px] text-gray-500 uppercase font-semibold mb-1">
                Raw Metadata Payload
              </p>
              <pre className="text-[10px] text-gray-800 font-mono bg-gray-50 border border-gray-200 rounded p-2 overflow-x-auto leading-relaxed">
                {JSON.stringify(selected.extra_metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

    </div>
  )
}
