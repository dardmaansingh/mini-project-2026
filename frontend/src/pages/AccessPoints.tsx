import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import type { NetworkAsset } from '@/types'
import { Wifi, ChevronRight, Activity, Radio, AlertTriangle } from 'lucide-react'
import { timeAgo, formatTs } from '@/lib/utils'

interface APList { total: number; items: NetworkAsset[] }

export default function AccessPoints() {
  const { data, loading } = useApi<APList>('/api/access-points')
  const [selected, setSelected] = useState<NetworkAsset | null>(null)

  const { data: apEvents, loading: evLoading } = useApi<any>(
    `/api/access-points/${selected?.ap_id}/events`,
    { skip: !selected?.ap_id }
  )
  const { data: apAlerts } = useApi<any>(
    `/api/access-points/${selected?.ap_id}/alerts`,
    { skip: !selected?.ap_id }
  )

  return (
    <div className="p-4 space-y-3 animate-fade-in text-gray-900">

      {/* Header ribbon */}
      <div className="flex items-center justify-between pb-1">
        <div>
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Radio size={16} className="text-green-700" />
            FortiAP Wireless Infrastructure & Controllers
          </h2>
          <p className="text-xs text-gray-500">
            Monitoring {data?.total ?? 0} campus access points and radio channels
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">

        {/* ── AP list panel (Crisp White Card) ─────────────────────── */}
        <div className="card shadow-sm p-0 overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-2.5 bg-[#F8FAFC] border-b border-[#D8DEE4]">
            <Wifi size={13} className="text-green-700" />
            <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Discovered Access Points
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-400 text-xs">
              Loading controllers…
            </div>
          ) : (
            <div className="overflow-y-auto max-h-[calc(100vh-210px)] divide-y divide-gray-100">
              {data?.items.map(ap => {
                const isSelected = selected?.id === ap.id
                const isOnline   = ap.status === 'online'
                const hasAlerts  = (ap.open_alert_count ?? 0) > 0

                return (
                  <button
                    key={ap.id}
                    onClick={() => setSelected(ap)}
                    className="w-full text-left p-3 flex items-center justify-between transition-colors hover:bg-gray-50"
                    style={{
                      borderLeft: isSelected ? '3px solid #237A3B' : '3px solid transparent',
                      backgroundColor: isSelected ? '#F0FDF4' : undefined,
                    }}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: isOnline ? '#16A34A' : '#DC2626' }}
                        />
                        <span className="font-mono text-xs font-bold text-gray-900">
                          {ap.ap_id}
                        </span>
                        <span className={`badge ${isOnline ? 'badge-green' : 'badge-critical'}`}>
                          {ap.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mt-1 pl-4">
                        {ap.name} · {ap.location ?? 'Campus AP'}
                      </p>
                      <div className="flex gap-3 mt-1 pl-4 text-[11px]">
                        {hasAlerts && (
                          <span className="text-orange-600 font-semibold flex items-center gap-1">
                            <AlertTriangle size={11} /> {ap.open_alert_count} alert{ap.open_alert_count > 1 ? 's' : ''}
                          </span>
                        )}
                        <span className="text-gray-500 font-mono">
                          {(ap.recent_event_count ?? 0).toLocaleString()} events
                        </span>
                      </div>
                    </div>
                    <ChevronRight size={13} className="text-gray-400 shrink-0" />
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* ── AP detail panel (White Card) ─────────────────────────── */}
        <div className="xl:col-span-2 space-y-3">
          {!selected ? (
            <div className="card shadow-sm flex flex-col items-center justify-center p-16 text-gray-400 gap-2">
              <Wifi size={32} className="text-gray-300" />
              <p className="text-xs">Select an access point from the list to view telemetry</p>
            </div>
          ) : (
            <>
              {/* AP info card */}
              <div className="card shadow-sm p-0 overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2.5 bg-[#F8FAFC] border-b border-[#D8DEE4]">
                  <div className="flex items-center gap-2">
                    <Wifi size={13} className="text-green-700" />
                    <span className="font-mono text-xs font-bold text-gray-900">
                      {selected.ap_id}
                    </span>
                    <span className="text-xs text-gray-500">— {selected.name}</span>
                  </div>
                  <span className={`badge ${selected.status === 'online' ? 'badge-green' : 'badge-critical'}`}>
                    {selected.status}
                  </span>
                </div>

                <div className="p-3 grid grid-cols-2 md:grid-cols-3 gap-2">
                  {[
                    ['IP Address',    selected.ip_address],
                    ['Switch ID',     selected.switch_id],
                    ['Switch Port',   selected.switch_port],
                    ['VLAN ID',       selected.vlan_id],
                    ['Campus Area',   selected.location ?? 'Not set'],
                    ['Configured SSID', selected.ssid ?? 'Campus-WPA2-Enterprise'],
                  ].map(([k, v]) => (
                    <div key={k} className="bg-gray-50 border border-gray-200 rounded p-2">
                      <p className="text-[9px] text-gray-500 uppercase font-semibold">{k}</p>
                      <p className="font-mono text-gray-900 text-xs mt-0.5 break-all font-medium">{v ?? '—'}</p>
                    </div>
                  ))}
                </div>

                {/* KPI row */}
                <div className="grid grid-cols-2 divide-x divide-gray-200 border-t border-gray-200 bg-gray-50">
                  <div className="p-3">
                    <p className="stat-label">Total Ingested Events</p>
                    <p className="text-lg font-bold text-blue-700 mt-1">
                      {(selected.recent_event_count ?? 0).toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3">
                    <p className="stat-label">Active WIDS Alerts</p>
                    <p className={`text-lg font-bold mt-1 ${(selected.open_alert_count ?? 0) > 0 ? 'text-orange-600' : 'text-green-700'}`}>
                      {selected.open_alert_count ?? 0}
                    </p>
                  </div>
                </div>
              </div>

              {/* Open alerts for this AP */}
              {apAlerts?.items?.length > 0 && (
                <div className="card shadow-sm p-0 overflow-hidden border-orange-200">
                  <div className="px-3 py-2 bg-orange-50 border-b border-orange-200 flex items-center gap-2">
                    <AlertTriangle size={13} className="text-orange-600" />
                    <span className="text-xs font-semibold text-orange-800 uppercase tracking-wide">
                      Active Threat Alerts ({apAlerts.items.length})
                    </span>
                  </div>
                  <div className="divide-y divide-gray-100">
                    {apAlerts.items.map((a: any) => (
                      <div key={a.id} className="p-3 flex items-center justify-between text-xs">
                        <div>
                          <p className="font-semibold text-gray-900">{a.title}</p>
                          <p className="text-gray-500 text-[11px] mt-0.5 font-mono">
                            Source: {a.source_ip ?? 'Unknown'} · {timeAgo(a.first_seen)}
                          </p>
                        </div>
                        <span className="badge badge-high">{a.severity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Events for this AP */}
              <div className="card shadow-sm p-0 overflow-hidden">
                <div className="flex items-center justify-between px-3 py-2.5 bg-[#F8FAFC] border-b border-[#D8DEE4]">
                  <div className="flex items-center gap-2">
                    <Activity size={13} className="text-gray-500" />
                    <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
                      Recent Radio & Traffic Events
                    </span>
                  </div>
                  <span className="text-[11px] text-gray-500 font-mono font-medium">
                    {apEvents?.total ?? 0} events recorded
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Time</th>
                        <th>Source IP</th>
                        <th>Destination</th>
                        <th>Proto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evLoading ? (
                        <tr><td colSpan={5} className="text-center py-6 text-gray-400">Loading events…</td></tr>
                      ) : (apEvents?.items ?? []).slice(0, 10).map((ev: any) => (
                        <tr key={ev.id}>
                          <td>
                            <span className="badge badge-info">{ev.event_type.replace(/_/g, ' ')}</span>
                          </td>
                          <td className="font-mono text-gray-500 text-[11px]">{formatTs(ev.timestamp_utc ?? ev.timestamp)}</td>
                          <td className="font-mono text-gray-900 font-semibold text-xs">{ev.source_ip ?? '—'}</td>
                          <td className="font-mono text-gray-600 text-xs">{ev.destination_ip ?? '—'}</td>
                          <td className="font-mono text-gray-500 text-xs uppercase">{ev.protocol ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

      </div>

    </div>
  )
}
