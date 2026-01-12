/**
 * Project API functions.
 */

import { api } from './client'
import type { ProjectInfo, PhaseInfo } from './types'

export async function getCurrentProject(): Promise<ProjectInfo> {
  return api.get<ProjectInfo>('/projects/current')
}

export async function getCurrentPhase(): Promise<PhaseInfo> {
  return api.get<PhaseInfo>('/projects/phase')
}

export interface ProjectConfig {
  configured: boolean
  config: Record<string, unknown>
  has_decisions: boolean
  has_glossary: boolean
  has_architecture: boolean
}

export async function getProjectConfig(): Promise<ProjectConfig> {
  return api.get<ProjectConfig>('/projects/config')
}

export interface InitResponse {
  initialized: boolean
  project_dir: string
  files_created: string[]
}

export interface InitRequest {
  responses?: Record<string, unknown>
}

export async function initProject(data: InitRequest = {}): Promise<InitResponse> {
  return api.post<InitResponse>('/projects/init', data)
}
