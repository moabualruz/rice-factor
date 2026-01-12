/**
 * API type definitions matching backend schemas.
 */

// Artifact types
export type ArtifactStatus = 'draft' | 'approved' | 'locked'

export type ArtifactType =
  | 'project_plan'
  | 'architecture_plan'
  | 'scaffold_plan'
  | 'test_plan'
  | 'implementation_plan'
  | 'refactor_plan'
  | 'validation_result'

export interface ArtifactSummary {
  id: string
  artifact_type: ArtifactType
  status: ArtifactStatus
  created_at: string
  updated_at: string
  version: number
  age_days: number
  needs_review: boolean
}

export interface ArtifactDetail extends ArtifactSummary {
  payload: Record<string, unknown>
  schema_version: string
  approval?: ApprovalInfo
}

export interface ApprovalInfo {
  approved_by: string
  approved_at: string
}

export interface ArtifactListResponse {
  artifacts: ArtifactSummary[]
  total: number
  by_type: Record<ArtifactType, number>
  by_status: Record<ArtifactStatus, number>
}

export interface ArtifactStats {
  total: number
  by_type: Record<ArtifactType, number>
  by_status: Record<ArtifactStatus, number>
  needs_review: number
  avg_age_days: number
  oldest_artifact_days: number | null
}

// Diff types
export type DiffStatus = 'pending' | 'approved' | 'rejected' | 'applied'

export interface DiffSummary {
  id: string
  target_file: string
  status: DiffStatus
  created_at: string
  lines_added: number
  lines_removed: number
  language?: string
  artifact_id?: string
}

export interface DiffDetail extends DiffSummary {
  content: string
  source_artifact_id?: string
  original_content?: string
  modified_content?: string
}

export interface DiffListResponse {
  diffs: DiffSummary[]
  total: number
  by_status: Record<DiffStatus, number>
}

// Approval types
export type Priority = 'high' | 'normal'

export interface PendingApproval {
  id: string
  item_type: 'artifact' | 'diff'
  name: string
  status: string
  created_at: string
  age_days: number
  priority: Priority
}

export interface ApprovalRecord {
  artifact_id: string
  approved_by: string
  approved_at: string
  notes?: string
}

export interface ApprovalListResponse {
  pending: PendingApproval[]
  total_pending: number
  approved_today: number
}

export interface ApprovalHistoryResponse {
  approvals: ApprovalRecord[]
  total: number
}

// History types
export interface HistoryEntry {
  id: string
  timestamp: string
  event_type: string
  artifact_id?: string
  artifact_type?: ArtifactType
  actor: string
  details: Record<string, unknown>
}

export interface HistoryResponse {
  entries: HistoryEntry[]
  total: number
  has_more: boolean
}

// Project types
export interface ProjectInfo {
  name: string
  root: string
  initialized: boolean
  has_artifacts: boolean
  has_project_config: boolean
}

export interface PhaseInfo {
  phase: string
  description: string
  artifact_counts: Record<ArtifactType, number>
  available_commands: string[]
}

// Auth types
export interface User {
  id: string
  username?: string
  email?: string
  avatar_url?: string
  provider?: string
}

export interface AuthStatus {
  authenticated: boolean
  user?: User
  auth_enabled: boolean
  providers: string[]
}
