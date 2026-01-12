<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useArtifacts } from '@/composables/useArtifacts'
import {
  getArtifactDependencyGraph,
  getArtifactVersions,
  getArtifactVersionPayload,
  type ArtifactVersion,
} from '@/api/artifacts'
import type { ArtifactDetail } from '@/api/types'
import MermaidDiagram from '@/components/MermaidDiagram.vue'
import VersionCompare from '@/components/VersionCompare.vue'

const route = useRoute()
const router = useRouter()
const { fetchArtifactById, approve, lock, loading, error } = useArtifacts()

const artifact = ref<ArtifactDetail | null>(null)
const actionLoading = ref(false)
const actionError = ref<string | null>(null)

// Dependency graph state
const dependencyGraph = ref<string>('')
const graphLoading = ref(false)
const dependencyCount = ref(0)
const dependentCount = ref(0)

// Version history state
const versions = ref<ArtifactVersion[]>([])
const versionsLoading = ref(false)
const showVersionCompare = ref(false)

const artifactId = computed(() => route.params.id as string)
const canApprove = computed(() => artifact.value?.status === 'draft')
const canLock = computed(() => artifact.value?.status === 'approved')
const hasDependencies = computed(() => dependencyCount.value > 0 || dependentCount.value > 0)
const hasMultipleVersions = computed(() => versions.value.length > 1)

onMounted(async () => {
  artifact.value = await fetchArtifactById(artifactId.value)
  await Promise.all([
    loadDependencyGraph(),
    loadVersions(),
  ])
})

async function loadVersions(): Promise<void> {
  versionsLoading.value = true
  try {
    const result = await getArtifactVersions(artifactId.value)
    versions.value = result.versions
  } catch (e) {
    console.error('Failed to load versions:', e)
  } finally {
    versionsLoading.value = false
  }
}

async function getVersionPayload(version: number): Promise<Record<string, unknown>> {
  const result = await getArtifactVersionPayload(artifactId.value, String(version))
  return result.payload
}

async function loadDependencyGraph(): Promise<void> {
  graphLoading.value = true
  try {
    const result = await getArtifactDependencyGraph(artifactId.value)
    dependencyGraph.value = result.diagram
    dependencyCount.value = result.dependency_count
    dependentCount.value = result.dependent_count
  } catch (e) {
    console.error('Failed to load dependency graph:', e)
  } finally {
    graphLoading.value = false
  }
}

async function handleApprove(): Promise<void> {
  actionLoading.value = true
  actionError.value = null
  const success = await approve(artifactId.value)
  if (success) {
    artifact.value = await fetchArtifactById(artifactId.value)
  } else {
    actionError.value = 'Failed to approve artifact'
  }
  actionLoading.value = false
}

