import { useState, useMemo } from 'react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import type { NetworkAsset } from '@/types'
import { timeAgo } from '@/lib/utils'
import {
  Shield, ShieldAlert, ShieldCheck, Server, Wifi, Laptop,
  Cpu, HardDrive, Plus, Search, Filter, RefreshCw, X, Check,
  ExternalLink, ChevronRight, AlertTriangle
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface AssetResponse {
  total: number
  items: NetworkAsset[]
}

const ASSET_TYPE_ICONS: Record<string, React.ElementType> = {
  access_point: Wifi,
  switch: HardDrive,
  router: HardDrive,
  server: Server,
  workstation: Laptop,
  iot: Cpu,
  unknown: ShieldAlert,
}

export default function AssetInventory() {
  const navigate = useNavigate()
  const { data, loading, refetch } = useApi<AssetResponse>('/api/assets?page_size=300')
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [authFilter, setAuthFilter] = useState('all')
  const [selectedAsset, setSelectedAsset] = useState<NetworkAsset | null>(null)
  const [isRegisterOpen, setIsRegisterOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form state for registration
  const [newAsset, setNewAsset] = useState({
    name: '',
    asset_type: 'workstation',
    hostname: '',
    ip_address: '',
    mac_address: '',
    location: '',
    vlan_id: '10',
    is_authorized: true,
  })

  const assets = data?.items ?? []

  const filteredAssets = useMemo(() => {
    return assets.filter(item => {
      const matchSearch =
        !searchTerm ||
        item.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.ip_address?.includes(searchTerm) ||
        item.mac_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.location?.toLowerCase().includes(searchTerm.toLowerCase())

      const matchType = typeFilter === 'all' || item.asset_type === typeFilter
      const matchAuth =
        authFilter === 'all' ||
        (authFilter === 'authorized' && item.is_authorized) ||
        (authFilter === 'unauthorized' && !item.is_authorized)

      return matchSearch && matchType && matchAuth
    })
  }, [assets, searchTerm, typeFilter, authFilter])

  const stats = useMemo(() => {
    const total = assets.length
    const authorized = assets.filter(a => a.is_authorized).length
    const unauthorized = assets.filter(a => !a.is_authorized).length
    const infra = assets.filter(a => ['access_point', 'switch', 'router'].includes(a.asset_type)).length
    const servers = assets.filter(a => a.asset_type === 'server').length
    return { total, authorized, unauthorized, infra, servers }
  }, [assets])

  const handleCreateAsset = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newAsset.name || !newAsset.ip_address) return

    setIsSubmitting(true)
    try {
      await api.post('/api/assets', {
        ...newAsset,
        status: 'online',
        last_seen: new Date().toISOString(),
      })
      setIsRegisterOpen(false)
      setNewAsset({
        name: '',
        asset_type: 'workstation',
        hostname: '',
        ip_address: '',
        mac_address: '',
        location: '',
        vlan_id: '10',
        is_authorized: true,
      })
      refetch()
    } catch (err) {
      console.error('Failed to create asset:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-4 space-y-4 animate-fade-in">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Asset Inventory</h1>
          <p className="page-subtitle">Discovered campus hardware, network switches, APs, and client devices</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="btn btn-secondary text-xs"
            title="Refresh assets"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            onClick={() => setIsRegisterOpen(true)}
            className="btn btn-primary text-xs"
          >
            <Plus size={14} />
            Register Asset
          </button>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Total Assets</p>
              <p className="stat-value mt-1">{stats.total}</p>
              <p className="text-xs text-gray-500 mt-1">Discovered on network</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Shield size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Authorized Devices</p>
              <p className="stat-value mt-1 text-green-400">{stats.authorized}</p>
              <p className="text-xs text-gray-500 mt-1">Verified campus profile</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-green-500/10 text-green-400 flex items-center justify-center">
              <ShieldCheck size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Unauthorized / Unknown</p>
              <p className={`stat-value mt-1 ${stats.unauthorized > 0 ? 'text-red-400' : 'text-gray-400'}`}>
                {stats.unauthorized}
              </p>
              <p className="text-xs text-gray-500 mt-1">Requires SOC review</p>
            </div>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${stats.unauthorized > 0 ? 'bg-red-500/10 text-red-400' : 'bg-gray-500/10 text-gray-400'}`}>
              <ShieldAlert size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Core Infrastructure</p>
              <p className="stat-value mt-1 text-purple-400">{stats.infra}</p>
              <p className="text-xs text-gray-500 mt-1">APs, Switches & Routers</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Server size={20} />
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="card flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name, IP, MAC, location..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="input w-full pl-9"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Filter size={14} />
            <span>Type:</span>
            <select
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
              className="select text-xs py-1.5"
            >
              <option value="all">All Types</option>
              <option value="access_point">Access Point</option>
              <option value="switch">Switch</option>
              <option value="server">Server</option>
              <option value="workstation">Workstation</option>
              <option value="iot">IoT Device</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span>Auth:</span>
            <select
              value={authFilter}
              onChange={e => setAuthFilter(e.target.value)}
              className="select text-xs py-1.5"
            >
              <option value="all">All Status</option>
              <option value="authorized">Authorized</option>
              <option value="unauthorized">Unauthorized</option>
            </select>
          </div>

          {(searchTerm || typeFilter !== 'all' || authFilter !== 'all') && (
            <button
              onClick={() => {
                setSearchTerm('')
                setTypeFilter('all')
                setAuthFilter('all')
              }}
              className="text-xs text-blue-400 hover:text-blue-300 underline ml-2"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Assets Table */}
      <div className="card p-0 overflow-hidden">
        <div className="table-container">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#D8DEE4] bg-[#F8FAFC]">
                <th className="table-head">Asset</th>
                <th className="table-head">Type</th>
                <th className="table-head">IP Address</th>
                <th className="table-head">MAC Address</th>
                <th className="table-head">Location / VLAN</th>
                <th className="table-head">Auth Status</th>
                <th className="table-head">Status</th>
                <th className="table-head">Last Seen</th>
                <th className="table-head text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-gray-500 text-sm">
                    Loading asset inventory…
                  </td>
                </tr>
              ) : filteredAssets.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-gray-500 text-sm">
                    No matching assets found.
                  </td>
                </tr>
              ) : (
                filteredAssets.map(asset => {
                  const Icon = ASSET_TYPE_ICONS[asset.asset_type] || Shield
                  return (
                    <tr
                      key={asset.id}
                      onClick={() => setSelectedAsset(asset)}
                      className="table-row cursor-pointer"
                    >
                      <td className="table-cell">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded bg-gray-100 border border-gray-200 flex items-center justify-center text-gray-600">
                            <Icon size={16} />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 text-sm">{asset.name}</p>
                            {asset.hostname && (
                              <p className="text-xs text-gray-500 font-mono">{asset.hostname}</p>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="table-cell capitalize">
                        <span className="text-xs text-gray-600">
                          {asset.asset_type.replace('_', ' ')}
                        </span>
                      </td>

                      <td className="table-cell">
                        <span className="font-mono text-xs font-semibold text-blue-700">
                          {asset.ip_address || '—'}
                        </span>
                      </td>

                      <td className="table-cell">
                        <span className="font-mono text-xs text-gray-600">
                          {asset.mac_address || '—'}
                        </span>
                      </td>

                      <td className="table-cell">
                        <div>
                          <p className="text-xs text-gray-300">{asset.location || 'Campus'}</p>
                          {asset.vlan_id && (
                            <p className="text-[10px] text-gray-500">VLAN {asset.vlan_id}</p>
                          )}
                        </div>
                      </td>

                      <td className="table-cell">
                        {asset.is_authorized ? (
                          <span className="badge bg-green-500/10 text-green-400 border border-green-500/30">
                            Authorized
                          </span>
                        ) : (
                          <span className="badge bg-red-500/10 text-red-400 border border-red-500/30">
                            Unauthorized
                          </span>
                        )}
                      </td>

                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              asset.status === 'online' ? 'bg-green-400' : 'bg-gray-500'
                            }`}
                          />
                          <span className="text-xs capitalize text-gray-400">
                            {asset.status || 'unknown'}
                          </span>
                        </div>
                      </td>

                      <td className="table-cell text-xs text-gray-400">
                        {timeAgo(asset.last_seen)}
                      </td>

                      <td className="table-cell text-right">
                        <ChevronRight size={16} className="text-gray-500 inline-block" />
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Asset Detail Slide-over / Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-white border-l border-[#D8DEE4] h-full p-6 overflow-y-auto space-y-6 shadow-2xl animate-fade-in text-gray-900">
            <div className="flex items-center justify-between pb-4 border-b border-[#EDF0F4]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
                  <Shield size={20} />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gray-900">{selectedAsset.name}</h3>
                  <p className="text-xs text-gray-500 uppercase tracking-wider">
                    {selectedAsset.asset_type.replace('_', ' ')}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedAsset(null)}
                className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100"
              >
                <X size={18} />
              </button>
            </div>

            {/* Authorization Flag Banner */}
            {!selectedAsset.is_authorized && (
              <div className="p-3 bg-red-50 border border-red-200 rounded flex items-start gap-3 text-red-800 text-xs">
                <AlertTriangle size={16} className="shrink-0 mt-0.5 text-red-600" />
                <div>
                  <span className="font-semibold">Unauthorized Device Flag:</span> This device has
                  not been registered in the campus directory. Network access is restricted and
                  monitored.
                </div>
              </div>
            )}

            {/* Properties List */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Network Attributes
              </h4>
              <div className="bg-gray-50 border border-gray-200 rounded p-4 space-y-2.5 text-xs">
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-500 font-medium">Hostname</span>
                  <span className="font-mono text-gray-900 font-semibold">{selectedAsset.hostname || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-500 font-medium">IP Address</span>
                  <span className="font-mono font-semibold text-blue-700">{selectedAsset.ip_address || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-500 font-medium">MAC Address</span>
                  <span className="font-mono text-gray-800">{selectedAsset.mac_address || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-500 font-medium">Vendor</span>
                  <span className="text-gray-800">{selectedAsset.vendor || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-500 font-medium">Location</span>
                  <span className="text-gray-800">{selectedAsset.location || '—'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200">
                  <span className="text-gray-500 font-medium">VLAN ID</span>
                  <span className="text-gray-800">{selectedAsset.vlan_id || '—'}</span>
                </div>
                {selectedAsset.switch_id && (
                  <div className="flex justify-between py-1 border-b border-gray-200">
                    <span className="text-gray-500 font-medium">Switch & Port</span>
                    <span className="text-gray-800 font-mono">
                      {selectedAsset.switch_id} : {selectedAsset.switch_port || '1'}
                    </span>
                  </div>
                )}
                {selectedAsset.ap_id && (
                  <div className="flex justify-between py-1 border-b border-gray-200">
                    <span className="text-gray-500 font-medium">Connected AP</span>
                    <span className="text-gray-800 font-mono">{selectedAsset.ap_id}</span>
                  </div>
                )}
                <div className="flex justify-between py-1">
                  <span className="text-gray-400">Last Seen</span>
                  <span className="text-gray-200">{timeAgo(selectedAsset.last_seen)}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Investigate & Pivot
              </h4>
              <div className="flex flex-col gap-2">
                {selectedAsset.ip_address && (
                  <button
                    onClick={() => {
                      setSelectedAsset(null)
                      navigate(`/events?source_ip=${selectedAsset.ip_address}`)
                    }}
                    className="btn btn-secondary text-xs justify-between w-full"
                  >
                    <span>View Events for {selectedAsset.ip_address}</span>
                    <ExternalLink size={14} />
                  </button>
                )}
                {selectedAsset.ap_id && (
                  <button
                    onClick={() => {
                      setSelectedAsset(null)
                      navigate('/access-points')
                    }}
                    className="btn btn-secondary text-xs justify-between w-full"
                  >
                    <span>Inspect AP {selectedAsset.ap_id}</span>
                    <ExternalLink size={14} />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Register Asset Modal */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="card w-full max-w-lg bg-white border-[#D8DEE4] shadow-2xl p-6 animate-scale-up text-gray-900">
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-[#EDF0F4]">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Plus size={18} className="text-green-700" />
                Register New Asset
              </h3>
              <button
                onClick={() => setIsRegisterOpen(false)}
                className="text-gray-400 hover:text-gray-700"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateAsset} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Asset Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. CS-Lab-Workstation-04"
                    value={newAsset.name}
                    onChange={e => setNewAsset({ ...newAsset, name: e.target.value })}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Asset Type
                  </label>
                  <select
                    value={newAsset.asset_type}
                    onChange={e => setNewAsset({ ...newAsset, asset_type: e.target.value })}
                    className="select w-full"
                  >
                    <option value="workstation">Workstation</option>
                    <option value="server">Server</option>
                    <option value="access_point">Access Point</option>
                    <option value="switch">Switch</option>
                    <option value="router">Router</option>
                    <option value="iot">IoT Device</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    IP Address *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="10.20.4.155"
                    value={newAsset.ip_address}
                    onChange={e => setNewAsset({ ...newAsset, ip_address: e.target.value })}
                    className="input w-full font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    MAC Address
                  </label>
                  <input
                    type="text"
                    placeholder="a4:83:e7:22:11:08"
                    value={newAsset.mac_address}
                    onChange={e => setNewAsset({ ...newAsset, mac_address: e.target.value })}
                    className="input w-full font-mono text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Hostname
                  </label>
                  <input
                    type="text"
                    placeholder="pc-lab4-01.college.edu"
                    value={newAsset.hostname}
                    onChange={e => setNewAsset({ ...newAsset, hostname: e.target.value })}
                    className="input w-full text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">
                    Location / Building
                  </label>
                  <input
                    type="text"
                    placeholder="Science Block B, Room 204"
                    value={newAsset.location}
                    onChange={e => setNewAsset({ ...newAsset, location: e.target.value })}
                    className="input w-full text-xs"
                  />
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="auth-check"
                  checked={newAsset.is_authorized}
                  onChange={e => setNewAsset({ ...newAsset, is_authorized: e.target.checked })}
                  className="rounded border-navy-600 bg-navy-700 text-blue-500 focus:ring-0"
                />
                <label htmlFor="auth-check" className="text-xs text-gray-300 cursor-pointer">
                  Mark device as authorized campus asset
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-navy-800">
                <button
                  type="button"
                  onClick={() => setIsRegisterOpen(false)}
                  className="btn btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn btn-primary text-xs"
                >
                  {isSubmitting ? 'Registering…' : 'Register Asset'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
