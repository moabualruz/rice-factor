import { api } from './client'

export interface CommandRequest {
  args: string[]
  cwd?: string
}

export interface CommandResponse {
  command: string
  exit_code: number
  stdout: string
  stderr: string
}

export async function executeCommand(request: CommandRequest): Promise<CommandResponse> {
  return api.post<CommandResponse>('/commands/execute', request)
}
