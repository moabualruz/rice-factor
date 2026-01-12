<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getGitHubLoginUrl, getGoogleLoginUrl } from '@/api/auth'

const authStore = useAuthStore()

const hasGitHub = computed(() => authStore.providers.includes('github'))
const hasGoogle = computed(() => authStore.providers.includes('google'))
const noProviders = computed(() => !authStore.authEnabled || authStore.providers.length === 0)
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center">
    <div class="card max-w-md w-full text-center">
      <h1 class="text-2xl font-bold text-white mb-2">Welcome to Rice-Factor</h1>
      <p class="text-gray-400 mb-8">Sign in to access team features</p>

      <div v-if="noProviders" class="text-gray-500">
        <p class="mb-4">Authentication is not configured.</p>
        <p class="text-sm">
          The application is running in anonymous mode.
          All features are available without login.
        </p>
      </div>

      <div v-else class="space-y-4">
        <a
          v-if="hasGitHub"
          :href="getGitHubLoginUrl()"
          class="btn-primary w-full flex items-center justify-center space-x-2"
        >
          <span>Continue with GitHub</span>
        </a>

        <a
          v-if="hasGoogle"
          :href="getGoogleLoginUrl()"
          class="btn-secondary w-full flex items-center justify-center space-x-2"
        >
          <span>Continue with Google</span>
        </a>

        <div class="pt-4 border-t border-rf-secondary/30">
          <p class="text-sm text-gray-500">
            Or continue as
            <RouterLink to="/" class="link">anonymous user</RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
