<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useArtifacts } from '@/composables/useArtifacts'
import { useDiffs } from '@/composables/useDiffs'
import { useProjectStore } from '@/stores/project'
import { listPendingApprovals } from '@/api/approvals'
import { getArtifactGraph } from '@/api/artifacts'
import type { ApprovalListResponse } from '@/api/types'
import StatsCard from '@/components/StatsCard.vue'
import ActivityFeed from '@/components/ActivityFeed.vue'
import PhaseIndicator from '@/components/PhaseIndicator.vue'
import MermaidDiagram from '@/components/MermaidDiagram.vue'

const projectStore = useProjectStore()
const { stats, fetchStats } = useArtifacts()
const { pendingDiffs, fetchDiffs } = useDiffs()

const approvals = ref<ApprovalListResponse | null>(null)
const loading = ref(true)
const artifactGraph = ref<string>('')
const graphLoading = ref(false)
const graphError = ref<string | null>(null)

const hasArtifacts = computed(() => (stats.value?.total ?? 0) > 0)

onMounted(async () => {
  loading.value = true
  await Promise.all([
    projectStore.refresh(),
    fetchStats(),
    fetchDiffs(),
    loadApprovals(),
  ])
  loading.value = false

  // Load graph after stats are available
  if (hasArtifacts.value) {
    await loadArtifactGraph()
  }
})

async function loadApprovals(): Promise<void> {
  try {
    approvals.value = await listPendingApprovals()
  } catch (e) {
    console.error('Failed to load approvals:', e)
  }
}

async function loadArtifactGraph(): Promise<void> {
  graphLoading.value = true
  graphError.value = null
  try {
    const result = await getArtifactGraph()
    artifactGraph.value = result.diagram
  } catch (e) {
    console.error('Failed to load artifact graph:', e)
    graphError.value = 'Failed to load artifact relationships'
  } finally {
    graphLoading.value = false
  }
}

async function refreshGraph(): Promise<void> {
  await loadArtifactGraph()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Dashboard</h1>
      <PhaseIndicator v-if="projectStore.phase" :phase="projectStore.phase" />
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="text-gray-400">Loading...</div>
    </div>

    <template v-else>
      <!-- Stats cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="Total Artifacts"
          :value="stats?.total ?? 0"
          icon="artifacts"
        />
        <StatsCard
          title="Pending Approvals"
          :value="approvals?.total_pending ?? 0"
          icon="approvals"
          :highlight="(approvals?.total_pending ?? 0) > 0"
        />
        <StatsCard
          title="Pending Diffs"
          :value="pendingDiffs.length"
          icon="diff"
          :highlight="pendingDiffs.length > 0"
        />
        <StatsCard
          title="Approved Today"
          :value="approvals?.approved_today ?? 0"
          icon="success"
        />
      </div>

      <!-- Artifact breakdown -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card">
          <h2 class="text-lg font-semibold text-white mb-4">Artifacts by Type</h2>
          <div v-if="stats" class="space-y-2">
            <div
              v-for="(count, type) in stats.by_type"
              :key="type"
              class="flex items-center justify-between text-sm"
            >
              <span class="text-gray-300">{{ type }}</span>
              <span class="text-rf-accent font-mono">{{ count }}</span>
            </div>
            <div v-if="Object.keys(stats.by_type).length === 0" class="text-gray-500 text-sm">
              No artifacts yet
            </div>
          </div>
        </div>

        <div class="card">
          <h2 class="text-lg font-semibold text-white mb-4">Artifacts by Status</h2>
          <div v-if="stats" class="space-y-2">
            <div
              v-for="(count, status) in stats.by_status"
              :key="status"
              class="flex items-center justify-between text-sm"
            >
              <span :class="['status-' + status, 'px-2 py-0.5 rounded text-xs']">
                {{ status }}
              </span>
              <span class="text-rf-accent font-mono">{{ count }}</span>
            </div>
            <div v-if="Object.keys(stats.by_status).length === 0" class="text-gray-500 text-sm">
              No artifacts yet
            </div>
          </div>
        </div>
      </div>

      <!-- Artifact Relationship Graph -->
      <div v-if="hasArtifacts" class="card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-white">Artifact Relationships</h2>
          <button
            class="btn btn-secondary text-sm"
            :disabled="graphLoading"
            @click="refreshGraph"
          >
            {{ graphLoading ? 'Loading...' : 'Refresh' }}
          </button>
        </div>
        <div v-if="graphLoading" class="flex items-center justify-center py-8">
          <div class="text-gray-400">Loading graph...</div>
        </div>
        <div v-else-if="graphError" class="text-red-400 text-sm py-4">
          {{ graphError }}
        </div>
        <div v-else-if="artifactGraph" class="overflow-x-auto">
          <MermaidDiagram :diagram="artifactGraph" id="dashboard-artifact-graph" />
        </div>
        <div v-else class="text-gray-500 text-sm py-4">
          No artifact relationships to display
        </div>
      </div>

      <!-- Activity feed -->
      <div class="card">
        <h2 class="text-lg font-semibold text-white mb-4">Recent Activity</h2>
        <ActivityFeed />
      </div>
    </template>
  </div>
</template>
