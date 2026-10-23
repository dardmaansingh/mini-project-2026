import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Search, Wifi, AlertTriangle,
  Database, Shield, Activity, Settings, Radio,
  ChevronRight, Bell, User, HelpCircle, Menu, RefreshCw
} from 'lucide-react'
import { cn } from '@/lib/utils'

const NAV_GROUPS = [
  {
    label: 'Dashboard',
    items: [
      { to: '/',             icon: LayoutDashboard, label: 'Status & Overview' },
      { to: '/events',       icon: Search,          label: 'FortiView Events' },
      { to: '/alerts',       icon: AlertTriangle,   label: 'Threat Alerts' },
    ],
  },
  {
    label: 'Network & Fabric',
    items: [
      { to: '/access-points', icon: Wifi,     label: 'WiFi & Controller' },
      { to: '/assets',        icon: Database, label: 'Assets & Devices' },
    ],
  },
  {
    label: 'Security Profiles',
    items: [
      { to: '/rules',   icon: Shield,   label: 'Detection Rules' },
      { to: '/sources', icon: Activity, label: 'Data Feeds & Logs' },
    ],
  },
  {
    label: 'System & Admin',
    items: [
      { to: '/settings', icon: Settings, label: 'System Settings' },
    ],
  },
]

const PAGE_LABELS: Record<string, string> = {
  '/':              'Dashboard / Status',
  '/events':        'FortiView / Event Explorer',
  '/alerts':        'Security Fabric / Threat Alerts',
  '/access-points': 'WiFi & Switch Controller / Access Points',
  '/assets':        'Assets & Identities / Device Inventory',
  '/rules':         'Security Profiles / Detection Rules',
  '/sources':       'Log & Report / Data Sources',
  '/settings':      'System / Administrator & Audit',
}

export default function Layout() {
  const location = useLocation()
  const pageLabel = PAGE_LABELS[location.pathname] ?? 'NetSentinel SOC'
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#F0F2F6]">

      {/* ── Top Bar: Authentic FortiGate Forest Green Header ──── */}
      <header
        className="h-10 px-3 flex items-center justify-between shrink-0 text-white select-none shadow-sm z-20"
        style={{ backgroundColor: '#237A3B' }}
      >
        {/* Left: Brand + Menu */}
        <div className="flex items-center gap-3">
          <button
            className="p-1 hover:bg-[#1C6430] rounded transition-colors"
            title="Toggle Menu"
          >
            <Menu size={16} />
          </button>
          
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-white/20 flex items-center justify-center">
              <Radio size={12} className="text-white" />
            </div>
            <span className="font-bold tracking-wider text-xs uppercase text-white">
              NetSentinel
            </span>
            <span className="text-[10px] text-white/70 hidden sm:inline border-l border-white/20 pl-2">
              SOC Security Gateway
            </span>
          </div>
        </div>

        {/* Center: Search input */}
        <div className="flex-1 max-w-md mx-4 hidden md:block">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search features, IPs, policies, alerts..."
              className="w-full bg-white text-gray-900 placeholder-gray-400 pl-8 pr-3 py-1 rounded text-xs outline-none border border-transparent focus:ring-1 focus:ring-white/50 h-7"
            />
          </div>
        </div>

        {/* Right: Status, Bell & Admin User Chip */}
        <div className="flex items-center gap-3 text-xs">
          {/* Live indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded bg-black/20 text-white text-[11px]">
            <span className="w-2 h-2 rounded-full bg-[#86EFAC] animate-pulse" />
            <span className="font-mono text-[10px] font-semibold tracking-wide">LIVE</span>
          </div>

          <button className="p-1.5 hover:bg-[#1C6430] rounded text-white/90 hover:text-white" title="Notifications">
            <Bell size={14} />
          </button>

          <button className="p-1.5 hover:bg-[#1C6430] rounded text-white/90 hover:text-white" title="Help & Docs">
            <HelpCircle size={14} />
          </button>

          {/* User pill */}
          <div className="flex items-center gap-1.5 pl-2 border-l border-white/20">
            <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center font-bold text-[10px]">
              A
            </div>
            <span className="text-xs font-medium hidden sm:inline">admin</span>
          </div>
        </div>
      </header>

      {/* ── Main Body: Dark Sidebar + Light Content Canvas ──── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Left Sidebar (Dark Charcoal) ────────────────── */}
        <aside
          className="w-56 shrink-0 flex flex-col select-none"
          style={{
            backgroundColor: '#242831',
            borderRight: '1px solid #1E222A',
          }}
        >
          {/* Navigation Items */}
          <nav className="flex-1 overflow-y-auto py-2">
            {NAV_GROUPS.map(group => (
              <div key={group.label} className="mb-2">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider px-3 py-1.5">
                  {group.label}
                </p>
                {group.items.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-[#2F3542] transition-colors',
                        isActive && 'bg-[#237A3B] text-white font-medium hover:bg-[#237A3B]'
                      )
                    }
                  >
                    <Icon size={14} className="shrink-0" />
                    <span className="truncate">{label}</span>
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>

          {/* System status footer */}
          <div
            className="px-3 py-2.5 text-[11px] text-gray-400 flex items-center justify-between"
            style={{ borderTop: '1px solid #1E222A', backgroundColor: '#1E222A' }}
          >
            <div>
              <p className="font-semibold text-gray-200">v7.4.3 (Build 2573)</p>
              <p className="text-[10px] text-gray-400 font-mono">SOC-PRI-01</p>
            </div>
            <span className="w-2 h-2 rounded-full bg-green-500" title="System Online" />
          </div>
        </aside>

        {/* ── Main Content Area (White / Light Canvas) ──────── */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#F0F2F6]">
          {/* Breadcrumb / Subheader Ribbon */}
          <div className="h-8 bg-white border-b border-[#D8DEE4] px-4 flex items-center justify-between shrink-0 shadow-sm">
            <div className="flex items-center gap-1.5 text-xs text-gray-600">
              <span className="font-semibold text-gray-900">{pageLabel.split(' / ')[0]}</span>
              {pageLabel.includes(' / ') && (
                <>
                  <ChevronRight size={12} className="text-gray-400" />
                  <span className="text-gray-500">{pageLabel.split(' / ')[1]}</span>
                </>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[11px] text-gray-500 font-mono">
                {new Date().toISOString().slice(0, 10)}
              </span>
            </div>
          </div>

          {/* Page View with scrolling */}
          <div className="flex-1 overflow-y-auto">
            <Outlet />
          </div>
        </main>
      </div>

    </div>
  )
}
