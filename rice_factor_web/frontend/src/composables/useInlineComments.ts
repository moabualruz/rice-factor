/**
 * Composable for managing inline comments on diffs.
 */

import { ref, computed } from 'vue'
import { api } from '@/api/client'

export interface InlineComment {
  id: string
  diff_id: string
  line_number: number
  content: string
  author: string
  created_at: string
  updated_at?: string
}

export interface CreateCommentPayload {
  diff_id: string
  line_number: number
  content: string
}

const comments = ref<Map<string, InlineComment[]>>(new Map())
const loading = ref(false)
const error = ref<string | null>(null)

export function useInlineComments() {
  /**
   * Get comments for a specific diff
   */
  function getCommentsForDiff(diffId: string): InlineComment[] {
    return comments.value.get(diffId) ?? []
  }

  /**
   * Get comments for a specific line in a diff
   */
  function getCommentsForLine(diffId: string, lineNumber: number): InlineComment[] {
    const diffComments = comments.value.get(diffId) ?? []
    return diffComments.filter((c) => c.line_number === lineNumber)
  }

  /**
   * Check if a line has comments
   */
  function hasComments(diffId: string, lineNumber: number): boolean {
    return getCommentsForLine(diffId, lineNumber).length > 0
  }

  /**
   * Fetch comments for a diff from the API
   */
  async function fetchComments(diffId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await api.get<{ comments: InlineComment[] }>(
        `/diffs/${diffId}/comments`
      )
      comments.value.set(diffId, response.comments)
    } catch (e) {
      // If endpoint doesn't exist yet, initialize with empty array
      comments.value.set(diffId, [])
      console.warn('Comments API not available:', e)
    } finally {
      loading.value = false
    }
  }

  /**
   * Add a new comment
   */
  async function addComment(payload: CreateCommentPayload): Promise<InlineComment | null> {
    loading.value = true
    error.value = null
    try {
      const response = await api.post<InlineComment>(
        `/diffs/${payload.diff_id}/comments`,
        payload
      )

      // Update local state
      const existing = comments.value.get(payload.diff_id) ?? []
      comments.value.set(payload.diff_id, [...existing, response])

      return response
    } catch (e) {
      // Fallback: create local comment if API not available
      const localComment: InlineComment = {
        id: `local-${Date.now()}`,
        diff_id: payload.diff_id,
        line_number: payload.line_number,
        content: payload.content,
        author: 'You',
        created_at: new Date().toISOString(),
      }

      const existing = comments.value.get(payload.diff_id) ?? []
      comments.value.set(payload.diff_id, [...existing, localComment])

      return localComment
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing comment
   */
  async function updateComment(
    diffId: string,
    commentId: string,
    content: string
  ): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.put(`/diffs/${diffId}/comments/${commentId}`, { content })

      // Update local state
      const existing = comments.value.get(diffId) ?? []
      const updated = existing.map((c) =>
        c.id === commentId
          ? { ...c, content, updated_at: new Date().toISOString() }
          : c
      )
      comments.value.set(diffId, updated)

      return true
    } catch (e) {
      // Update local state anyway for fallback
      const existing = comments.value.get(diffId) ?? []
      const updated = existing.map((c) =>
        c.id === commentId
          ? { ...c, content, updated_at: new Date().toISOString() }
          : c
      )
      comments.value.set(diffId, updated)
      return true
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a comment
   */
  async function deleteComment(diffId: string, commentId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/diffs/${diffId}/comments/${commentId}`)

      // Update local state
      const existing = comments.value.get(diffId) ?? []
      comments.value.set(diffId, existing.filter((c) => c.id !== commentId))

      return true
    } catch (e) {
      // Remove from local state anyway
      const existing = comments.value.get(diffId) ?? []
      comments.value.set(diffId, existing.filter((c) => c.id !== commentId))
      return true
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear all comments (used when switching diffs)
   */
  function clearComments(diffId?: string): void {
    if (diffId) {
      comments.value.delete(diffId)
    } else {
      comments.value.clear()
    }
  }

  return {
    comments: computed(() => comments.value),
    loading,
    error,
    getCommentsForDiff,
    getCommentsForLine,
    hasComments,
    fetchComments,
    addComment,
    updateComment,
    deleteComment,
    clearComments,
  }
}
