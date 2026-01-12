<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getHistory } from '@/api/history'
import type { HistoryEntry } from '@/api/types'

const entries = ref<HistoryEntry[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    const response = await getHistory({ limit: 10 })
    entries.value = response.entries
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load activity'
  } finally {
    loading.value = false
  }
})

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

function getEventIcon(eventType: string): string {
  if (eventType.includes('created')) return '+'
  if (eventType.includes('approved')) return '&#10003;'
  if (eventType.includes('locked')) return '&#128274;'
  if (eventType.includes('rejected')) return '&#10007;'
  return '&#8226;'
}

function getEventColor(eventType: string): string {
  if (eventType.includes('created')) return 'text-blue-400'
  if (eventType.includes('approved')) return 'text-green-400'
  if (eventType.includes('locked')) return 'text-purple-400'
  if (eventType.includes('rejected')) return 'text-red-400'
  return 'text-gray-400'
}
</script>

<template>
  <div>
    <div v-if="loading" class="text-gray-400 text-sm">Loading activity...</div>
    <div v-else-if="error" class="text-red-400 text-sm">{{ error }}</div>
    <div v-else-if="entries.length === 0" class="text-gray-500 text-sm">
      No recent activity
    </div>
    <ul v-else class="space-y-3">
      <li
        v-for="entry in entries"
        :key="entry.id"
        class="flex items-start space-x-3 text-sm"
      >
        <span
          :class="[getEventColor(entry.event_type), 'font-mono text-lg']"
          v-html="getEventIcon(entry.event_type)"
        />
        <div class="flex-1 min-w-0">
          <p class="text-gray-300 truncate">
            <span class="font-medium">{{ entry.event_type.replace(/_/g, ' ') }}</span>
            <span v-if="entry.artifact_type" class="text-gray-500">
              - {{ entry.artifact_type }}
            </span>
          </p>
          <p class="text-xs text-gray-500">
            {{ entry.actor }} &bull; {{ formatTime(entry.timestamp) }}
          </p>
        </div>
      </li>
    </ul>
  </div>
</template>
