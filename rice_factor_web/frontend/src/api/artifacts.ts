/**
 * Artifact API functions.
 */

import { api } from './client'
import type {
  ArtifactListResponse,
  ArtifactDetail,
  ArtifactStats,
  ArtifactType,
  ArtifactStatus,
} from './types'

export async function listArtifacts(params?: {
  artifact_type?: ArtifactType
  status?: ArtifactStatus
  limit?: number
  offset?: number
}): Promise<ArtifactListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.artifact_type) searchParams.set('artifact_type', params.artifact_type)
  if (params?.status) searchParams.set('status', params.status)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())

  const query = searchParams.toString()
  return api.get<ArtifactListResponse>(`/artifacts${query ? `?${query}` : ''}`)
}

export async function getArtifact(id: string): Promise<ArtifactDetail> {
  return api.get<ArtifactDetail>(`/artifacts/${id}`)
}

export async function getArtifactStats(): Promise<ArtifactStats> {
  return api.get<ArtifactStats>('/artifacts/stats')
}

export async function approveArtifact(id: string): Promise<ArtifactDetail> {
  return api.post<ArtifactDetail>(`/artifacts/${id}/approve`)
}

export async function lockArtifact(id: string): Promise<ArtifactDetail> {
  return api.post<ArtifactDetail>(`/artifacts/${id}/lock`)
}

export interface MermaidGraph {
  diagram: string
  count?: number
}

export async function getArtifactGraph(): Promise<MermaidGraph> {
  return api.get<MermaidGraph>('/artifacts/graph/mermaid')
}

export interface ArtifactDependencyGraph {
  diagram: string
  artifact_id: string
  dependency_count: number
  dependent_count: number
}

export async function getArtifactDependencyGraph(id: string): Promise<ArtifactDependencyGraph> {
  return api.get<ArtifactDependencyGraph>(`/artifacts/${id}/graph/mermaid`)
}

export interface ArtifactVersion {
  version: string
  created_at: string
  status: string
  artifact_type: string
}

export interface ArtifactVersionsResponse {
  artifact_id: string
  versions: ArtifactVersion[]
  total: number
}

export interface ArtifactVersionPayloadResponse {
  version: string
  payload: Record<string, unknown>
}

export async function getArtifactVersions(id: string): Promise<ArtifactVersionsResponse> {
  return api.get<ArtifactVersionsResponse>(`/artifacts/${id}/versions`)
}

export async function getArtifactVersionPayload(
  id: string,
  version: string
): Promise<ArtifactVersionPayloadResponse> {
  return api.get<ArtifactVersionPayloadResponse>(`/artifacts/${id}/versions/${version}`)
}
