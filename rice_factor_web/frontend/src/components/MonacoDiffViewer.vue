<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as monaco from 'monaco-editor'

const props = defineProps<{
  original: string
  modified: string
  language?: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'change', value: string): void
}>()

const containerRef = ref<HTMLDivElement>()
let diffEditor: monaco.editor.IStandaloneDiffEditor | null = null

// Rice-Factor dark theme based on brand colors
const RF_THEME = 'rf-dark'

function initMonaco(): void {
  if (!containerRef.value) return

  // Define Rice-Factor dark theme
  monaco.editor.defineTheme(RF_THEME, {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A9955' },
      { token: 'keyword', foreground: '00c030' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'type', foreground: '4EC9B0' },
      { token: 'function', foreground: 'DCDCAA' },
    ],
    colors: {
      'editor.background': '#0a1a0a',
      'editor.foreground': '#d4d4d4',
      'editor.lineHighlightBackground': '#102010',
      'editor.selectionBackground': '#264f78',
      'editorLineNumber.foreground': '#4b5563',
      'editorLineNumber.activeForeground': '#00a020',
      'editorCursor.foreground': '#00c030',
      'editor.findMatchBackground': '#515c6a',
      'editor.findMatchHighlightBackground': '#1E424D',
      'diffEditor.insertedTextBackground': '#00a02030',
      'diffEditor.removedTextBackground': '#ff444430',
      'diffEditor.insertedLineBackground': '#00a02020',
      'diffEditor.removedLineBackground': '#ff444420',
    },
  })

  // Create diff editor
  diffEditor = monaco.editor.createDiffEditor(containerRef.value, {
    theme: RF_THEME,
    readOnly: props.readonly ?? true,
    automaticLayout: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    renderSideBySide: true,
    enableSplitViewResizing: true,
    fontSize: 13,
    fontFamily: "'Terminus', 'Consolas', 'Courier New', monospace",
    lineNumbers: 'on',
    renderOverviewRuler: true,
    scrollbar: {
      verticalScrollbarSize: 10,
      horizontalScrollbarSize: 10,
    },
  })

  // Set models
  updateModels()

  // Listen for changes on modified model
  if (!props.readonly && diffEditor) {
    const modifiedEditor = diffEditor.getModifiedEditor()
    modifiedEditor.onDidChangeModelContent(() => {
      emit('change', modifiedEditor.getValue())
    })
  }
}

function updateModels(): void {
  if (!diffEditor) return

  const originalModel = monaco.editor.createModel(
    props.original,
    getLanguage(props.language),
  )
  const modifiedModel = monaco.editor.createModel(
    props.modified,
    getLanguage(props.language),
  )

  diffEditor.setModel({
    original: originalModel,
    modified: modifiedModel,
  })
}

function getLanguage(lang?: string): string {
  // Map common file extensions to Monaco language IDs
  const langMap: Record<string, string> = {
    py: 'python',
    python: 'python',
    js: 'javascript',
    javascript: 'javascript',
    ts: 'typescript',
    typescript: 'typescript',
    tsx: 'typescript',
    jsx: 'javascript',
    rs: 'rust',
    rust: 'rust',
    go: 'go',
    golang: 'go',
    java: 'java',
    rb: 'ruby',
    ruby: 'ruby',
    php: 'php',
    c: 'c',
    cpp: 'cpp',
    'c++': 'cpp',
    cs: 'csharp',
    csharp: 'csharp',
    json: 'json',
    yaml: 'yaml',
    yml: 'yaml',
    xml: 'xml',
    html: 'html',
    css: 'css',
    scss: 'scss',
    md: 'markdown',
    markdown: 'markdown',
    sql: 'sql',
    sh: 'shell',
    bash: 'shell',
    zsh: 'shell',
  }

  return langMap[lang?.toLowerCase() ?? ''] ?? 'plaintext'
}

function dispose(): void {
  if (diffEditor) {
    diffEditor.dispose()
    diffEditor = null
  }
}

onMounted(() => {
  initMonaco()
})

onBeforeUnmount(() => {
  dispose()
})

watch(
  () => [props.original, props.modified, props.language],
  () => {
    if (diffEditor) {
      updateModels()
    }
  },
)

// Expose methods for parent component
defineExpose({
  getModifiedContent: () => diffEditor?.getModifiedEditor().getValue() ?? props.modified,
})
</script>

<template>
  <div ref="containerRef" class="monaco-diff-viewer w-full h-[500px] border border-rf-secondary/30 rounded-lg overflow-hidden" />
</template>

<style scoped>
.monaco-diff-viewer :deep(.monaco-editor) {
  border-radius: 0.5rem;
}

.monaco-diff-viewer :deep(.monaco-editor .margin) {
  background-color: #0a1a0a;
}
</style>
