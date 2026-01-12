/**
 * History API functions.
 */

import { api } from './client'
import type { HistoryResponse, ArtifactType } from './types'

export async function getHistory(params?: {
  event_type?: string
  artifact_type?: ArtifactType
  start_date?: string
  end_date?: string
  limit?: number
  offset?: number
}): Promise<HistoryResponse> {
  const searchParams = new URLSearchParams()
  if (params?.event_type) searchParams.set('event_type', params.event_type)
  if (params?.artifact_type) searchParams.set('artifact_type', params.artifact_type)
  if (params?.start_date) searchParams.set('start_date', params.start_date)
  if (params?.end_date) searchParams.set('end_date', params.end_date)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  return api.get<HistoryResponse>(`/history${query ? `?${query}` : ''}`)
}

export async function exportHistory(
  format: 'json' | 'csv',
  params?: {
    start_date?: string
    end_date?: string
  }
): Promise<Blob> {
  const searchParams = new URLSearchParams()
  searchParams.set('format', format)
  if (params?.start_date) searchParams.set('start_date', params.start_date)
  if (params?.end_date) searchParams.set('end_date', params.end_date)

  const response = await fetch(`/api/v1/history/export?${searchParams.toString()}`, {
    credentials: 'include',
  })

  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`)
  }

  return response.blob()
}
