/**
 * Auth store for managing authentication state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAuthStatus, logout as apiLogout } from '@/api/auth'
import type { User, AuthStatus } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const authEnabled = ref(false)
  const providers = ref<string[]>([])
  const loading = ref(false)
  const checked = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const isAnonymous = computed(() => !authEnabled.value || !user.value)

  async function checkAuth(): Promise<void> {
    loading.value = true
    try {
      const status: AuthStatus = await getAuthStatus()
      authEnabled.value = status.auth_enabled
      providers.value = status.providers
      user.value = status.user || null
      checked.value = true
    } catch (e) {
      console.error('Failed to check auth status:', e)
      // Auth check failed, assume anonymous
      authEnabled.value = false
      user.value = null
      checked.value = true
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    loading.value = true
    try {
      await apiLogout()
      user.value = null
    } catch (e) {
      console.error('Failed to logout:', e)
    } finally {
      loading.value = false
    }
  }

  function setUser(newUser: User): void {
    user.value = newUser
  }

  return {
    user,
    authEnabled,
    providers,
    loading,
    checked,
    isAuthenticated,
    isAnonymous,
    checkAuth,
    logout,
    setUser,
  }
})
