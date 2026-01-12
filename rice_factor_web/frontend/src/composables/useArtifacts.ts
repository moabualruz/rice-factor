/**
 * Artifacts composable for managing artifact state.
 */

import { ref, computed } from 'vue'
import {
  listArtifacts,
  getArtifact,
  getArtifactStats,
  approveArtifact,
  lockArtifact,
} from '@/api/artifacts'
import type {
  ArtifactSummary,
  ArtifactDetail,
  ArtifactStats,
  ArtifactType,
  ArtifactStatus,
} from '@/api/types'
import { useWebSocket } from './useWebSocket'

const artifacts = ref<ArtifactSummary[]>([])
const stats = ref<ArtifactStats | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

export function useArtifacts() {
  const { subscribe } = useWebSocket()

  const draftArtifacts = computed(() =>
    artifacts.value.filter((a) => a.status === 'draft')
  )

  const approvedArtifacts = computed(() =>
    artifacts.value.filter((a) => a.status === 'approved')
  )

  const lockedArtifacts = computed(() =>
    artifacts.value.filter((a) => a.status === 'locked')
  )

  async function fetchArtifacts(params?: {
    artifact_type?: ArtifactType
    status?: ArtifactStatus
  }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await listArtifacts(params)
      artifacts.value = response.artifacts
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch artifacts'
    } finally {
      loading.value = false
    }
  }

  async function fetchStats(): Promise<void> {
    try {
      stats.value = await getArtifactStats()
    } catch (e) {
      console.error('Failed to fetch artifact stats:', e)
    }
  }

  async function fetchArtifactById(id: string): Promise<ArtifactDetail | null> {
    loading.value = true
    error.value = null
    try {
      return await getArtifact(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch artifact'
      return null
    } finally {
      loading.value = false
    }
  }

  async function approve(id: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await approveArtifact(id)
      // Refresh the list
      await fetchArtifacts()
      await fetchStats()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to approve artifact'
      return false
    } finally {
      loading.value = false
    }
  }

  async function lock(id: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await lockArtifact(id)
      // Refresh the list
      await fetchArtifacts()
      await fetchStats()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to lock artifact'
      return false
    } finally {
      loading.value = false
    }
  }

  // Subscribe to WebSocket events
  subscribe('artifact_created', () => {
    fetchArtifacts()
    fetchStats()
  })

  subscribe('artifact_approved', () => {
    fetchArtifacts()
    fetchStats()
  })

  subscribe('artifact_locked', () => {
    fetchArtifacts()
    fetchStats()
  })

  return {
    artifacts,
    stats,
    loading,
    error,
    draftArtifacts,
    approvedArtifacts,
    lockedArtifacts,
    fetchArtifacts,
    fetchStats,
    fetchArtifactById,
    approve,
    lock,
  }
}
