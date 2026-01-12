<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDiffs } from '@/composables/useDiffs'
import type { DiffDetail } from '@/api/types'
import DiffViewer from '@/components/DiffViewer.vue'
import MonacoDiffViewer from '@/components/MonacoDiffViewer.vue'

const route = useRoute()
const router = useRouter()
const { fetchDiffById, approve, reject, loading, error } = useDiffs()

const diff = ref<DiffDetail | null>(null)
const actionLoading = ref(false)
const actionError = ref<string | null>(null)
const rejectReason = ref('')
const showRejectModal = ref(false)

// View mode: 'monaco' for side-by-side, 'unified' for text diff
const viewMode = ref<'monaco' | 'unified'>('monaco')

const diffId = computed(() => route.params.id as string)
const canApprove = computed(() => diff.value?.status === 'pending')
const canReject = computed(() => diff.value?.status === 'pending')
const hasMonacoContent = computed(() =>
  diff.value?.original_content !== undefined && diff.value?.modified_content !== undefined
)

onMounted(async () => {
  diff.value = await fetchDiffById(diffId.value)
})

async function handleApprove(): Promise<void> {
  actionLoading.value = true
  actionError.value = null
  const success = await approve(diffId.value)
  if (success) {
    diff.value = await fetchDiffById(diffId.value)
  } else {
    actionError.value = 'Failed to approve diff'
  }
  actionLoading.value = false
}

async function handleReject(): Promise<void> {
  actionLoading.value = true
  actionError.value = null
  const success = await reject(diffId.value, rejectReason.value)
  if (success) {
    diff.value = await fetchDiffById(diffId.value)
    showRejectModal.value = false
    rejectReason.value = ''
  } else {
    actionError.value = 'Failed to reject diff'
  }
  actionLoading.value = false
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

function goBack(): void {
  router.push('/diffs')
}

function getStatusClass(status: string): string {
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
    <div class="flex items-center space-x-4">
      <button class="btn-secondary text-sm" @click="goBack">
        &larr; Back
      </button>
      <h1 class="text-2xl font-bold text-white">Diff Review</h1>
    </div>

    <div v-if="loading" class="text-gray-400">Loading diff...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <template v-else-if="diff">
      <!-- Header -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h2 class="text-lg font-semibold text-white font-mono">
              {{ diff.target_file }}
            </h2>
            <p class="text-xs text-gray-500 font-mono mt-1">{{ diff.id }}</p>
          </div>
          <span :class="[getStatusClass(diff.status), 'px-3 py-1 rounded text-sm']">
            {{ diff.status }}
          </span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p class="text-gray-500">Lines Added</p>
            <p class="text-green-400 font-mono">+{{ diff.lines_added }}</p>
          </div>
          <div>
            <p class="text-gray-500">Lines Removed</p>
            <p class="text-red-400 font-mono">-{{ diff.lines_removed }}</p>
          </div>
          <div>
            <p class="text-gray-500">Language</p>
            <p class="text-white">{{ diff.language }}</p>
          </div>
          <div>
            <p class="text-gray-500">Created</p>
            <p class="text-white">{{ formatDate(diff.created_at) }}</p>
          </div>
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
            v-if="canReject"
            :disabled="actionLoading"
            class="btn-danger"
            @click="showRejectModal = true"
          >
            Reject
          </button>
          <span
            v-if="diff.status === 'applied'"
            class="text-gray-500 text-sm py-2"
          >
            This diff has been applied.
          </span>
        </div>
      </div>

      <!-- Diff content -->
      <div class="card">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-white">Changes</h3>
          <div v-if="hasMonacoContent" class="flex items-center space-x-2">
            <button
              :class="[
                'px-3 py-1 text-sm rounded transition-colors',
                viewMode === 'monaco'
                  ? 'bg-rf-primary text-white'
                  : 'bg-rf-bg-dark text-gray-400 hover:text-white'
              ]"
              @click="viewMode = 'monaco'"
            >
              Side by Side
            </button>
            <button
              :class="[
                'px-3 py-1 text-sm rounded transition-colors',
                viewMode === 'unified'
                  ? 'bg-rf-primary text-white'
                  : 'bg-rf-bg-dark text-gray-400 hover:text-white'
              ]"
              @click="viewMode = 'unified'"
            >
              Unified
            </button>
          </div>
        </div>

        <!-- Monaco side-by-side diff viewer -->
        <MonacoDiffViewer
          v-if="hasMonacoContent && viewMode === 'monaco'"
          :original="diff.original_content ?? ''"
          :modified="diff.modified_content ?? ''"
          :language="diff.language"
          :readonly="true"
        />

        <!-- Unified text diff viewer (fallback or when selected) -->
        <DiffViewer
          v-else
          :content="diff.content"
          :language="diff.language"
          :diff-id="diff.id"
          :enable-comments="true"
        />
      </div>

      <!-- Reject modal -->
      <div
        v-if="showRejectModal"
        class="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
        @click.self="showRejectModal = false"
      >
        <div class="card max-w-md w-full mx-4">
          <h3 class="text-lg font-semibold text-white mb-4">Reject Diff</h3>
          <div class="mb-4">
            <label class="block text-sm text-gray-400 mb-1">Reason (optional)</label>
            <textarea
              v-model="rejectReason"
              class="w-full bg-rf-bg-dark border border-rf-secondary/50 rounded px-3 py-2 text-sm text-gray-200"
              rows="3"
              placeholder="Enter reason for rejection..."
            />
          </div>
          <div class="flex justify-end space-x-3">
            <button
              class="btn-secondary"
              @click="showRejectModal = false"
            >
              Cancel
            </button>
            <button
              :disabled="actionLoading"
              class="btn-danger"
              @click="handleReject"
            >
              {{ actionLoading ? 'Rejecting...' : 'Reject' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
