import { useEffect, useRef, useCallback } from 'react'
import type { WsMessage } from '@/types'

const WS_URL = import.meta.env.VITE_WS_URL ?? `ws://${window.location.host}/ws/events`

export function useWebSocket(onMessage: (msg: WsMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>()
  const mountedRef = useRef(true)

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        console.info('[WS] Connected')
        // Clear any pending reconnect timer
        clearTimeout(reconnectTimerRef.current)
      }

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data) as WsMessage
          onMessage(msg)
        } catch {
          // ignore malformed messages
        }
      }

      ws.onerror = () => {
        ws.close()
      }

      ws.onclose = () => {
        console.warn('[WS] Disconnected — reconnecting in 3s')
        if (mountedRef.current) {
          reconnectTimerRef.current = setTimeout(connect, 3000)
        }
      }

      // Heartbeat
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping')
        }
      }, 25000)

      return () => clearInterval(heartbeat)
    } catch (err) {
      console.error('[WS] Connection failed:', err)
      reconnectTimerRef.current = setTimeout(connect, 5000)
    }
  }, [onMessage])

  useEffect(() => {
    mountedRef.current = true
    const cleanup = connect()
    return () => {
      mountedRef.current = false
      clearTimeout(reconnectTimerRef.current)
      cleanup?.()
      wsRef.current?.close()
    }
  }, [connect])

  return wsRef
}
