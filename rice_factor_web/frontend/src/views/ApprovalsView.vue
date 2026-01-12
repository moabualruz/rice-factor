<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { listPendingApprovals } from '@/api/approvals'
import { useArtifacts } from '@/composables/useArtifacts'
import { useDiffs } from '@/composables/useDiffs'
import type { ApprovalListResponse, PendingApproval } from '@/api/types'

const { approve: approveArtifact } = useArtifacts()
const { approve: approveDiff } = useDiffs()

const approvals = ref<ApprovalListResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const actionLoading = ref<string | null>(null)

onMounted(async () => {
  await loadApprovals()
})

async function loadApprovals(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    approvals.value = await listPendingApprovals()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load approvals'
  } finally {
    loading.value = false
  }
}

async function handleApprove(item: PendingApproval): Promise<void> {
  actionLoading.value = item.id
  try {
    if (item.item_type === 'artifact') {
      await approveArtifact(item.id)
    } else {
      await approveDiff(item.id)
    }
    await loadApprovals()
  } catch (e) {
    console.error('Approval failed:', e)
  } finally {
    actionLoading.value = null
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function getDetailLink(item: PendingApproval): string {
  if (item.item_type === 'artifact') {
    return `/artifacts/${item.id}`
  }
  return `/diffs/${item.id}`
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Pending Approvals</h1>
      <div v-if="approvals" class="flex space-x-4 text-sm">
        <span class="text-gray-400">
          {{ approvals.total_pending }} pending
        </span>
        <span class="text-green-400">
          {{ approvals.approved_today }} approved today
        </span>
      </div>
    </div>

    <div v-if="loading" class="text-gray-400">Loading approvals...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <div v-else-if="!approvals || approvals.pending.length === 0" class="card text-gray-500">
      No pending approvals. All caught up!
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="item in approvals.pending"
        :key="item.id"
        class="card card-hover"
      >
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <div class="flex items-center space-x-3">
              <span
                :class="[
                  'px-2 py-0.5 rounded text-xs',
                  item.item_type === 'artifact' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                ]"
              >
                {{ item.item_type }}
              </span>
              <span
                v-if="item.priority === 'high'"
                class="px-2 py-0.5 rounded text-xs bg-red-500/20 text-red-400"
              >
                High Priority
              </span>
            </div>
            <RouterLink
              :to="getDetailLink(item)"
              class="block mt-2 text-white font-medium hover:text-rf-accent"
            >
              {{ item.name }}
            </RouterLink>
            <p class="text-xs text-gray-500 mt-1">
              {{ formatDate(item.created_at) }} &bull; {{ item.age_days }} days old
            </p>
          </div>
          <div class="flex space-x-2">
            <RouterLink
              :to="getDetailLink(item)"
              class="btn-secondary text-sm"
            >
              Review
            </RouterLink>
            <button
              :disabled="actionLoading === item.id"
              class="btn-primary text-sm"
              @click="handleApprove(item)"
            >
              {{ actionLoading === item.id ? 'Approving...' : 'Approve' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
