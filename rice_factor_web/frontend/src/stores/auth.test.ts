import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from './auth'

// Mock the api module
vi.mock('@/api/auth', () => ({
  getAuthStatus: vi.fn(),
  logout: vi.fn(),
}))

import { getAuthStatus, logout } from '@/api/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should initialize with default values', () => {
    const store = useAuthStore()

    expect(store.user).toBeNull()
    expect(store.authEnabled).toBe(false)
    expect(store.providers).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.checked).toBe(false)
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAnonymous).toBe(true)
  })

  it('should check auth status successfully', async () => {
    const mockStatus = {
      authenticated: true,
      user: { id: '123', username: 'testuser' },
      auth_enabled: true,
      providers: ['github', 'google'],
    }
    vi.mocked(getAuthStatus).mockResolvedValue(mockStatus)

    const store = useAuthStore()
    await store.checkAuth()

    expect(store.user).toEqual(mockStatus.user)
    expect(store.authEnabled).toBe(true)
    expect(store.providers).toEqual(['github', 'google'])
    expect(store.checked).toBe(true)
    expect(store.isAuthenticated).toBe(true)
    expect(store.isAnonymous).toBe(false)
  })

  it('should handle auth check failure gracefully', async () => {
    vi.mocked(getAuthStatus).mockRejectedValue(new Error('Network error'))

    const store = useAuthStore()
    await store.checkAuth()

    expect(store.user).toBeNull()
    expect(store.authEnabled).toBe(false)
    expect(store.checked).toBe(true)
  })

  it('should logout successfully', async () => {
    vi.mocked(logout).mockResolvedValue(undefined)

    const store = useAuthStore()
    store.setUser({ id: '123', username: 'testuser' })
    expect(store.user).not.toBeNull()

    await store.logout()

    expect(store.user).toBeNull()
  })
})
