import { useState, useCallback } from 'react'
import { useApi } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { OverviewMetrics, Alert, WsMessage } from '@/types'
import { formatTs, timeAgo, severityClass } from '@/lib/utils'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import {
  AlertTriangle, Activity, Wifi, Server,
  Shield, Zap, TrendingUp, RefreshCw, Clock, Plus,
  MoreVertical, CheckCircle2, ShieldAlert, Cpu, Globe, Lock, HardDrive
} from 'lucide-react'
import { format } from 'date-fns'

const SEV_COLORS: Record<string, string> = {
  critical:      '#DC2626',
  high:          '#EA580C',
  medium:        '#D97706',
  low:           '#0284C7',
  informational: '#64748B',
}

const TOOLTIP_STYLE = {
  backgroundColor: '#FFFFFF',
  border: '1px solid #D8DEE4',
  borderRadius: 4,
  fontSize: 11,
  padding: '6px 10px',
  color: '#0F172A',
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
}

export default function Dashboard() {
  const { data, loading, refetch } = useApi<OverviewMetrics>('/api/metrics/overview')
  const [liveAlerts, setLiveAlerts] = useState<Alert[]>([])

  const onMessage = useCallback((msg: WsMessage) => {
    if (msg.type === 'alert.new') {
      setLiveAlerts(prev => [msg.data as Alert, ...prev].slice(0, 6))
      refetch()
    }
  }, [refetch])

  useWebSocket(onMessage)

  const chartData = (data?.event_volume_24h ?? []).map(d => ({
    time: format(new Date(d.hour), 'HH:mm'),
    events: d.count,
  }))

  const alerts = liveAlerts.length > 0 ? liveAlerts : (data?.recent_alerts ?? [])

  // Asset donut chart data
  const donutData = [
    { name: 'Monitored APs', value: data?.monitored_aps ?? 6, color: '#16A34A' },
    { name: 'Switches', value: data?.monitored_switches ?? 4, color: '#0284C7' },
    { name: 'Active Alerts', value: data?.high_critical_alerts ?? 12, color: '#DC2626' },
    { name: 'Network Nodes', value: 24, color: '#9333EA' },
  ]
  const totalNodes = donutData.reduce((acc, cur) => acc + cur.value, 0)

  return (
    <div className="p-4 space-y-4 animate-fade-in text-gray-900">

      {/* ── Top Ribbon: Add Widget + System Actions ───────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="btn btn-secondary text-xs font-semibold py-1 px-3 shadow-sm flex items-center gap-1.5">
            <Plus size={13} className="text-gray-600" />
            <span>Add widget</span>
          </button>
          <span className="text-xs text-gray-500 font-mono hidden sm:inline">
            Status: NGFW_PRI (Cluster Active)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            disabled={loading}
            className="btn btn-secondary text-xs py-1 px-2.5 flex items-center gap-1.5 shadow-sm"
            title="Refresh All Widgets"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin text-green-600' : 'text-gray-600'} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <select className="select text-xs py-1 px-2 w-auto shadow-sm">
            <option>Auto Refresh: 10s</option>
            <option>Auto Refresh: 30s</option>
            <option>Auto Refresh: 1m</option>
            <option>Manual Refresh</option>
          </select>
        </div>
      </div>

      {/* ── Row 1: System Info, Security Licenses Grid & Asset Donut ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* 1. System Information Widget */}
        <div className="card shadow-sm">
          <div className="card-header">
            <span className="card-title">
              <Server size={14} className="text-gray-500" />
              System Information
            </span>
            <div className="flex items-center gap-1 text-gray-400">
              <MoreVertical size={14} className="cursor-pointer hover:text-gray-700" />
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500 font-medium">Hostname</span>
              <span className="font-semibold text-gray-800">NETSENTINEL-NGFW-01</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500 font-medium">Serial Number</span>
              <span className="font-mono text-gray-700">NS181FTK20261023</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500 font-medium">Firmware</span>
              <span className="text-gray-800 font-mono">v7.4.3 build2573 (Feature)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500 font-medium">Operation Mode</span>
              <span className="text-gray-800">NAT / Campus Core Gateway</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500 font-medium">System Time</span>
              <span className="font-mono text-gray-700">{format(new Date(), 'yyyy/MM/dd HH:mm:ss')}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-gray-100">
              <span className="text-gray-500 font-medium">Uptime</span>
              <span className="font-mono text-gray-700">65d 1h 15m 20s</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-gray-500 font-medium">WAN Gateway IP</span>
              <span className="font-mono font-semibold text-green-700">172.16.200.1 / 10.10.0.1</span>
            </div>
          </div>
        </div>

        {/* 2. Security Licenses & Feature Tiles (The iconic FortiGate 3x2 Grid) */}
        <div className="card shadow-sm">
          <div className="card-header">
            <span className="card-title">
              <Shield size={14} className="text-gray-500" />
              Security Fabric & Licenses
            </span>
            <span className="badge badge-green">All Protected</span>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {/* Tile 1: Support */}
            <div className="fg-tile fg-tile-orange">
              <Clock size={16} className="mb-1" />
              <span className="text-[11px] font-bold">24/7 Care</span>
              <span className="text-[9px] opacity-90">Support</span>
            </div>

            {/* Tile 2: Threat Updates */}
            <div className="fg-tile fg-tile-green">
              <RefreshCw size={16} className="mb-1" />
              <span className="text-[11px] font-bold">Live</span>
              <span className="text-[9px] opacity-90">Updates</span>
            </div>

            {/* Tile 3: IPS */}
            <div className="fg-tile fg-tile-green">
              <ShieldAlert size={16} className="mb-1" />
              <span className="text-[11px] font-bold">Active</span>
              <span className="text-[9px] opacity-90">IPS / IDS</span>
            </div>

            {/* Tile 4: AntiVirus */}
            <div className="fg-tile fg-tile-green">
              <Zap size={16} className="mb-1" />
              <span className="text-[11px] font-bold">Clean</span>
              <span className="text-[9px] opacity-90">AntiVirus</span>
            </div>

            {/* Tile 5: Web Filter */}
            <div className="fg-tile fg-tile-green">
              <Globe size={16} className="mb-1" />
              <span className="text-[11px] font-bold">Enabled</span>
              <span className="text-[9px] opacity-90">Web Filter</span>
            </div>

            {/* Tile 6: Wireless WIDS */}
            <div className="fg-tile fg-tile-green">
              <Wifi size={16} className="mb-1" />
              <span className="text-[11px] font-bold">Guarded</span>
              <span className="text-[9px] opacity-90">WiFi WIDS</span>
            </div>
          </div>

          <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>FortiGate Cloud Sandbox:</span>
            <span className="text-green-700 font-semibold flex items-center gap-1">
              <CheckCircle2 size={12} /> Connected & Synced
            </span>
          </div>
        </div>

        {/* 3. Assets & Inventory Donut Widget */}
        <div className="card shadow-sm">
          <div className="card-header">
            <span className="card-title">
              <HardDrive size={14} className="text-gray-500" />
              Monitored Assets & Devices
            </span>
            <span className="text-xs text-gray-500 font-mono font-medium">Campus LAN</span>
          </div>

          <div className="flex items-center justify-between h-40">
            <div className="relative w-36 h-36 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={donutData}
                    innerRadius={38}
                    outerRadius={56}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {donutData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className="text-xl font-bold text-gray-900">{totalNodes}</span>
                <span className="text-[9px] text-gray-500 uppercase font-semibold">Devices</span>
              </div>
            </div>

            <div className="flex-1 space-y-1.5 pl-3 text-xs">
              {donutData.map(item => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-gray-600">{item.name}</span>
                  </div>
                  <span className="font-mono font-semibold text-gray-900">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* ── Row 2: KPI Metrics Cards with Severity Accent Borders ─ */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="stat-card" style={{ borderLeft: '3px solid #0284C7' }}>
          <p className="stat-label">Total Ingested Events</p>
          <p className="stat-value text-blue-700">{(data?.total_events ?? 0).toLocaleString()}</p>
          <p className="stat-sub">{data?.events_per_minute ?? 0} events/min</p>
        </div>

        <div className="stat-card" style={{ borderLeft: '3px solid #16A34A' }}>
          <p className="stat-label">Monitored APs & Switches</p>
          <p className="stat-value text-green-700">
            {(data?.monitored_aps ?? 0) + (data?.monitored_switches ?? 0)}
          </p>
          <p className="stat-sub">{data?.monitored_aps ?? 0} APs · {data?.monitored_switches ?? 0} Switches</p>
        </div>

        <div className="stat-card" style={{ borderLeft: '3px solid #EA580C' }}>
          <p className="stat-label">Active Threat Alerts</p>
          <p className="stat-value text-orange-600">{data?.new_alerts ?? 0}</p>
          <p className="stat-sub">Pending SOC review</p>
        </div>

        <div className="stat-card" style={{ borderLeft: '3px solid #DC2626' }}>
          <p className="stat-label">High / Critical Incidents</p>
          <p className="stat-value text-red-600">{data?.high_critical_alerts ?? 0}</p>
          <p className="stat-sub">Immediate action required</p>
        </div>
      </div>

      {/* ── Row 3: Traffic Throughput Chart & Severity Breakdown ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* 24-Hour Event Volume (Area Chart) */}
        <div className="card lg:col-span-2 shadow-sm">
          <div className="card-header">
            <span className="card-title">
              <Activity size={14} className="text-gray-500" />
              Network Traffic & Event Throughput (24 Hours)
            </span>
            <div className="flex items-center gap-2 text-xs">
              <span className="badge badge-green">Real-time Stream</span>
            </div>
          </div>

          <div style={{ height: 190 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="eventGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#237A3B" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#237A3B" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
                <XAxis
                  dataKey="time"
                  stroke="#94A3B8"
                  fontSize={10}
                  tickLine={false}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="#94A3B8"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area
                  type="monotone"
                  dataKey="events"
                  stroke="#237A3B"
                  strokeWidth={2}
                  fill="url(#eventGrad)"
                  name="Events / hr"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-2 pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Throughput: ~{data?.events_per_minute ?? 0} eps</span>
            <span className="font-mono">Sensor: Core Gateway eth0</span>
          </div>
        </div>

        {/* Threat Severity Breakdown */}
        <div className="card shadow-sm flex flex-col justify-between">
          <div className="card-header">
            <span className="card-title">
              <AlertTriangle size={14} className="text-gray-500" />
              Incident Severity Distribution
            </span>
          </div>

          <div className="space-y-3 my-auto">
            {[
              { label: 'Critical', count: data?.high_critical_alerts ?? 0, color: '#DC2626' },
              { label: 'High', count: Math.max(0, (data?.new_alerts ?? 0) - (data?.high_critical_alerts ?? 0)), color: '#EA580C' },
              { label: 'Medium', count: Math.round((data?.new_alerts ?? 0) * 0.4), color: '#D97706' },
              { label: 'Low / Info', count: Math.round((data?.new_alerts ?? 0) * 0.2), color: '#0284C7' },
            ].map(item => {
              const max = 50
              const pct = Math.min((item.count / Math.max(max, item.count || 1)) * 100, 100)
              return (
                <div key={item.label} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-gray-700">{item.label}</span>
                    <span className="font-mono font-bold" style={{ color: item.color }}>
                      {item.count}
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: item.color }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          <div className="pt-2 border-t border-gray-100 text-center">
            <span className="text-[11px] text-gray-500">
              Correlated with MITRE ATT&CK Framework
            </span>
          </div>
        </div>

      </div>

      {/* ── Row 4: Live Security Alerts & Event Stream Table ───── */}
      <div className="card shadow-sm">
        <div className="card-header">
          <span className="card-title">
            <ShieldAlert size={14} className="text-gray-500" />
            FortiView Sources & Recent Threat Detections
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {alerts.length} live records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 90 }}>Severity</th>
                <th style={{ width: 140 }}>Time</th>
                <th style={{ width: 160 }}>Source Host</th>
                <th>Detection Rule / Threat</th>
                <th style={{ width: 90 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-6 text-gray-400">
                    No active alerts detected. All systems normal.
                  </td>
                </tr>
              ) : (
                alerts.map(alert => (
                  <tr key={alert.id}>
                    <td>
                      <span className={severityClass(alert.severity)}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="font-mono text-gray-600 text-[11px]">
                      {timeAgo(alert.first_seen)}
                    </td>
                    <td className="font-mono text-gray-900 font-medium">
                      {alert.source_ip ?? 'Unknown host'}
                    </td>
                    <td className="font-medium text-gray-800">
                      {alert.title}
                    </td>
                    <td>
                      <span className="badge badge-info">
                        {alert.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
