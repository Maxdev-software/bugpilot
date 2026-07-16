<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div style="font-size:32px;margin-bottom:8px">🐛</div>
        <h1>BugPilot</h1>
        <p>AI-powered bug tracker</p>
      </div>

      <div class="auth-tabs">
        <div class="auth-tab" :class="{ active: tab === 'login' }" @click="tab = 'login'">Sign in</div>
        <div class="auth-tab" :class="{ active: tab === 'register' }" @click="tab = 'register'">Register</div>
      </div>

      <form v-if="tab === 'login'" @submit.prevent="doLogin">
        <div class="field">
          <label>Username</label>
          <input class="input" v-model="form.username" placeholder="admin" autocomplete="username" required />
        </div>
        <div class="field">
          <label>Password</label>
          <input class="input" type="password" v-model="form.password" placeholder="••••••••" autocomplete="current-password" required />
        </div>
        <div v-if="error" style="color:var(--red);font-size:12px;margin-bottom:12px">{{ error }}</div>
        <button class="btn btn-primary" style="width:100%;justify-content:center" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:12px;height:12px"></span>
          <span>{{ loading ? 'Signing in…' : 'Sign in' }}</span>
        </button>
      </form>

      <form v-else @submit.prevent="doRegister">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div class="field">
            <label>First name</label>
            <input class="input" v-model="reg.first_name" placeholder="Alex" />
          </div>
          <div class="field">
            <label>Last name</label>
            <input class="input" v-model="reg.last_name" placeholder="Smith" />
          </div>
        </div>
        <div class="field">
          <label>Username</label>
          <input class="input" v-model="reg.username" placeholder="alex" required />
        </div>
        <div class="field">
          <label>Email</label>
          <input class="input" type="email" v-model="reg.email" placeholder="alex@example.com" />
        </div>
        <div class="field">
          <label>Role</label>
          <select class="input" v-model="reg.role">
            <option value="developer">Developer</option>
            <option value="teamlead">Team Lead</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div class="field">
          <label>Password</label>
          <input class="input" type="password" v-model="reg.password" placeholder="min 8 chars" required />
        </div>
        <div class="field">
          <label>Confirm password</label>
          <input class="input" type="password" v-model="reg.password_confirm" placeholder="repeat password" required />
        </div>
        <div v-if="error" style="color:var(--red);font-size:12px;margin-bottom:12px">{{ error }}</div>
        <button class="btn btn-primary" style="width:100%;justify-content:center" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:12px;height:12px"></span>
          <span>{{ loading ? 'Creating…' : 'Create account' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth   = useAuthStore()
const router = useRouter()

const tab   = ref('login')
const loading = ref(false)
const error   = ref('')

const form = reactive({ username: '', password: '' })
const reg  = reactive({ username: '', email: '', first_name: '', last_name: '', password: '', password_confirm: '', role: 'developer' })

async function doLogin() {
  error.value = ''; loading.value = true
  try {
    await auth.login(form)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.non_field_errors?.[0] || 'Invalid credentials'
  } finally { loading.value = false }
}

async function doRegister() {
  error.value = ''; loading.value = true
  try {
    await auth.register(reg)
    router.push('/dashboard')
  } catch (e) {
    const d = e.response?.data
    error.value = d ? Object.values(d).flat().join(' ') : 'Registration failed'
  } finally { loading.value = false }
}
</script>
