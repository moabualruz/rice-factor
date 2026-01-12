/**
 * Notification store for toast management.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  message?: string
  duration: number  // ms, 0 = persistent
  action?: {
    label: string
    handler: () => void
  }
}

export const useNotificationStore = defineStore('notifications', () => {
  const toasts = ref<Toast[]>([])

  function generateId(): string {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  function addToast(toast: Omit<Toast, 'id'>): string {
    const id = generateId()
    const newToast: Toast = { ...toast, id }
    toasts.value.push(newToast)

    // Auto-dismiss after duration
    if (toast.duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, toast.duration)
    }

    return id
  }

  function removeToast(id: string): void {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  function clearAll(): void {
    toasts.value = []
  }

  // Convenience methods
  function success(title: string, message?: string, duration = 5000): string {
    return addToast({ type: 'success', title, message, duration })
  }

  function error(title: string, message?: string, duration = 8000): string {
    return addToast({ type: 'error', title, message, duration })
  }

  function warning(title: string, message?: string, duration = 6000): string {
    return addToast({ type: 'warning', title, message, duration })
  }

  function info(title: string, message?: string, duration = 5000): string {
    return addToast({ type: 'info', title, message, duration })
  }

  return {
    toasts,
    addToast,
    removeToast,
    clearAll,
    success,
    error,
    warning,
    info,
  }
})
