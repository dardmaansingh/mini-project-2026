import { useState } from 'react'
import { useApi } from '@/hooks/useApi'
import type { NetworkAsset } from '@/types'
import { Wifi, ChevronRight, MapPin, Server } from 'lucide-react'
import { timeAgo } from '@/lib/utils'

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
    <div className="p-6 space-y-4 animate-fade-in">
      <div className="page-header">
        <div>
          <h2 className="page-title">Access Points</h2>
          <p className="page-subtitle">Wireless infrastructure status and event history</p>
        </div>
        <div className="text-xs text-gray-400">{data?.total ?? 0} access points registered</div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* AP list */}
        <div className="card p-0">
          <div className="p-4 border-b border-navy-700">
            <p className="card-title"><Wifi size={14} />Access Points</p>
          </div>
          {loading ? (
            <div className="py-8 text-center text-gray-500 text-sm">Loading…</div>
          ) : (
            <div className="divide-y divide-navy-700/50">
              {data?.items.map(ap => (
                <button key={ap.id} onClick={() => setSelected(ap)}
                  className={`w-full text-left px-4 py-3 hover:bg-navy-700/40 transition-colors flex items-center justify-between ${selected?.id === ap.id ? 'bg-blue-500/5 border-l-2 border-blue-500' : ''}`}>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${ap.status === 'online' ? 'bg-green-400' : 'bg-gray-500'}`} />
                      <span className="text-sm font-medium text-gray-200">{ap.ap_id}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 ml-4">{ap.name}</p>
                    <div className="flex gap-3 mt-1 ml-4 text-[10px] text-gray-500">
                      {ap.open_alert_count ? (
                        <span className="text-orange-400">⚠ {ap.open_alert_count} alert{ap.open_alert_count > 1 ? 's' : ''}</span>
                      ) : null}
                      <span>{ap.recent_event_count?.toLocaleString() ?? 0} events</span>
                    </div>
                  </div>
                  <ChevronRight size={14} className="text-gray-600" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* AP detail */}
        <div className="xl:col-span-2 space-y-4">
          {!selected ? (
            <div className="card py-16 text-center text-gray-500">
              <Wifi size={40} className="mx-auto mb-3 text-gray-600" />
              <p>Select an access point to view details</p>
            </div>
          ) : (
            <>
              {/* Info */}
              <div className="card">
                <div className="card-header">
                  <span className="card-title"><Wifi size={14} />{selected.ap_id}</span>
                  <span className={`badge ${selected.status === 'online' ? 'bg-green-500/20 text-green-400 border-green-500/30' : 'badge-informational'}`}>
                    {selected.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    ['Name', selected.name],
                    ['IP Address', selected.ip_address],
                    ['Switch', selected.switch_id],
                    ['Port', selected.switch_port],
                    ['VLAN', selected.vlan_id],
                    ['Location', selected.location ?? 'Unknown'],
                  ].map(([k, v]) => (
                    <div key={k} className="bg-navy-700/40 rounded-lg p-2">
                      <p className="text-[10px] text-gray-500 uppercase">{k}</p>
                      <p className="text-xs text-gray-200 font-mono mt-0.5">{v ?? '—'}</p>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3 italic">
                  AP-to-client associations are based on event metadata only.
                  If ap_id is missing from events, the association is unknown.
                </p>
              </div>

              {/* Open Alerts */}
              {apAlerts?.items.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <span className="card-title text-orange-400">⚠ Open Alerts</span>
                  </div>
                  <div className="space-y-2">
                    {apAlerts.items.map((a: any) => (
                      <div key={a.id} className="bg-navy-700/30 rounded-lg p-3 flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-200">{a.title}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{timeAgo(a.first_seen)}</p>
                        </div>
                        <span className={`badge badge-${a.severity}`}>{a.severity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent events */}
              <div className="card p-0">
                <div className="p-4 border-b border-navy-700">
                  <span className="card-title">Recent Events</span>
                </div>
                {evLoading ? (
                  <div className="py-6 text-center text-gray-500 text-sm">Loading events…</div>
                ) : (
                  <div className="table-container">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-navy-700">
                          <th className="table-head">Timestamp</th>
                          <th className="table-head">Type</th>
                          <th className="table-head">Source IP</th>
                          <th className="table-head">Domain</th>
                        </tr>
                      </thead>
                      <tbody>
                        {apEvents?.items.map((ev: any) => (
                          <tr key={ev.id} className="table-row">
                            <td className="table-cell font-mono text-xs text-gray-400">{timeAgo(ev.timestamp_utc)}</td>
                            <td className="table-cell text-xs">{ev.event_type}</td>
                            <td className="table-cell font-mono text-xs">{ev.source_ip ?? '—'}</td>
                            <td className="table-cell text-xs text-gray-400 truncate max-w-xs">{ev.domain ?? '—'}</td>
                          </tr>
                        ))}
                        {!apEvents?.items.length && (
                          <tr><td colSpan={4} className="py-6 text-center text-gray-500 text-sm">No events for this AP yet.</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
