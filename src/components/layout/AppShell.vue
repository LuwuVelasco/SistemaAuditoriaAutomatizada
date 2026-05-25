<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/ui/AppIcon.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const showUserMenu = ref(false)

const navItems = [
  { name: 'Inicio',      to: '/inicio',      icon: 'home' },
  { name: 'Auditorías', to: '/auditorias',  icon: 'list' },
  { name: 'Mi perfil',  to: '/perfil',      icon: 'user' }
]

function isActive(to) {
  if (to === '/inicio') return route.path === '/inicio'
  return route.path.startsWith(to)
}

async function logout() {
  showUserMenu.value = false
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">CF</div>
        <div>
          <div class="logo-text">COSFI</div>
          <div class="logo-sub">Auditoría TI · IA</div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="sidebar-section-label">Navegación</div>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item.to) }"
        >
          <AppIcon :name="item.icon" :size="15" class="nav-icon" />
          {{ item.name }}
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="user-card" @click="showUserMenu = !showUserMenu">
          <div class="user-avatar">{{ auth.initials }}</div>
          <div class="user-info">
            <div class="user-name">{{ auth.user?.name }}</div>
            <div class="user-email">{{ auth.user?.email }}</div>
          </div>
          <div class="user-menu-btn">
            <AppIcon name="more-vertical" :size="14" />
          </div>
          <Transition name="fade">
            <div v-if="showUserMenu" class="user-dropdown" @click.stop>
              <RouterLink to="/perfil" class="user-dropdown-item" @click="showUserMenu=false">
                <AppIcon name="user" :size="13" />
                Mi perfil
              </RouterLink>
              <div class="user-dropdown-item danger" @click="logout">
                <AppIcon name="logout" :size="13" />
                Cerrar sesión
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main class="main-area">
      <slot />
    </main>
  </div>
</template>
