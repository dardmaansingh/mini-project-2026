import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Search, Wifi, AlertTriangle,
  Database, Shield, Activity, Settings, Radio
} from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Overview' },
  { to: '/events', icon: Search, label: 'Event Explorer' },
  { to: '/access-points', icon: Wifi, label: 'Access Points' },
  { to: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { to: '/assets', icon: Database, label: 'Asset Inventory' },
  { to: '/rules', icon: Shield, label: 'Detection Rules' },
  { to: '/sources', icon: Activity, label: 'Data Sources' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 bg-navy-900 border-r border-navy-700 flex flex-col">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-navy-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/50">
              <Radio size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-wide">NetSentinel</h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest">Security Monitor</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
          <p className="section-title">Navigation</p>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => cn('nav-item', isActive && 'active')}
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-navy-700">
          <div className="flex items-center gap-2">
            <span className="live-dot" />
            <span className="text-xs text-gray-500">
              <span className="text-yellow-400 font-medium">DEMO MODE</span>
              {' '}· Simulated data
            </span>
          </div>
          <p className="text-[10px] text-gray-600 mt-1">NetSentinel v2.0 · College Network SOC</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto bg-navy-950 bg-grid-pattern bg-grid">
        <Outlet />
      </main>
    </div>
  )
}
