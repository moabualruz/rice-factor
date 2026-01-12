<script setup lang="ts">
import type { Toast, ToastType } from '@/stores/notifications'

const props = defineProps<{
  toast: Toast
}>()

const emit = defineEmits<{
  close: [id: string]
}>()

function getIconClass(type: ToastType): string {
  switch (type) {
    case 'success':
      return 'text-green-400'
    case 'error':
      return 'text-red-400'
    case 'warning':
      return 'text-yellow-400'
    case 'info':
      return 'text-blue-400'
  }
}

function getIcon(type: ToastType): string {
  switch (type) {
    case 'success':
      return '&#10003;'  // checkmark
    case 'error':
      return '&#10007;'  // x
    case 'warning':
      return '&#9888;'   // warning triangle
    case 'info':
      return '&#8505;'   // info
  }
}

function getBorderClass(type: ToastType): string {
  switch (type) {
    case 'success':
      return 'border-l-green-500'
    case 'error':
      return 'border-l-red-500'
    case 'warning':
      return 'border-l-yellow-500'
    case 'info':
      return 'border-l-blue-500'
  }
}

function handleClose(): void {
  emit('close', props.toast.id)
}

function handleAction(): void {
  if (props.toast.action) {
    props.toast.action.handler()
    handleClose()
  }
}
</script>

<template>
  <div
    :class="[
      'flex items-start p-4 bg-rf-bg-light border-l-4 rounded-r-lg shadow-lg',
      'animate-slide-in',
      getBorderClass(toast.type)
    ]"
    role="alert"
  >
    <span
      :class="['text-xl mr-3 flex-shrink-0', getIconClass(toast.type)]"
      v-html="getIcon(toast.type)"
    />
    <div class="flex-1 min-w-0">
      <p class="font-medium text-white">{{ toast.title }}</p>
      <p v-if="toast.message" class="text-sm text-gray-400 mt-1">
        {{ toast.message }}
      </p>
      <button
        v-if="toast.action"
        class="mt-2 text-sm text-rf-accent hover:text-rf-primary underline"
        @click="handleAction"
      >
        {{ toast.action.label }}
      </button>
    </div>
    <button
      class="ml-4 text-gray-500 hover:text-gray-300 transition-colors"
      aria-label="Close"
      @click="handleClose"
    >
      &times;
    </button>
  </div>
</template>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
