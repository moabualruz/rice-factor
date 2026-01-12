<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useArtifacts } from '@/composables/useArtifacts'
import type { ArtifactType, ArtifactStatus } from '@/api/types'

const {
  artifacts,
  loading,
  error,
  fetchArtifacts,
} = useArtifacts()

const filterType = ref<ArtifactType | ''>('')
const filterStatus = ref<ArtifactStatus | ''>('')

const artifactTypes: ArtifactType[] = [
  'project_plan',
  'architecture_plan',
  'scaffold_plan',
  'test_plan',
  'implementation_plan',
  'refactor_plan',
  'validation_result',
]

const artifactStatuses: ArtifactStatus[] = ['draft', 'approved', 'locked']

onMounted(() => {
  fetchArtifacts()
})

watch([filterType, filterStatus], () => {
  fetchArtifacts({
    artifact_type: filterType.value || undefined,
    status: filterStatus.value || undefined,
  })
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Artifacts</h1>
    </div>

    <!-- Filters -->
    <div class="card flex flex-wrap gap-4">
      <div>
        <label class="block text-sm text-gray-400 mb-1">Type</label>
        <select
          v-model="filterType"
          class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        >
          <option value="">All Types</option>
          <option v-for="t in artifactTypes" :key="t" :value="t">
            {{ t.replace(/_/g, ' ') }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">Status</label>
        <select
          v-model="filterStatus"
          class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        >
          <option value="">All Statuses</option>
          <option v-for="s in artifactStatuses" :key="s" :value="s">
            {{ s }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="text-gray-400">Loading artifacts...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <!-- Artifacts list -->
    <div v-else-if="artifacts.length === 0" class="card text-gray-500">
      No artifacts found.
    </div>
    <div v-else class="space-y-3">
      <RouterLink
        v-for="artifact in artifacts"
        :key="artifact.id"
        :to="`/artifacts/${artifact.id}`"
        class="card card-hover block"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-white font-medium">
              {{ artifact.artifact_type.replace(/_/g, ' ') }}
            </p>
            <p class="text-xs text-gray-500 font-mono">{{ artifact.id }}</p>
          </div>
          <div class="flex items-center space-x-4">
            <span
              :class="['status-' + artifact.status, 'px-2 py-1 rounded text-xs']"
            >
              {{ artifact.status }}
            </span>
            <span
              v-if="artifact.needs_review"
              class="text-xs text-yellow-400"
            >
              Needs Review
            </span>
          </div>
        </div>
        <div class="mt-2 flex items-center space-x-4 text-xs text-gray-500">
          <span>Version {{ artifact.version }}</span>
          <span>{{ formatDate(artifact.created_at) }}</span>
          <span v-if="artifact.age_days > 0">{{ artifact.age_days }} days old</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
