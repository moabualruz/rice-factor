import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { api } from './client'

describe('ApiClient', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    global.fetch = originalFetch
  })

  it('should make GET requests correctly', async () => {
    const mockData = { id: '123', name: 'test' }
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response)

    const result = await api.get<typeof mockData>('/test')

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/test',
      expect.objectContaining({
        method: 'GET',
        credentials: 'include',
      })
    )
    expect(result).toEqual(mockData)
  })

  it('should make POST requests with body', async () => {
    const mockData = { success: true }
    const postBody = { name: 'test' }
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response)

    const result = await api.post<typeof mockData>('/test', postBody)

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/test',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(postBody),
      })
    )
    expect(result).toEqual(mockData)
  })

  it('should throw error on non-ok response', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: () => Promise.resolve({ detail: 'Resource not found' }),
    } as Response)

    await expect(api.get('/test')).rejects.toThrow('Resource not found')
  })

  it('should handle JSON parse error', async () => {
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.reject(new Error('Invalid JSON')),
    } as Response)

    await expect(api.get('/test')).rejects.toThrow('HTTP 500: Internal Server Error')
  })
})
