<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'
import { getGitHubLoginUrl, getGoogleLoginUrl } from '@/api/auth'
import ProjectSwitcher from './ProjectSwitcher.vue'

const authStore = useAuthStore()
const projectStore = useProjectStore()

const showLogin = computed(() => authStore.authEnabled && !authStore.isAuthenticated)
const userName = computed(() => authStore.user?.username || authStore.user?.email || 'Anonymous')

function handleLogout(): void {
  authStore.logout()
}
</script>

<template>
  <header class="bg-rf-secondary border-b border-rf-primary/30 px-6 py-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-4">
        <h1 class="text-xl font-bold text-white">
          Rice-Factor
        </h1>
        <ProjectSwitcher />
        <span
          v-if="projectStore.phase"
          class="text-xs text-rf-accent bg-rf-bg-dark/30 px-2 py-1 rounded"
        >
          Phase: {{ projectStore.phase.phase }}
        </span>
      </div>

      <div class="flex items-center space-x-4">
        <!-- Auth section -->
        <template v-if="showLogin">
          <a
            v-if="authStore.providers.includes('github')"
            :href="getGitHubLoginUrl()"
            class="btn-secondary text-sm"
          >
            Login with GitHub
          </a>
          <a
            v-if="authStore.providers.includes('google')"
            :href="getGoogleLoginUrl()"
            class="btn-secondary text-sm"
          >
            Login with Google
          </a>
        </template>
        <template v-else-if="authStore.isAuthenticated">
          <span class="text-sm text-gray-300">{{ userName }}</span>
          <button class="btn-secondary text-sm" @click="handleLogout">
            Logout
          </button>
        </template>
        <template v-else>
          <span class="text-sm text-gray-400">Anonymous</span>
        </template>
      </div>
    </div>
  </header>
</template>
