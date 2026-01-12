<script setup lang="ts">
import type { PhaseInfo } from '@/api/types'

defineProps<{
  phase: PhaseInfo
}>()

const phaseColors: Record<string, string> = {
  init: 'bg-gray-500',
  planning: 'bg-yellow-500',
  architecture: 'bg-blue-500',
  testing: 'bg-purple-500',
  implementation: 'bg-rf-primary',
}
</script>

<template>
  <div class="flex items-center space-x-3">
    <div
      :class="[
        'w-3 h-3 rounded-full',
        phaseColors[phase.phase] || 'bg-gray-500'
      ]"
    />
    <div>
      <p class="text-sm font-medium text-white capitalize">{{ phase.phase }}</p>
      <p class="text-xs text-gray-400">{{ phase.description }}</p>
    </div>
  </div>
</template>
