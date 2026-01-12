/**
 * Project store for managing project state.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCurrentProject, getCurrentPhase } from '@/api/projects'
import type { ProjectInfo, PhaseInfo } from '@/api/types'

export const useProjectStore = defineStore('project', () => {
  const project = ref<ProjectInfo | null>(null)
  const phase = ref<PhaseInfo | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isInitialized = computed(() => project.value?.initialized ?? false)
  const projectName = computed(() => project.value?.name ?? 'Unknown')
  const currentPhase = computed(() => phase.value?.phase ?? 'init')

  async function fetchProject(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      project.value = await getCurrentProject()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch project info'
    } finally {
      loading.value = false
    }
  }

  async function fetchPhase(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      phase.value = await getCurrentPhase()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch phase info'
    } finally {
      loading.value = false
    }
  }

  async function refresh(): Promise<void> {
    await Promise.all([fetchProject(), fetchPhase()])
  }

  return {
    project,
    phase,
    loading,
    error,
    isInitialized,
    projectName,
    currentPhase,
    fetchProject,
    fetchPhase,
    refresh,
  }
})