async function handleLock(): Promise<void> {
  actionLoading.value = true
  actionError.value = null
  const success = await lock(artifactId.value)
  if (success) {
    artifact.value = await fetchArtifactById(artifactId.value)
  } else {
    actionError.value = 'Failed to lock artifact'
  }
  actionLoading.value = false
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

function goBack(): void {
  router.push('/artifacts')
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center space-x-4">
      <button class="btn-secondary text-sm" @click="goBack">
        &larr; Back
      </button>
      <h1 class="text-2xl font-bold text-white">Artifact Detail</h1>
    </div>

    <div v-if="loading" class="text-gray-400">Loading artifact...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <template v-else-if="artifact">
      <!-- Header -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-xl font-semibold text-white">
              {{ artifact.artifact_type.replace(/_/g, ' ') }}
            </h2>
            <p class="text-xs text-gray-500 font-mono mt-1">{{ artifact.id }}</p>
          </div>
          <span
            :class="['status-' + artifact.status, 'px-3 py-1 rounded text-sm']"
          >
            {{ artifact.status }}
          </span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Version</p>
            <p class="text-white">{{ artifact.version }}</p>
          </div>
          <div>
            <p class="text-gray-500">Schema</p>
            <p class="text-white">{{ artifact.schema_version }}</p>
          </div>
          <div>
            <p class="text-gray-500">Created</p>
            <p class="text-white">{{ formatDate(artifact.created_at) }}</p>
          </div>
          <div>
            <p class="text-gray-500">Updated</p>
            <p class="text-white">{{ formatDate(artifact.updated_at) }}</p>
          </div>
        </div>

        <!-- Approval info -->
        <div v-if="artifact.approval" class="mt-4 pt-4 border-t border-rf-secondary/30">
          <p class="text-sm text-gray-500">Approved by</p>
          <p class="text-white">
            {{ artifact.approval.approved_by }}
            <span class="text-gray-500 text-sm">
              on {{ formatDate(artifact.approval.approved_at) }}
            </span>
          </p>
        </div>
      </div>

      <!-- Actions -->
      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-4">Actions</h3>
        <div v-if="actionError" class="text-red-400 text-sm mb-4">
          {{ actionError }}
        </div>
        <div class="flex space-x-3">
          <button
            v-if="canApprove"
            :disabled="actionLoading"
            class="btn-primary"
            @click="handleApprove"
          >
            {{ actionLoading ? 'Approving...' : 'Approve' }}
          </button>
          <button
            v-if="canLock"
            :disabled="actionLoading"
            class="btn-secondary"
            @click="handleLock"
          >
            {{ actionLoading ? 'Locking...' : 'Lock' }}
          </button>
          <button
            v-if="versions.length > 0"
            class="btn-secondary"
            @click="showVersionCompare = true"
          >
            Compare Versions
          </button>
          <span
            v-if="artifact.status === 'locked'"
            class="text-gray-500 text-sm py-2"
          >
            This artifact is locked and cannot be modified.
          </span>
        </div>
      </div>

      <!-- Dependency Graph -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Dependencies</h3>
          <div class="flex items-center space-x-4 text-sm text-gray-400">
            <span v-if="dependencyCount > 0">{{ dependencyCount }} dependencies</span>
            <span v-if="dependentCount > 0">{{ dependentCount }} dependents</span>
          </div>
        </div>
        <div v-if="graphLoading" class="flex items-center justify-center py-8">
          <div class="text-gray-400">Loading graph...</div>
        </div>
        <div v-else-if="dependencyGraph" class="overflow-x-auto">
          <MermaidDiagram :diagram="dependencyGraph" :id="'artifact-' + artifactId + '-graph'" />
        </div>
        <div v-else class="text-gray-500 text-sm py-4">
          No dependencies
        </div>
      </div>

      <!-- Payload -->
      <div class="card">
        <h3 class="text-lg font-semibold text-white mb-4">Payload</h3>
        <pre class="bg-rf-bg-dark rounded p-4 overflow-auto text-sm text-gray-300 font-mono">{{ JSON.stringify(artifact.payload, null, 2) }}</pre>
      </div>

      <!-- Version Compare Modal -->
      <div
        v-if="showVersionCompare"
        class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
        @click.self="showVersionCompare = false"
      >
        <div class="card max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-white">Compare Versions</h3>
            <button
              class="text-gray-400 hover:text-white"
              @click="showVersionCompare = false"
            >
              ✕
            </button>
          </div>

          <div v-if="versionsLoading" class="flex items-center justify-center py-8">
            <div class="text-gray-400">Loading versions...</div>
          </div>

          <div v-else-if="versions.length === 0" class="text-gray-500 text-sm py-4">
            No version history available.
          </div>

          <div v-else-if="versions.length === 1" class="text-gray-500 text-sm py-4">
            Only one version exists. Version comparison requires multiple versions.
            <p class="mt-2 text-xs text-gray-600">
              Version history is tracked when using Git-backed storage or when the artifact is updated.
            </p>
          </div>

          <VersionCompare
            v-else
            :artifact-id="artifactId"
            :versions="versions.map(v => ({
              version: parseInt(v.version) || 1,
              created_at: v.created_at,
              status: v.status
            }))"
            :get-version-payload="getVersionPayload"
          />
        </div>
      </div>
    </template>
  </div>
</template>
