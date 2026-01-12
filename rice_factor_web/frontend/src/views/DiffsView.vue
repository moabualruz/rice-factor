<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useDiffs } from '@/composables/useDiffs'
import type { DiffStatus } from '@/api/types'

const {
  diffs,
  loading,
  error,
  fetchDiffs,
} = useDiffs()

const filterStatus = ref<DiffStatus | ''>('')

const diffStatuses: DiffStatus[] = ['pending', 'approved', 'rejected', 'applied']

onMounted(() => {
  fetchDiffs()
})

watch(filterStatus, () => {
  fetchDiffs({
    status: filterStatus.value || undefined,
  })
})

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getStatusClass(status: DiffStatus): string {
  switch (status) {
    case 'pending':
      return 'status-pending'
    case 'approved':
      return 'status-approved'
    case 'rejected':
      return 'status-rejected'
    case 'applied':
      return 'status-locked'
    default:
      return ''
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Diff Review</h1>
    </div>

    <!-- Filters -->
    <div class="card">
      <label class="block text-sm text-gray-400 mb-1">Status</label>
      <select
        v-model="filterStatus"
        class="bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
      >
        <option value="">All Statuses</option>
        <option v-for="s in diffStatuses" :key="s" :value="s">
          {{ s }}
        </option>
      </select>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="text-gray-400">Loading diffs...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <!-- Diffs list -->
    <div v-else-if="diffs.length === 0" class="card text-gray-500">
      No diffs found.
    </div>
    <div v-else class="space-y-3">
      <RouterLink
        v-for="diff in diffs"
        :key="diff.id"
        :to="`/diffs/${diff.id}`"
        class="card card-hover block"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-white font-medium font-mono text-sm">
              {{ diff.target_file }}
            </p>
            <p class="text-xs text-gray-500 font-mono">{{ diff.id }}</p>
          </div>
          <span :class="[getStatusClass(diff.status), 'px-2 py-1 rounded text-xs']">
            {{ diff.status }}
          </span>
        </div>
        <div class="mt-2 flex items-center space-x-4 text-xs">
          <span class="text-green-400">+{{ diff.lines_added }}</span>
          <span class="text-red-400">-{{ diff.lines_removed }}</span>
          <span class="text-gray-500">{{ diff.language }}</span>
          <span class="text-gray-500">{{ formatDate(diff.created_at) }}</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
