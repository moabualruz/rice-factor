<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import ToastContainer from '@/components/ToastContainer.vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { useWebSocket } from '@/composables/useWebSocket'
import { useToast } from '@/composables/useToast'

const authStore = useAuthStore()
const projectStore = useProjectStore()
const { connect, subscribe } = useWebSocket()
const toast = useToast()

// Initialize auth, project, and WebSocket on app mount
authStore.checkAuth()
projectStore.refresh()
connect()

// Subscribe to WebSocket events and show toasts
subscribe('artifact_created', (event) => {
  toast.info('Artifact Created', `New ${event.payload.artifact_type} artifact`)
})

subscribe('artifact_approved', (event) => {
  toast.success('Artifact Approved', `${event.payload.artifact_type} has been approved`)
})

subscribe('artifact_locked', (event) => {
  toast.info('Artifact Locked', `${event.payload.artifact_type} is now locked`)
})

subscribe('diff_created', () => {
  toast.info('New Diff', 'A new diff is ready for review')
})

subscribe('diff_approved', (event) => {
  toast.success('Diff Approved', `Diff for ${event.payload.file_path || 'file'} approved`)
})

subscribe('diff_rejected', (event) => {
  toast.warning('Diff Rejected', `Diff for ${event.payload.file_path || 'file'} rejected`)
})

subscribe('error', (event) => {
  toast.error('Error', event.payload.message as string || 'An error occurred')
})
</script>

<template>
  <div class="min-h-screen bg-rf-bg-dark flex flex-col">
    <AppHeader />
    <div class="flex flex-1">
      <AppSidebar />
      <main class="flex-1 p-6 overflow-auto">
        <RouterView />
      </main>
    </div>
    <ToastContainer />
  </div>
</template>
