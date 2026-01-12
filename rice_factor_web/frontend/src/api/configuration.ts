import { api } from './client'

export interface ConfigResponse {
  merged: Record<string, any>
  project_config: string | null
  user_config: string | null
  project_config_path: string
  user_config_path: string
}

export interface ConfigUpdate {
  content: string
  scope: 'project' | 'user'
}

export interface ConfigUpdateResponse {
  status: string
  path: string
}

export async function getConfiguration(): Promise<ConfigResponse> {
  return api.get<ConfigResponse>('/configuration')
}

export async function updateConfiguration(update: ConfigUpdate): Promise<ConfigUpdateResponse> {
  return api.post<ConfigUpdateResponse>('/configuration', update)
}
