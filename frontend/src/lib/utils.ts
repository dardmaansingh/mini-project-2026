import { type ClassValue, clsx } from 'clsx'
import { formatDistanceToNow, format } from 'date-fns'
import type { Severity, AlertStatus } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatTs(iso?: string | null): string {
  if (!iso) return '—'
  return format(new Date(iso), 'yyyy-MM-dd HH:mm:ss')
}

export function timeAgo(iso?: string | null): string {
  if (!iso) return '—'
  return formatDistanceToNow(new Date(iso), { addSuffix: true })
}

export function severityClass(s: Severity): string {
  return {
    critical: 'badge-critical',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    informational: 'badge-informational',
  }[s] ?? 'badge-informational'
}

export function statusClass(s: AlertStatus): string {
  return `badge-${s}`
}

export function severityColor(s: Severity): string {
  return {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#3b82f6',
    informational: '#6b7280',
  }[s] ?? '#6b7280'
}

export function formatBytes(bytes?: number | null): string {
  if (bytes == null) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
}

export function eventTypeIcon(type: string): string {
  return {
    dns_query: '🔍',
    connection: '🔗',
    auth_failure: '🔒',
    auth_success: '✅',
    dhcp: '📡',
    flow: '📊',
    ap_event: '📶',
    switch_event: '🖧',
  }[type] ?? '📋'
}
