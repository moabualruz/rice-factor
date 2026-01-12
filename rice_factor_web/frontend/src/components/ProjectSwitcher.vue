<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api/client'
import { useToast } from '@/composables/useToast'

interface ProjectInfo {
  root: string
  name: string
  is_current: boolean
  initialized: boolean
}

interface ProjectListResponse {
  projects: ProjectInfo[]
  current: string
}

const projects = ref<ProjectInfo[]>([])
const currentProject = ref<string>('')
const loading = ref(false)
const isOpen = ref(false)
const toast = useToast()

async function loadProjects(): Promise<void> {
  loading.value = true
  try {
    const response = await api.get<ProjectListResponse>('/projects')
    projects.value = response.projects
    currentProject.value = response.current
  } catch (e) {
    console.error('Failed to load projects:', e)
  } finally {
    loading.value = false
  }
}

async function handleSwitch(project: ProjectInfo): Promise<void> {
  if (project.is_current) {
    isOpen.value = false
    return
  }

  try {
    const response = await api.post<{ message: string }>('/projects/switch', {
      root: project.root,
    })
    toast.info('Project Switch', response.message)
    isOpen.value = false
  } catch (e) {
    toast.error('Switch Failed', e instanceof Error ? e.message : 'Failed to switch project')
  }
}

function toggleDropdown(): void {
  isOpen.value = !isOpen.value
}

function closeDropdown(): void {
  isOpen.value = false
}

onMounted(() => {
  loadProjects()
})
</script>

<template>
  <div class="relative" @mouseleave="closeDropdown">
    <button
      class="flex items-center space-x-2 px-3 py-1.5 rounded bg-rf-bg-dark/50 hover:bg-rf-bg-dark text-sm transition-colors"
      @click="toggleDropdown"
    >
      <span class="text-gray-300">{{ projects.find(p => p.is_current)?.name || 'Project' }}</span>
      <span class="text-gray-500 text-xs">&#9662;</span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute top-full left-0 mt-1 w-64 bg-rf-bg-light border border-rf-secondary/30 rounded-lg shadow-xl z-50"
      >
        <div class="p-2">
          <p class="text-xs text-gray-500 px-2 py-1">Projects</p>
          <div v-if="loading" class="px-2 py-3 text-gray-400 text-sm">
            Loading...
          </div>
          <div v-else-if="projects.length === 0" class="px-2 py-3 text-gray-500 text-sm">
            No projects found
          </div>
          <ul v-else class="space-y-1">
            <li v-for="project in projects" :key="project.root">
              <button
                :class="[
                  'w-full text-left px-2 py-2 rounded text-sm transition-colors',
                  project.is_current
                    ? 'bg-rf-primary/20 text-rf-accent'
                    : 'text-gray-300 hover:bg-rf-bg-dark'
                ]"
                @click="handleSwitch(project)"
              >
                <div class="flex items-center justify-between">
                  <span class="font-medium truncate">{{ project.name }}</span>
                  <span
                    v-if="project.is_current"
                    class="text-xs text-rf-primary"
                  >
                    Current
                  </span>
                </div>
                <p class="text-xs text-gray-500 truncate mt-0.5">
                  {{ project.root }}
                </p>
              </button>
            </li>
          </ul>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
