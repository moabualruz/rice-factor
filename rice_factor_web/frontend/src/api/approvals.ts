/**
 * Approval API functions.
 */

import { api } from './client'
import type { ApprovalListResponse, ApprovalHistoryResponse } from './types'

export async function listPendingApprovals(): Promise<ApprovalListResponse> {
  return api.get<ApprovalListResponse>('/approvals')
}

export async function getApprovalHistory(limit?: number): Promise<ApprovalHistoryResponse> {
  const query = limit ? `?limit=${limit}` : ''
  return api.get<ApprovalHistoryResponse>(`/approvals/history${query}`)
}

export interface RevokeApprovalResponse {
  artifact_id: string
  revoked: boolean
  revoked_by: string
  revoked_at: string
}

export async function revokeApproval(
  artifactId: string,
  reason: string
): Promise<RevokeApprovalResponse> {
  return api.post<RevokeApprovalResponse>(`/approvals/${artifactId}/revoke`, {
    reason,
  })
}
