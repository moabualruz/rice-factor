<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useProjectStore } from "@/stores/project";
import { initProject } from "@/api/projects";

const router = useRouter();
const projectStore = useProjectStore();

const loading = ref(false);
const error = ref<string | null>(null);
const success = ref(false);

async function handleInit() {
  loading.value = true;
  error.value = null;
  try {
    await initProject();
    await projectStore.refresh();
    success.value = true;
    setTimeout(() => {
      router.push("/");
    }, 1500);
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Initialization failed";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto py-12 px-4">
    <div
      class="bg-gray-900 rounded-lg shadow-xl border border-gray-800 p-8 text-center"
    >
      <h1 class="text-3xl font-bold text-white mb-4">Welcome to Rice-Factor</h1>
      <p class="text-gray-400 mb-8 max-w-md mx-auto">
        Your project hasn't been initialized yet. Initialize it now to start
        using Rice-Factor's LLM-assisted development features.
      </p>

      <div
        v-if="error"
        class="bg-red-900/50 border border-red-800 text-red-200 p-4 rounded mb-6 text-sm"
      >
        {{ error }}
      </div>

      <div
        v-if="success"
        class="bg-green-900/50 border border-green-800 text-green-200 p-4 rounded mb-6 text-sm"
      >
        Project initialized successfully! Redirecting...
      </div>

      <button
        @click="handleInit"
        :disabled="loading || success"
        class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center mx-auto"
      >
        <svg
          v-if="loading"
          class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        {{ loading ? "Initializing..." : "Initialize Project" }}
      </button>

      <div class="mt-8 text-sm text-gray-500">
        This will create a
        <code class="text-gray-400">.project/</code> directory in the current
        workspace.
      </div>
    </div>
  </div>
</template>
