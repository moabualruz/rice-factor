<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  getConfiguration,
  updateConfiguration,
  type ConfigResponse,
} from "@/api/configuration";

const loading = ref(true);
const saving = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

const config = ref<ConfigResponse | null>(null);
const activeTab = ref<"merged" | "project" | "user">("merged");
const editContent = ref("");

onMounted(loadConfig);

async function loadConfig() {
  loading.value = true;
  error.value = null;
  try {
    config.value = await getConfiguration();
    if (activeTab.value === "project") {
      editContent.value = config.value.project_config || "";
    } else if (activeTab.value === "user") {
      editContent.value = config.value.user_config || "";
    }
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function selectTab(tab: "merged" | "project" | "user") {
  activeTab.value = tab;
  successMessage.value = null;
  if (config.value) {
    if (tab === "project") {
      editContent.value = config.value.project_config || "";
    } else if (tab === "user") {
      editContent.value = config.value.user_config || "";
    }
  }
}

async function saveConfig() {
  if (!config.value) return;

  saving.value = true;
  error.value = null;
  successMessage.value = null;

  try {
    // Both project and user scopes are supported by the backend.
    // The scope is determined by the active tab.
    const scope = activeTab.value === "user" ? "user" : "project";

    await updateConfiguration({
      content: editContent.value,
      scope: scope,
    });

    // Reload to confirm application
    await loadConfig();
    successMessage.value = "Configuration saved and reloaded.";
  } catch (e: any) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-white">Configuration Manager</h1>
      <button
        class="btn-secondary text-sm"
        @click="loadConfig"
        :disabled="loading"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading && !config" class="text-gray-400">
      Loading configuration...
    </div>
    <div
      v-else-if="error"
      class="bg-red-900/20 border border-red-500/50 text-red-500 p-4 rounded"
    >
      {{ error }}
    </div>

    <div v-if="config" class="space-y-4">
      <!-- Tabs -->
      <div class="flex border-b border-rf-secondary/30">
        <button
          v-for="tab in ['merged', 'project', 'user']"
          :key="tab"
          @click="selectTab(tab as any)"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
            activeTab === tab
              ? 'border-rf-success text-rf-success'
              : 'border-transparent text-gray-400 hover:text-white',
          ]"
        >
          {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
        </button>
      </div>

      <!-- Content -->
      <div class="card p-4">
        <!-- Message -->
        <div v-if="successMessage" class="mb-4 text-green-400 text-sm">
          {{ successMessage }}
        </div>

        <div v-if="activeTab === 'merged'">
          <div class="mb-2 text-xs text-gray-500">
            Current runtime configuration (read-only).
          </div>
          <pre
            class="bg-rf-bg-dark p-4 rounded overflow-auto h-[600px] text-xs font-mono text-gray-300"
            >{{ JSON.stringify(config.merged, null, 2) }}</pre
          >
        </div>

        <div v-else>
          <div class="flex justify-between items-center mb-2">
            <div class="text-xs text-gray-500 font-mono">
              {{
                activeTab === "project"
                  ? config.project_config_path
                  : config.user_config_path
              }}
            </div>
            <button
              class="btn-primary text-xs"
              @click="saveConfig"
              :disabled="saving"
            >
              {{ saving ? "Saving..." : "Save Changes" }}
            </button>
          </div>
          <textarea
            v-model="editContent"
            class="w-full h-[600px] bg-rf-bg-dark text-gray-300 font-mono text-sm p-4 rounded border border-rf-secondary focus:border-rf-success outline-none"
            spellcheck="false"
          ></textarea>
        </div>
      </div>
    </div>
  </div>
</template>
