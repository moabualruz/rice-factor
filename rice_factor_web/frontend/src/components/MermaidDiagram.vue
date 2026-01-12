<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps<{
  diagram: string
  id?: string
}>()

const container = ref<HTMLDivElement | null>(null)
const error = ref<string | null>(null)
const rendered = ref(false)

// Generate unique ID for this diagram
const diagramId = props.id || `mermaid-${Date.now()}`

async function renderDiagram(): Promise<void> {
  if (!container.value || !props.diagram) {
    return
  }

  error.value = null
  rendered.value = false

  try {
    // Dynamic import mermaid
    const mermaid = await import('mermaid')

    // Initialize with dark theme matching Rice-Factor brand
    mermaid.default.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#00a020',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#009e20',
        lineColor: '#00c030',
        secondaryColor: '#102010',
        tertiaryColor: '#0a1a0a',
        background: '#0a1a0a',
        mainBkg: '#102010',
        nodeBorder: '#009e20',
        clusterBkg: '#102010',
        clusterBorder: '#009e20',
        titleColor: '#ffffff',
        edgeLabelBackground: '#102010',
      },
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
      },
    })

    // Render the diagram
    const { svg } = await mermaid.default.render(diagramId, props.diagram)
    container.value.innerHTML = svg
    rendered.value = true
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to render diagram'
    console.error('Mermaid render error:', e)
  }
}

onMounted(() => {
  renderDiagram()
})

watch(() => props.diagram, () => {
  nextTick(() => renderDiagram())
})
</script>

<template>
  <div class="mermaid-container">
    <div v-if="error" class="text-red-400 text-sm p-4 bg-rf-bg-dark rounded">
      <p class="font-medium">Failed to render diagram</p>
      <p class="text-xs mt-1">{{ error }}</p>
    </div>
    <div
      v-show="!error"
      ref="container"
      class="mermaid-svg overflow-auto"
    />
    <div v-if="!rendered && !error" class="text-gray-500 text-sm p-4">
      Loading diagram...
    </div>
  </div>
</template>

<style scoped>
.mermaid-container {
  @apply bg-rf-bg-dark rounded-lg border border-rf-secondary/30 p-4;
}

.mermaid-svg :deep(svg) {
  max-width: 100%;
  height: auto;
}

.mermaid-svg :deep(.node rect),
.mermaid-svg :deep(.node circle),
.mermaid-svg :deep(.node polygon) {
  stroke-width: 2px;
}

.mermaid-svg :deep(.edgePath path) {
  stroke-width: 2px;
}
</style>
