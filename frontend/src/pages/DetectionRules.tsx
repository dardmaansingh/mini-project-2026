import { useState, useMemo } from 'react'
import { useApi } from '@/hooks/useApi'
import { api } from '@/lib/api'
import type { DetectionRule, Severity } from '@/types'
import { severityClass, timeAgo } from '@/lib/utils'
import {
  ShieldCheck, ShieldAlert, Sliders, Play, CheckCircle2,
  AlertTriangle, RefreshCw, Search, Filter, Settings, X
} from 'lucide-react'

interface RulesResponse {
  items: DetectionRule[]
}

export default function DetectionRules() {
  const { data, loading, refetch } = useApi<RulesResponse>('/api/rules')
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [testingId, setTestingId] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ id: string; msg: string } | null>(null)
  const [editingRule, setEditingRule] = useState<DetectionRule | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  // Edit form state
  const [editForm, setEditForm] = useState<{
    severity: Severity
    threshold: number
    detection_window_seconds: number
    cooldown_seconds: number
  }>({
    severity: 'medium',
    threshold: 10,
    detection_window_seconds: 60,
    cooldown_seconds: 300,
  })

  const rules = data?.items ?? []

  const categories = useMemo(() => {
    const set = new Set<string>()
    rules.forEach(r => {
      if (r.category) set.add(r.category)
    })
    return Array.from(set)
  }, [rules])

  const filteredRules = useMemo(() => {
    return rules.filter(r => {
      const matchSearch =
        !searchTerm ||
        r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.description?.toLowerCase().includes(searchTerm.toLowerCase())

      const matchCat = categoryFilter === 'all' || r.category === categoryFilter
      return matchSearch && matchCat
    })
  }, [rules, searchTerm, categoryFilter])

  const stats = useMemo(() => {
    const total = rules.length
    const enabled = rules.filter(r => r.enabled).length
    const totalAlerts = rules.reduce((acc, r) => acc + (r.alert_count || 0), 0)
    const highCrit = rules.filter(r => r.severity === 'high' || r.severity === 'critical').length
    return { total, enabled, totalAlerts, highCrit }
  }, [rules])

  const handleToggleEnabled = async (rule: DetectionRule) => {
    try {
      await api.patch(`/api/rules/${rule.id}`, { enabled: !rule.enabled })
      refetch()
    } catch (err) {
      console.error('Failed to toggle rule state:', err)
    }
  }

  const handleTestRule = async (ruleId: string) => {
    setTestingId(ruleId)
    try {
      const res = await api.post<{ test_status: string; note: string }>(`/api/rules/${ruleId}/test`)
      setTestResult({ id: ruleId, msg: res.note || 'Synthetic test passed successfully.' })
      setTimeout(() => {
        setTestResult(null)
      }, 4000)
    } catch (err) {
      console.error('Test rule failed:', err)
      setTestResult({ id: ruleId, msg: 'Test failed or timed out.' })
    } finally {
      setTestingId(null)
    }
  }

  const openEditModal = (rule: DetectionRule) => {
    setEditingRule(rule)
    setEditForm({
      severity: rule.severity,
      threshold: rule.threshold ?? 10,
      detection_window_seconds: rule.detection_window_seconds,
      cooldown_seconds: rule.cooldown_seconds,
    })
  }

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingRule) return
    setIsSaving(true)
    try {
      await api.patch(`/api/rules/${editingRule.id}`, editForm)
      setEditingRule(null)
      refetch()
    } catch (err) {
      console.error('Failed to update rule configuration:', err)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="p-4 space-y-4 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Detection Rules</h1>
          <p className="page-subtitle">
            Continuous correlation and signature engines guarding the campus network
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn btn-secondary text-xs"
          title="Refresh rules"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Total Detection Rules</p>
              <p className="stat-value mt-1">{stats.total}</p>
              <p className="text-xs text-gray-500 mt-1">Engine modules loaded</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <Sliders size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Active & Enforcing</p>
              <p className="stat-value mt-1 text-green-400">{stats.enabled}</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.total > 0 ? Math.round((stats.enabled / stats.total) * 100) : 0}% active
              </p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-green-500/10 text-green-400 flex items-center justify-center">
              <ShieldCheck size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">High / Critical Rules</p>
              <p className="stat-value mt-1 text-orange-400">{stats.highCrit}</p>
              <p className="text-xs text-gray-500 mt-1">Severe threat signatures</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 text-orange-400 flex items-center justify-center">
              <AlertTriangle size={20} />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Total Alerts Raised</p>
              <p className="stat-value mt-1 text-purple-400">{stats.totalAlerts}</p>
              <p className="text-xs text-gray-500 mt-1">By all active rules</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <ShieldAlert size={20} />
            </div>
          </div>
        </div>
      </div>

      {/* Filters & Search */}
      <div className="card flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search rules by name, ID or keywords..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="input w-full pl-9"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <Filter size={14} />
            <span>Category:</span>
            <select
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
              className="select text-xs py-1.5 capitalize"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {(searchTerm || categoryFilter !== 'all') && (
            <button
              onClick={() => {
                setSearchTerm('')
                setCategoryFilter('all')
              }}
              className="text-xs text-blue-400 hover:text-blue-300 underline ml-2"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Rules List Grid */}
      <div className="space-y-3">
        {loading ? (
          <div className="card py-12 text-center text-gray-500 text-sm">
            Loading detection rules…
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="card py-12 text-center text-gray-500 text-sm">
            No matching detection rules found.
          </div>
        ) : (
          filteredRules.map(rule => (
            <div
              key={rule.id}
              style={{
                backgroundColor: '#FFFFFF',
                border: `1px solid ${rule.enabled ? '#D8DEE4' : '#E2E8F0'}`,
                borderRadius: 4, padding: '12px 14px',
                opacity: rule.enabled ? 1 : 0.6,
                boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                transition: 'all 150ms ease',
              }}
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Left: Info */}
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 10, fontWeight: 700, padding: '1px 7px', borderRadius: 3, backgroundColor: '#F8FAFC', color: '#0284C7', border: '1px solid #D8DEE4' }}>
                      {rule.id}
                    </span>
                    <h3 className="font-semibold text-gray-900 text-sm">{rule.name}</h3>
                    <span className={severityClass(rule.severity)}>
                      {rule.severity}
                    </span>
                    {rule.category && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', padding: '1px 7px', borderRadius: 3, fontSize: 10, fontWeight: 500, backgroundColor: 'rgba(148,163,184,0.1)', color: '#94A3B8', border: '1px solid rgba(148,163,184,0.2)', textTransform: 'capitalize' }}>
                        {rule.category}
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      Confidence: <span className="text-gray-300 font-medium capitalize">{rule.confidence}</span>
                    </span>
                  </div>

                  <p className="text-xs text-gray-400 leading-relaxed">
                    {rule.description || 'No detailed description specified.'}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-gray-400">
                    <div>
                      <span className="text-gray-500">Window:</span>{' '}
                      <span className="font-mono text-gray-300">{rule.detection_window_seconds}s</span>
                    </div>
                    {rule.threshold != null && (
                      <div>
                        <span className="text-gray-500">Threshold:</span>{' '}
                        <span className="font-mono text-gray-300">{rule.threshold}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Cooldown:</span>{' '}
                      <span className="font-mono text-gray-300">{rule.cooldown_seconds}s</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Alerts Triggered:</span>{' '}
                      <span className="font-mono text-blue-400 font-semibold">{rule.alert_count ?? 0}</span>
                    </div>
                    {rule.last_triggered && (
                      <div>
                        <span className="text-gray-500">Last Seen:</span>{' '}
                        <span className="text-gray-300">{timeAgo(rule.last_triggered)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-3 shrink-0 self-start lg:self-center">
                  {/* Test notification toast */}
                  {testResult?.id === rule.id && (
                    <span className="text-xs text-green-400 flex items-center gap-1 bg-green-500/10 px-2.5 py-1 rounded-lg border border-green-500/20">
                      <CheckCircle2 size={12} />
                      {testResult.msg}
                    </span>
                  )}

                  <button
                    onClick={() => handleTestRule(rule.id)}
                    disabled={testingId === rule.id || !rule.enabled}
                    className="btn btn-secondary text-xs"
                    title="Simulate rule evaluation against test buffer"
                  >
                    <Play size={12} className={testingId === rule.id ? 'animate-spin' : ''} />
                    {testingId === rule.id ? 'Testing…' : 'Test Rule'}
                  </button>

                  <button
                    onClick={() => openEditModal(rule)}
                    className="btn btn-secondary text-xs"
                    title="Configure thresholds and windows"
                  >
                    <Settings size={12} />
                    Configure
                  </button>

                  {/* Toggle button */}
                  <button
                    onClick={() => handleToggleEnabled(rule)}
                    style={{
                      position: 'relative', display: 'inline-flex', height: 22, width: 40,
                      alignItems: 'center', borderRadius: 11, cursor: 'pointer', border: 'none',
                      backgroundColor: rule.enabled ? '#237A3B' : '#CBD5E1',
                      transition: 'background-color 200ms ease',
                    }}
                    title={rule.enabled ? 'Disable rule' : 'Enable rule'}
                  >
                    <span
                    style={{
                      display: 'inline-block', width: 14, height: 14, borderRadius: '50%', backgroundColor: '#F8FAFC',
                      transform: rule.enabled ? 'translateX(22px)' : 'translateX(3px)',
                      transition: 'transform 200ms ease',
                      flexShrink: 0,
                    }}
                    />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Configure Rule Modal */}
      {editingRule && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 50, backgroundColor: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(2px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div style={{ backgroundColor: '#FFFFFF', border: '1px solid #D8DEE4', borderRadius: 6, padding: '20px 24px', width: '100%', maxWidth: 460, boxShadow: '0 10px 30px rgba(0,0,0,0.15)' }}>
            <div className="flex items-center justify-between pb-3 mb-4" style={{ borderBottom: '1px solid #EDF0F4' }}>
              <div>
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <Settings size={16} className="text-green-700" />
                  Configure {editingRule.id}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">{editingRule.name}</p>
              </div>
              <button
                onClick={() => setEditingRule(null)}
                className="text-gray-400 hover:text-gray-700"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Severity Level
                </label>
                <select
                  value={editForm.severity}
                  onChange={e => setEditForm({ ...editForm, severity: e.target.value as Severity })}
                  className="select w-full capitalize"
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="informational">Informational</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Detection Window (seconds)
                </label>
                <input
                  type="number"
                  min="5"
                  max="3600"
                  value={editForm.detection_window_seconds}
                  onChange={e =>
                    setEditForm({
                      ...editForm,
                      detection_window_seconds: parseInt(e.target.value) || 60,
                    })
                  }
                  className="input w-full font-mono text-xs"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Rolling sliding window length in which event thresholds are accumulated.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Event Threshold (count or rate)
                </label>
                <input
                  type="number"
                  min="1"
                  step="0.1"
                  value={editForm.threshold}
                  onChange={e =>
                    setEditForm({
                      ...editForm,
                      threshold: parseFloat(e.target.value) || 1,
                    })
                  }
                  className="input w-full font-mono text-xs"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Minimum count of matching events required within the window to trigger an alert.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Cooldown Period (seconds)
                </label>
                <input
                  type="number"
                  min="0"
                  max="86400"
                  value={editForm.cooldown_seconds}
                  onChange={e =>
                    setEditForm({
                      ...editForm,
                      cooldown_seconds: parseInt(e.target.value) || 300,
                    })
                  }
                  className="input w-full font-mono text-xs"
                />
                <p className="text-[11px] text-gray-500 mt-1">
                  Prevents alert flooding by deduplicating repeated firings on the same source.
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-3" style={{ borderTop: '1px solid #EDF0F4' }}>
                <button
                  type="button"
                  onClick={() => setEditingRule(null)}
                  className="btn btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="btn btn-primary text-xs"
                >
                  {isSaving ? 'Saving…' : 'Save Configuration'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
