import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/artifacts',
    name: 'artifacts',
    component: () => import('@/views/ArtifactsView.vue'),
    meta: { title: 'Artifacts' },
  },
  {
    path: '/artifacts/:id',
    name: 'artifact-detail',
    component: () => import('@/views/ArtifactDetailView.vue'),
    meta: { title: 'Artifact Detail' },
  },
  {
    path: '/diffs',
    name: 'diffs',
    component: () => import('@/views/DiffsView.vue'),
    meta: { title: 'Diff Review' },
  },
  {
    path: '/diffs/:id',
    name: 'diff-detail',
    component: () => import('@/views/DiffDetailView.vue'),
    meta: { title: 'Diff Review' },
  },
  {
    path: '/approvals',
    name: 'approvals',
    component: () => import('@/views/ApprovalsView.vue'),
    meta: { title: 'Approvals' },
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('@/views/HistoryView.vue'),
    meta: { title: 'History' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: 'Login', guest: true },
  },
  {
    path: '/init',
    name: 'init',
    component: () => import('@/views/InitView.vue'),
    meta: { title: 'Initialize Project' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Update page title
router.beforeEach((to) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - Rice-Factor` : 'Rice-Factor'
})

export default router
