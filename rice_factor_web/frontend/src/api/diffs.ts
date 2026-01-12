/**
 * Diff API functions.
 */

import { api } from './client'
import type { DiffListResponse, DiffDetail, DiffStatus } from './types'

export async function listDiffs(params?: {
  status?: DiffStatus
  limit?: number
  offset?: number
}): Promise<DiffListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  return api.get<DiffListResponse>(`/diffs${query ? `?${query}` : ''}`)
}

export async function getDiff(id: string): Promise<DiffDetail> {
  return api.get<DiffDetail>(`/diffs/${id}`)
}

export async function approveDiff(id: string): Promise<DiffDetail> {
  return api.post<DiffDetail>(`/diffs/${id}/approve`)
}

export async function rejectDiff(id: string, reason?: string): Promise<DiffDetail> {
  return api.post<DiffDetail>(`/diffs/${id}/reject`, { reason })
}
