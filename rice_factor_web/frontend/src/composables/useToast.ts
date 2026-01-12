/**
 * Toast composable for easy toast notifications.
 */

import { useNotificationStore } from '@/stores/notifications'

export function useToast() {
  const store = useNotificationStore()

  return {
    success: store.success,
    error: store.error,
    warning: store.warning,
    info: store.info,
    remove: store.removeToast,
    clearAll: store.clearAll,
  }
}
