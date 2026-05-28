import { createRouter, createWebHistory } from 'vue-router'
import { watch } from 'vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'Welcome', component: () => import('../views/WelcomeView.vue'), meta: { public: true } },
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
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

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Esperar a que Firebase inicialice antes de verificar sesión
  if (auth.loading) {
    await new Promise(resolve => {
      const stop = watch(() => auth.loading, (loading) => {
        if (!loading) { stop(); resolve() }
      })
    })
  }

  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'Welcome' }
  }
  if ((to.name === 'Login' || to.name === 'Welcome') && auth.isAuthenticated) {
    return { name: 'Dashboard' }
  }
})

export default router
