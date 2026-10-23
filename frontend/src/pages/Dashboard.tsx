import { useState, useCallback } from 'react'
import { useApi } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { OverviewMetrics, Alert, WsMessage } from '@/types'
import { formatTs, timeAgo, severityClass } from '@/lib/utils'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts'
import { AlertTriangle, Activity, Wifi, Server, Shield, Zap, TrendingUp, Clock } from 'lucide-react'
import { format } from 'date-fns'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444', high: '#f97316', medium: '#eab308',
  low: '#3b82f6', informational: '#6b7280',
}

function StatCard({ icon: Icon, label, value, sub, accent = 'blue' }: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; accent?: string
}) {
  const colors: Record<string, string> = {
    blue: 'text-blue-400 bg-blue-500/10',
    red: 'text-red-400 bg-red-500/10',
    orange: 'text-orange-400 bg-orange-500/10',
    green: 'text-green-400 bg-green-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    teal: 'text-teal-400 bg-teal-500/10',
  }
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="stat-label">{label}</p>
          <p className="stat-value mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colors[accent]}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data, loading, refetch } = useApi<OverviewMetrics>('/api/metrics/overview')
  const [liveAlerts, setLiveAlerts] = useState<Alert[]>([])

  const onMessage = useCallback((msg: WsMessage) => {
    if (msg.type === 'alert.new') {
      setLiveAlerts(prev => [msg.data as Alert, ...prev].slice(0, 5))
      refetch()
    }
  }, [refetch])

  useWebSocket(onMessage)

  const chartData = (data?.event_volume_24h ?? []).map(d => ({
    time: format(new Date(d.hour), 'HH:mm'),
    events: d.count,
  }))

  const severityData = Object.entries(data ? {
    critical: data.high_critical_alerts,
    high: 0, medium: 0, low: 0
  } : {}).map(([name, value]) => ({ name, value }))

  const recentAlerts = [...liveAlerts, ...(data?.recent_alerts ?? [])].slice(0, 8)

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Security Overview</h2>
          <p className="page-subtitle">Real-time college network security monitoring</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <span className="sim-dot" />
          <span className="text-xs text-yellow-400 font-medium">DEMO MODE — Simulated Data</span>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard icon={Activity}      label="Total Events"    value={loading ? '…' : (data?.total_events ?? 0).toLocaleString()} accent="blue" />
        <StatCard icon={Zap}           label="Events / Min"   value={loading ? '…' : data?.events_per_minute ?? 0} accent="teal" />
        <StatCard icon={AlertTriangle} label="New Alerts"      value={loading ? '…' : data?.new_alerts ?? 0}        accent="orange" />
        <StatCard icon={Shield}        label="High/Critical"   value={loading ? '…' : data?.high_critical_alerts ?? 0} accent="red" />
        <StatCard icon={Wifi}          label="Access Points"   value={loading ? '…' : data?.monitored_aps ?? 0}     accent="purple" />
        <StatCard icon={Server}        label="Switches"        value={loading ? '…' : data?.monitored_switches ?? 0} accent="green" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Event volume chart */}
        <div className="card xl:col-span-2">
          <div className="card-header">
            <span className="card-title"><TrendingUp size={14} />Event Volume (24h)</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="evGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 8 }}
                labelStyle={{ color: '#9ca3af' }}
                itemStyle={{ color: '#60a5fa' }}
              />
              <Area type="monotone" dataKey="events" stroke="#3b82f6" fill="url(#evGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Alerts by severity */}
        <div className="card">
          <div className="card-header">
            <span className="card-title"><AlertTriangle size={14} />Alerts by Severity</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={Object.entries(SEVERITY_COLORS).map(([sev, color]) => ({
              name: sev.charAt(0).toUpperCase() + sev.slice(1),
              count: (data as any)?.[`by_severity_${sev}`] ?? 0,
              color,
            }))} layout="vertical" margin={{ left: 30, right: 16 }}>
              <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={80} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: 8 }}
                itemStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="count" radius={4}>
                {Object.entries(SEVERITY_COLORS).map(([sev, color]) => (
                  <Cell key={sev} fill={color} fillOpacity={0.8} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent alerts table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Clock size={14} />Recent Security Alerts</span>
          <span className="text-xs text-gray-500">{recentAlerts.length} shown</span>
        </div>
        {recentAlerts.length === 0 ? (
          <div className="py-12 text-center text-gray-500 text-sm">
            <Shield size={32} className="mx-auto mb-3 text-gray-600" />
            No alerts yet — synthetic generator is warming up…
          </div>
        ) : (
          <div className="table-container">
            <table className="w-full">
              <thead>
                <tr className="border-b border-navy-700">
                  <th className="table-head">Severity</th>
                  <th className="table-head">Title</th>
                  <th className="table-head">Rule</th>
                  <th className="table-head">Source IP</th>
                  <th className="table-head">First Seen</th>
                  <th className="table-head">Status</th>
                </tr>
              </thead>
              <tbody>
                {recentAlerts.map(a => (
                  <tr key={a.id} className="table-row">
                    <td className="table-cell">
                      <span className={severityClass(a.severity)}>{a.severity}</span>
                    </td>
                    <td className="table-cell max-w-xs truncate font-medium text-gray-200">{a.title}</td>
                    <td className="table-cell text-gray-400 text-xs">{a.rule_name}</td>
                    <td className="table-cell font-mono text-xs">{a.source_ip ?? '—'}</td>
                    <td className="table-cell text-xs text-gray-400">{timeAgo(a.first_seen)}</td>
                    <td className="table-cell">
                      <span className={`badge badge-${a.status}`}>{a.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
