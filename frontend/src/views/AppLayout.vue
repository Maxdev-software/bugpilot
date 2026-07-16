<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-icon">🐛</div>
        <div>
          <div class="logo-text">BugPilot</div>
          <div class="logo-sub">AI error analysis</div>
        </div>
      </div>

      <div class="nav-section">Main</div>
      <router-link
        v-for="item in navItems" :key="item.to"
        :to="item.to"
        class="nav-item"
        active-class="active"
      >
        <component :is="item.icon" :size="15" />
        <span>{{ item.label }}</span>
        <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
      </router-link>

      <div v-if="auth.isTeamlead" class="nav-section">Manage</div>
      <router-link v-if="auth.isTeamlead" to="/projects" class="nav-item" active-class="active">
        <IconFolder :size="15" /><span>Projects</span>
      </router-link>
      <router-link v-if="auth.isTeamlead" to="/ingest" class="nav-item" active-class="active">
        <IconWebhook :size="15" /><span>Ingest logs</span>
      </router-link>
      <router-link v-if="auth.isAdmin" to="/team" class="nav-item" active-class="active">
        <IconUsers :size="15" /><span>Team</span>
      </router-link>

      <div class="sidebar-footer">
        <div class="avatar-sm">{{ initials }}</div>
        <div class="user-info">
          <div class="user-name">{{ auth.user?.username }}</div>
          <div class="user-role">{{ auth.user?.role }}</div>
        </div>
        <button class="btn btn-sm" style="padding:3px 7px" @click="doLogout" title="Logout">
          <IconLogout :size="13" />
        </button>
      </div>
    </aside>

    <div class="main-area">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const IconHome    = { template: `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`, props:['size'] }
const IconTickets = { template: `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2a2 2 0 0 0 0-4z"/></svg>`, props:['size'] }
const IconFolder  = { template: `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`, props:['size'] }
const IconWebhook = { template: `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c.01-.7.2-1.4.57-2"/><path d="m6 17 3.13-5.78c.53-.97.1-2.18-.5-3.1a4 4 0 1 1 6.89-4.06"/><path d="m12 6 3.13 5.73C15.66 12.7 16.9 13 18 13a4 4 0 0 1 0 8"/></svg>`, props:['size'] }
const IconUsers   = { template: `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`, props:['size'] }
const IconLogout  = { template: `<svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`, props:['size'] }

const auth   = useAuthStore()
const router = useRouter()
const toast  = useToastStore()

const initials = computed(() => {
  const u = auth.user
  if (!u) return '?'
  return ((u.first_name?.[0] || '') + (u.last_name?.[0] || '') || u.username[0]).toUpperCase()
})

const navItems = computed(() => [
  { to: '/dashboard', label: 'Dashboard', icon: IconHome },
  { to: '/tickets',   label: 'Tickets',   icon: IconTickets },
])

async function doLogout() {
  await auth.logout()
  router.push('/login')
  toast.success('Logged out')
}
</script>
