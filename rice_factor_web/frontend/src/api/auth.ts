/**
 * Auth API functions.
 */

import { api } from './client'
import type { AuthStatus } from './types'

export async function getAuthStatus(): Promise<AuthStatus> {
  return api.get<AuthStatus>('/auth/status')
}

export function getGitHubLoginUrl(): string {
  return '/api/v1/auth/github'
}

export function getGoogleLoginUrl(): string {
  return '/api/v1/auth/google'
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}
