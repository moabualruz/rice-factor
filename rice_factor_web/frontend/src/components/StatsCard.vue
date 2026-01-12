<script setup lang="ts">
defineProps<{
  title: string
  value: number | string
  icon?: 'artifacts' | 'approvals' | 'diff' | 'success'
  highlight?: boolean
}>()
</script>

<template>
  <div
    :class="[
      'card card-hover p-4',
      highlight ? 'border-rf-accent' : ''
    ]"
  >
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm text-gray-400">{{ title }}</p>
        <p class="text-2xl font-bold text-white mt-1">{{ value }}</p>
      </div>
      <div class="text-3xl text-rf-primary/60">
        <template v-if="icon === 'artifacts'">&#128230;</template>
        <template v-else-if="icon === 'approvals'">&#10003;</template>
        <template v-else-if="icon === 'diff'">&#8801;</template>
        <template v-else-if="icon === 'success'">&#9989;</template>
      </div>
    </div>
  </div>
</template>
