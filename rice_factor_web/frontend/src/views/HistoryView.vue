<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { getHistory, exportHistory } from '@/api/history'
import type { HistoryResponse, HistoryEntry, ArtifactType } from '@/api/types'

const history = ref<HistoryResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const exporting = ref(false)

const filterEventType = ref('')
const filterArtifactType = ref<ArtifactType | ''>('')
const filterStartDate = ref('')
const filterEndDate = ref('')

const eventTypes = [
  'artifact_created',
  'artifact_approved',
  'artifact_locked',
  'diff_created',
  'diff_approved',
  'diff_rejected',
  'diff_applied',
]

const artifactTypes: ArtifactType[] = [
  'project_plan',
  'architecture_plan',
  'scaffold_plan',
  'test_plan',
  'implementation_plan',
  'refactor_plan',
  'validation_result',
]

onMounted(async () => {
  await loadHistory()
})

watch([filterEventType, filterArtifactType, filterStartDate, filterEndDate], () => {
  loadHistory()
})

async function loadHistory(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    history.value = await getHistory({
      event_type: filterEventType.value || undefined,
      artifact_type: filterArtifactType.value || undefined,
      start_date: filterStartDate.value || undefined,
      end_date: filterEndDate.value || undefined,
      limit: 50,
    })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load history'
  } finally {
    loading.value = false
  }
}

async function handleExport(format: 'json' | 'csv'): Promise<void> {
  exporting.value = true
  try {
    const blob = await exportHistory(format, {
      start_date: filterStartDate.value || undefined,
      end_date: filterEndDate.value || undefined,
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `history.${format}`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

function getEventIcon(eventType: string): string {
  if (eventType.includes('created')) return '+'
  if (eventType.includes('approved')) return '&#10003;'
  if (eventType.includes('locked')) return '&#128274;'
  if (eventType.includes('rejected')) return '&#10007;'
  if (eventType.includes('applied')) return '&#9658;'
  return '&#8226;'
}

function getEventColor(eventType: string): string {
  if (eventType.includes('created')) return 'border-blue-500 bg-blue-500/10'
  if (eventType.includes('approved')) return 'border-green-500 bg-green-500/10'
  if (eventType.includes('locked')) return 'border-purple-500 bg-purple-500/10'
  if (eventType.includes('rejected')) return 'border-red-500 bg-red-500/10'
  if (eventType.includes('applied')) return 'border-yellow-500 bg-yellow-500/10'
  return 'border-gray-500 bg-gray-500/10'
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">History</h1>
      <div class="flex space-x-2">
        <button
          :disabled="exporting"
          class="btn-secondary text-sm"
          @click="handleExport('json')"
        >
          Export JSON
        </button>
        <button
          :disabled="exporting"
          class="btn-secondary text-sm"
          @click="handleExport('csv')"
        >
          Export CSV
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="card flex flex-wrap gap-4">
      <div>
        <label class="block text-sm text-gray-400 mb-1">Event Type</label>
        <select
          v-model="filterEventType"
          class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        >
          <option value="">All Events</option>
          <option v-for="e in eventTypes" :key="e" :value="e">
            {{ e.replace(/_/g, ' ') }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">Artifact Type</label>
        <select
          v-model="filterArtifactType"
          class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        >
          <option value="">All Types</option>
          <option v-for="t in artifactTypes" :key="t" :value="t">
            {{ t.replace(/_/g, ' ') }}
          </option>
        </select>
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">Start Date</label>
        <input
          v-model="filterStartDate"
          type="date"
          class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        />
      </div>
      <div>
        <label class="block text-sm text-gray-400 mb-1">End Date</label>
        <input
          v-model="filterEndDate"
          type="date"
          class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        />
      </div>
    </div>

    <div v-if="loading" class="text-gray-400">Loading history...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <div v-else-if="!history || history.entries.length === 0" class="card text-gray-500">
      No history entries found.
    </div>

    <!-- Timeline -->
    <div v-else class="space-y-1">
      <div
        v-for="entry in history.entries"
        :key="entry.id"
        :class="[
          'card py-3 border-l-4',
          getEventColor(entry.event_type)
        ]"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-start space-x-3">
            <span
              class="text-lg font-mono"
              v-html="getEventIcon(entry.event_type)"
            />
            <div>
              <p class="text-white font-medium">
                {{ entry.event_type.replace(/_/g, ' ') }}
              </p>
              <p v-if="entry.artifact_type" class="text-sm text-gray-400">
                {{ entry.artifact_type.replace(/_/g, ' ') }}
              </p>
              <p v-if="entry.artifact_id" class="text-xs text-gray-500 font-mono">
                {{ entry.artifact_id }}
              </p>
            </div>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-400">{{ entry.actor }}</p>
            <p class="text-xs text-gray-500">{{ formatDate(entry.timestamp) }}</p>
          </div>
        </div>
      </div>

      <div v-if="history.has_more" class="text-center py-4">
        <span class="text-gray-500 text-sm">
          Showing {{ history.entries.length }} of {{ history.total }} entries
        </span>
      </div>
    </div>
  </div>
</template>
