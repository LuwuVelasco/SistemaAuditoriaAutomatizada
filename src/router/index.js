import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  { path: '/', redirect: '/inicio' },
  { path: '/inicio', name: 'Dashboard', component: () => import('../views/DashboardView.vue') },
  { path: '/auditorias', name: 'Auditorias', component: () => import('../views/AuditoriasView.vue') },
  { path: '/workspace/:auditId', name: 'Workspace', component: () => import('../views/WorkspaceView.vue') },
  { path: '/workspace/:auditId/hallazgo/:findingId', name: 'FindingDetail', component: () => import('../views/FindingDetailView.vue') },
  { path: '/perfil', name: 'Perfil', component: () => import('../views/ProfileView.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'Login' }
  }
  if (to.name === 'Login' && auth.isAuthenticated) {
    return { name: 'Dashboard' }
  }
})

export default router
