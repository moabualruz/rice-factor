<script setup lang="ts">
import { computed, ref } from 'vue'
import InlineComment from './InlineComment.vue'
import { useInlineComments, type InlineComment as CommentType } from '@/composables/useInlineComments'

const props = defineProps<{
  content: string
  language?: string
  diffId?: string
  enableComments?: boolean
}>()

const emit = defineEmits<{
  (e: 'comment-added', lineNumber: number, content: string): void
  (e: 'comment-deleted', lineNumber: number): void
}>()

const { getCommentsForLine, addComment, deleteComment } = useInlineComments()

// Track which lines have open comment forms
const openCommentLines = ref<Set<number>>(new Set())

interface DiffLine {
  type: 'added' | 'removed' | 'context' | 'header'
  content: string
  lineNumber?: number
}

const parsedLines = computed<DiffLine[]>(() => {
  const lines = props.content.split('\n')
  let oldLine = 0
  let newLine = 0

  return lines.map((line): DiffLine => {
    if (line.startsWith('@@')) {
      // Parse hunk header to get line numbers
      const match = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/)
      if (match) {
        oldLine = parseInt(match[1], 10) - 1
        newLine = parseInt(match[2], 10) - 1
      }
      return { type: 'header', content: line }
    }

    if (line.startsWith('+') && !line.startsWith('+++')) {
      newLine++
      return { type: 'added', content: line.substring(1), lineNumber: newLine }
    }

    if (line.startsWith('-') && !line.startsWith('---')) {
      oldLine++
      return { type: 'removed', content: line.substring(1), lineNumber: oldLine }
    }

    if (line.startsWith(' ')) {
      oldLine++
      newLine++
      return { type: 'context', content: line.substring(1), lineNumber: newLine }
    }

    return { type: 'context', content: line }
  })
})

function getLineClass(type: DiffLine['type']): string {
  switch (type) {
    case 'added':
      return 'bg-green-500/10 text-green-300'
    case 'removed':
      return 'bg-red-500/10 text-red-300'
    case 'header':
      return 'bg-blue-500/10 text-blue-300 font-bold'
    default:
      return 'text-gray-400'
  }
}

function getPrefix(type: DiffLine['type']): string {
  switch (type) {
    case 'added':
      return '+'
    case 'removed':
      return '-'
    default:
      return ' '
  }
}

function getLineComments(lineNumber: number): CommentType[] {
  if (!props.diffId) return []
  return getCommentsForLine(props.diffId, lineNumber)
}

function isCommentFormOpen(lineNumber: number): boolean {
  return openCommentLines.value.has(lineNumber)
}

function toggleCommentForm(lineNumber: number): void {
  if (openCommentLines.value.has(lineNumber)) {
    openCommentLines.value.delete(lineNumber)
  } else {
    openCommentLines.value.add(lineNumber)
  }
}

async function handleSaveComment(lineNumber: number, content: string): Promise<void> {
  if (!props.diffId) return

  await addComment({
    diff_id: props.diffId,
    line_number: lineNumber,
    content,
  })

  openCommentLines.value.delete(lineNumber)
  emit('comment-added', lineNumber, content)
}

async function handleDeleteComment(lineNumber: number): Promise<void> {
  if (!props.diffId) return

  const comments = getLineComments(lineNumber)
  for (const comment of comments) {
    await deleteComment(props.diffId, comment.id)
  }

  emit('comment-deleted', lineNumber)
}

function handleCancelComment(lineNumber: number): void {
  openCommentLines.value.delete(lineNumber)
}
</script>

<template>
  <div class="diff-viewer overflow-auto max-h-[600px]">
    <div class="font-mono text-sm">
      <template v-for="(line, index) in parsedLines" :key="index">
        <!-- Diff line -->
        <div
          :class="[
            getLineClass(line.type),
            'flex px-2 py-0.5 whitespace-pre group',
            enableComments && line.lineNumber ? 'hover:bg-rf-bg-light/50 cursor-pointer' : ''
          ]"
          @click="enableComments && line.lineNumber ? toggleCommentForm(line.lineNumber) : null"
        >
          <span class="w-12 text-right text-gray-600 select-none mr-4">
            {{ line.lineNumber || '' }}
          </span>
          <span class="w-4 text-center select-none">
            {{ line.type !== 'header' ? getPrefix(line.type) : '' }}
          </span>
          <span class="flex-1">{{ line.content }}</span>

          <!-- Comment indicator -->
          <span
            v-if="enableComments && line.lineNumber && getLineComments(line.lineNumber).length > 0"
            class="ml-2 text-rf-primary opacity-70 group-hover:opacity-100"
            title="Has comments"
          >
            💬 {{ getLineComments(line.lineNumber).length }}
          </span>

          <!-- Add comment button (on hover) -->
          <button
            v-if="enableComments && line.lineNumber && !isCommentFormOpen(line.lineNumber)"
            class="ml-2 text-gray-600 opacity-0 group-hover:opacity-100 hover:text-rf-primary transition-opacity"
            title="Add comment"
            @click.stop="toggleCommentForm(line.lineNumber)"
          >
            +
          </button>
        </div>

        <!-- Existing comments for this line -->
        <template v-if="enableComments && line.lineNumber">
          <InlineComment
            v-for="comment in getLineComments(line.lineNumber)"
            :key="comment.id"
            :line-number="line.lineNumber"
            :existing-comment="comment.content"
            :author="comment.author"
            :timestamp="comment.created_at"
            @save="(content) => handleSaveComment(line.lineNumber!, content)"
            @delete="handleDeleteComment(line.lineNumber!)"
          />

          <!-- New comment form -->
          <InlineComment
            v-if="isCommentFormOpen(line.lineNumber) && getLineComments(line.lineNumber).length === 0"
            :line-number="line.lineNumber"
            @save="(content) => handleSaveComment(line.lineNumber!, content)"
            @cancel="handleCancelComment(line.lineNumber)"
          />
        </template>
      </template>
    </div>
  </div>
</template>
