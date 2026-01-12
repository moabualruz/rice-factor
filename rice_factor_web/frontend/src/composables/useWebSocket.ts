/**
 * WebSocket composable for real-time updates.
 */

import { ref, onUnmounted } from 'vue'

export type WebSocketEventType =
  | 'artifact_created'
  | 'artifact_approved'
  | 'artifact_locked'
  | 'diff_created'
  | 'diff_approved'
  | 'diff_rejected'
  | 'diff_applied'
  | 'approval_granted'
  | 'approval_revoked'
  | 'connected'
  | 'error'

export interface WebSocketEvent {
  type: WebSocketEventType
  payload: Record<string, unknown>
  timestamp: string
}

type EventHandler = (event: WebSocketEvent) => void

const socket = ref<WebSocket | null>(null)
const isConnected = ref(false)
const handlers = new Map<WebSocketEventType, Set<EventHandler>>()

function getWebSocketUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}/ws`
}

function handleMessage(event: MessageEvent): void {
  try {
    const data: WebSocketEvent = JSON.parse(event.data)
    const eventHandlers = handlers.get(data.type)
    if (eventHandlers) {
      eventHandlers.forEach((handler) => handler(data))
    }
    // Also call 'all' handlers
    const allHandlers = handlers.get('connected')
    if (allHandlers && data.type !== 'connected') {
      allHandlers.forEach((handler) => handler(data))
    }
  } catch (e) {
    console.error('Failed to parse WebSocket message:', e)
  }
}

export function useWebSocket() {
  function connect(): void {
    if (socket.value?.readyState === WebSocket.OPEN) {
      return
    }

    const ws = new WebSocket(getWebSocketUrl())

    ws.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')
    }

    ws.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
      // Reconnect after 3 seconds
      setTimeout(() => {
        if (!socket.value || socket.value.readyState === WebSocket.CLOSED) {
          connect()
        }
      }, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onmessage = handleMessage

    socket.value = ws
  }

  function disconnect(): void {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
  }

  function subscribe(eventType: WebSocketEventType, handler: EventHandler): () => void {
    if (!handlers.has(eventType)) {
      handlers.set(eventType, new Set())
    }
    handlers.get(eventType)!.add(handler)

    // Return unsubscribe function
    return () => {
      handlers.get(eventType)?.delete(handler)
    }
  }

  function subscribeAll(handler: EventHandler): () => void {
    return subscribe('connected', handler)
  }

  onUnmounted(() => {
    // Note: Don't disconnect on unmount as other components may use it
  })

  return {
    isConnected,
    connect,
    disconnect,
    subscribe,
    subscribeAll,
  }
}
