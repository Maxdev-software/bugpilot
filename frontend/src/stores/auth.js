import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user  = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn  = computed(() => !!token.value)
  const isAdmin     = computed(() => user.value?.role === 'admin')
  const isTeamlead  = computed(() => ['admin', 'teamlead'].includes(user.value?.role))
  const isDeveloper = computed(() => !!user.value?.role)

  async function login(credentials) {
    const { data } = await authApi.login(credentials)
    token.value = data.token
    user.value  = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  async function register(payload) {
    const { data } = await authApi.register(payload)
    token.value = data.token
    user.value  = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  async function logout() {
    try { await authApi.logout() } catch {}
    token.value = ''
    user.value  = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function refreshMe() {
    const { data } = await authApi.me()
    user.value = data
    localStorage.setItem('user', JSON.stringify(data))
  }

  return { token, user, isLoggedIn, isAdmin, isTeamlead, isDeveloper, login, register, logout, refreshMe }
})
