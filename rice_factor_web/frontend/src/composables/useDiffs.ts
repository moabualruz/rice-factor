/**
 * Diffs composable for managing diff state.
 */

import { ref, computed } from 'vue'
import { listDiffs, getDiff, approveDiff, rejectDiff } from '@/api/diffs'
import type { DiffSummary, DiffDetail, DiffStatus } from '@/api/types'
import { useWebSocket } from './useWebSocket'

const diffs = ref<DiffSummary[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

export function useDiffs() {
  const { subscribe } = useWebSocket()

  const pendingDiffs = computed(() =>
    diffs.value.filter((d) => d.status === 'pending')
  )

  const approvedDiffs = computed(() =>
    diffs.value.filter((d) => d.status === 'approved')
  )

  const rejectedDiffs = computed(() =>
    diffs.value.filter((d) => d.status === 'rejected')
  )

  async function fetchDiffs(params?: { status?: DiffStatus }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await listDiffs(params)
      diffs.value = response.diffs
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch diffs'
    } finally {
      loading.value = false
    }
  }

  async function fetchDiffById(id: string): Promise<DiffDetail | null> {
    loading.value = true
    error.value = null
    try {
      return await getDiff(id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch diff'
      return null
    } finally {
      loading.value = false
    }
  }

  async function approve(id: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await approveDiff(id)
      await fetchDiffs()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to approve diff'
      return false
    } finally {
      loading.value = false
    }
  }

  async function reject(id: string, reason?: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await rejectDiff(id, reason)
      await fetchDiffs()
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to reject diff'
      return false
    } finally {
      loading.value = false
    }
  }

  // Subscribe to WebSocket events
  subscribe('diff_created', () => fetchDiffs())
  subscribe('diff_approved', () => fetchDiffs())
  subscribe('diff_rejected', () => fetchDiffs())
  subscribe('diff_applied', () => fetchDiffs())

  return {
    diffs,
    loading,
    error,
    pendingDiffs,
    approvedDiffs,
    rejectedDiffs,
    fetchDiffs,
    fetchDiffById,
    approve,
    reject,
  }
}
