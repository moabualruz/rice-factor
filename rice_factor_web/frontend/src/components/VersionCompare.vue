<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import MonacoDiffViewer from './MonacoDiffViewer.vue'

export interface Version {
  version: number
  created_at: string
  status: string
  payload_hash?: string
}

const props = defineProps<{
  artifactId: string
  versions: Version[]
  getVersionPayload: (version: number) => Promise<Record<string, unknown>>
}>()

const leftVersion = ref<number | null>(null)
const rightVersion = ref<number | null>(null)
const leftPayload = ref<string>('')
const rightPayload = ref<string>('')
const loading = ref(false)

// Initialize with first and last version if available
if (props.versions.length >= 2) {
  leftVersion.value = props.versions[props.versions.length - 1].version
  rightVersion.value = props.versions[0].version
} else if (props.versions.length === 1) {
  leftVersion.value = props.versions[0].version
  rightVersion.value = props.versions[0].version
}

const sortedVersions = computed(() =>
  [...props.versions].sort((a, b) => b.version - a.version)
)

const canCompare = computed(() =>
  leftVersion.value !== null && rightVersion.value !== null
)

async function loadPayloads(): Promise<void> {
  if (!canCompare.value) return

  loading.value = true
  try {
    const [left, right] = await Promise.all([
      props.getVersionPayload(leftVersion.value!),
      props.getVersionPayload(rightVersion.value!),
    ])
    leftPayload.value = JSON.stringify(left, null, 2)
    rightPayload.value = JSON.stringify(right, null, 2)
  } catch (e) {
    console.error('Failed to load version payloads:', e)
  } finally {
    loading.value = false
  }
}

// Load payloads when versions change
watch([leftVersion, rightVersion], () => {
  loadPayloads()
}, { immediate: true })

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

function getStatusClass(status: string): string {
  switch (status) {
    case 'draft':
      return 'status-draft'
    case 'approved':
      return 'status-approved'
    case 'locked':
      return 'status-locked'
    default:
      return ''
  }
}
</script>

<template>
  <div class="version-compare space-y-4">
    <!-- Version selectors -->
    <div class="flex items-center space-x-4">
      <div class="flex-1">
        <label class="block text-sm text-gray-400 mb-1">Left (Older)</label>
        <select
          v-model="leftVersion"
          class="w-full bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        >
          <option v-for="v in sortedVersions" :key="v.version" :value="v.version">
            v{{ v.version }} - {{ formatDate(v.created_at) }}
            <span v-if="v.status">({{ v.status }})</span>
          </option>
        </select>
      </div>

      <div class="flex items-center pt-6">
        <span class="text-gray-500 text-xl">⇔</span>
      </div>

      <div class="flex-1">
        <label class="block text-sm text-gray-400 mb-1">Right (Newer)</label>
        <select
          v-model="rightVersion"
          class="w-full bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
        >
          <option v-for="v in sortedVersions" :key="v.version" :value="v.version">
            v{{ v.version }} - {{ formatDate(v.created_at) }}
            <span v-if="v.status">({{ v.status }})</span>
          </option>
        </select>
      </div>
    </div>

    <!-- Version metadata -->
    <div class="grid grid-cols-2 gap-4 text-sm">
      <div class="bg-rf-bg-dark/50 rounded p-3">
        <div class="flex items-center justify-between">
          <span class="text-gray-400">Version {{ leftVersion }}</span>
          <span
            v-if="versions.find(v => v.version === leftVersion)?.status"
            :class="[getStatusClass(versions.find(v => v.version === leftVersion)?.status ?? ''), 'px-2 py-0.5 rounded text-xs']"
          >
            {{ versions.find(v => v.version === leftVersion)?.status }}
          </span>
        </div>
      </div>
      <div class="bg-rf-bg-dark/50 rounded p-3">
        <div class="flex items-center justify-between">
          <span class="text-gray-400">Version {{ rightVersion }}</span>
          <span
            v-if="versions.find(v => v.version === rightVersion)?.status"
            :class="[getStatusClass(versions.find(v => v.version === rightVersion)?.status ?? ''), 'px-2 py-0.5 rounded text-xs']"
          >
            {{ versions.find(v => v.version === rightVersion)?.status }}
          </span>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <div class="text-gray-400">Loading versions...</div>
    </div>

    <!-- Diff viewer -->
    <div v-else-if="leftPayload && rightPayload">
      <MonacoDiffViewer
        :original="leftPayload"
        :modified="rightPayload"
        language="json"
        :readonly="true"
      />
    </div>

    <!-- No versions -->
    <div v-else-if="versions.length < 2" class="text-gray-500 text-sm py-4">
      Only one version available. Cannot compare.
    </div>
  </div>
</template>
