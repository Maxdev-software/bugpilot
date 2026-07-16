<template>
  <div class="topbar">
    <span class="topbar-title">Team</span>
  </div>

  <div class="page-content">
    <div v-if="loading" style="text-align:center;padding:40px"><span class="spinner"></span></div>
    <div v-else class="card" style="overflow:hidden">
      <table class="data-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Email</th>
            <th>Role</th>
            <th>Joined</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" style="cursor:default">
            <td>
              <div style="display:flex;align-items:center;gap:8px">
                <div class="avatar-sm">{{ u.username[0].toUpperCase() }}</div>
                <div>
                  <div style="font-size:13px;font-weight:500">{{ u.first_name }} {{ u.last_name }}</div>
                  <div style="font-size:11px;color:var(--text3)">{{ u.username }}</div>
                </div>
              </div>
            </td>
            <td style="font-size:12px;color:var(--text2)">{{ u.email || '—' }}</td>
            <td>
              <span class="badge" :class="roleClass(u.role)">{{ u.role }}</span>
            </td>
            <td style="font-size:11px;color:var(--text3)">{{ fmtDate(u.date_joined) }}</td>
            <td>
              <select
                v-if="auth.isAdmin && u.id !== auth.user?.id"
                class="input" style="width:120px;padding:4px 8px;font-size:12px"
                :value="u.role"
                @change="changeRole(u, $event.target.value)"
              >
                <option value="developer">Developer</option>
                <option value="teamlead">Team Lead</option>
                <option value="admin">Admin</option>
              </select>
              <span v-else style="font-size:11px;color:var(--text3)">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth  = useAuthStore()
const toast = useToastStore()
const users   = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  const { data } = await authApi.users()
  users.value  = data.results ?? data
  loading.value = false
}

async function changeRole(u, role) {
  try {
    await authApi.changeRole(u.id, role)
    u.role = role
    toast.success(`${u.username} is now ${role}`)
  } catch { toast.error('Failed to change role') }
}

function roleClass(r) {
  return { admin: 'badge-critical', teamlead: 'badge-bug', developer: 'badge-info' }[r] ?? ''
}

function fmtDate(s) {
  return new Date(s).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(load)
</script>
