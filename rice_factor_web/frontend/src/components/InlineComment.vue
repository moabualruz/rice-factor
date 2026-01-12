<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  lineNumber: number
  existingComment?: string
  author?: string
  timestamp?: string
}>()

const emit = defineEmits<{
  (e: 'save', comment: string): void
  (e: 'delete'): void
  (e: 'cancel'): void
}>()

const isEditing = ref(!props.existingComment)
const commentText = ref(props.existingComment ?? '')

function handleSave(): void {
  if (commentText.value.trim()) {
    emit('save', commentText.value.trim())
    isEditing.value = false
  }
}

function handleDelete(): void {
  emit('delete')
}

function handleCancel(): void {
  if (props.existingComment) {
    commentText.value = props.existingComment
    isEditing.value = false
  } else {
    emit('cancel')
  }
}

function formatTimestamp(ts?: string): string {
  if (!ts) return ''
  return new Date(ts).toLocaleString()
}
</script>

<template>
  <div class="inline-comment bg-rf-bg-light border-l-2 border-rf-primary p-3 my-1 rounded-r">
    <!-- Existing comment display -->
    <div v-if="existingComment && !isEditing" class="space-y-2">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2 text-xs text-gray-400">
          <span v-if="author" class="font-medium text-gray-300">{{ author }}</span>
          <span v-if="timestamp">{{ formatTimestamp(timestamp) }}</span>
          <span class="text-gray-600">Line {{ lineNumber }}</span>
        </div>
        <div class="flex items-center space-x-2">
          <button
            class="text-xs text-gray-400 hover:text-white transition-colors"
            @click="isEditing = true"
          >
            Edit
          </button>
          <button
            class="text-xs text-red-400 hover:text-red-300 transition-colors"
            @click="handleDelete"
          >
            Delete
          </button>
        </div>
      </div>
      <p class="text-sm text-gray-200 whitespace-pre-wrap">{{ existingComment }}</p>
    </div>

    <!-- Comment editor -->
    <div v-else class="space-y-2">
      <div class="flex items-center space-x-2 text-xs text-gray-500">
        <span>Comment on line {{ lineNumber }}</span>
      </div>
      <textarea
        v-model="commentText"
        class="w-full bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200 resize-none focus:outline-none focus:border-rf-primary"
        rows="3"
        placeholder="Add a comment..."
        @keydown.ctrl.enter="handleSave"
        @keydown.meta.enter="handleSave"
      />
      <div class="flex items-center justify-between">
        <span class="text-xs text-gray-600">Ctrl+Enter to save</span>
        <div class="flex items-center space-x-2">
          <button
            class="px-3 py-1 text-sm text-gray-400 hover:text-white transition-colors"
            @click="handleCancel"
          >
            Cancel
          </button>
          <button
            class="px-3 py-1 text-sm bg-rf-primary text-white rounded hover:bg-rf-accent transition-colors disabled:opacity-50"
            :disabled="!commentText.trim()"
            @click="handleSave"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
