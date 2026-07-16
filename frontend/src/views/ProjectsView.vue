<template>
  <div class="topbar">
    <span class="topbar-title">Projects</span>
    <button class="btn btn-primary" @click="showCreate = true">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      New project
    </button>
  </div>

  <div class="page-content">
    <div v-if="loading" style="text-align:center;padding:40px"><span class="spinner"></span></div>
    <div v-else-if="!projects.length" class="empty-state">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
      <p>No projects yet</p>
    </div>
    <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px">
      <div v-for="p in projects" :key="p.id" class="card" style="padding:16px 18px">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
          <div>
            <div style="font-size:14px;font-weight:500;margin-bottom:2px">{{ p.name }}</div>
            <code style="font-size:11px;color:var(--text3);font-family:var(--mono)">{{ p.slug }}</code>
          </div>
          <button v-if="auth.isTeamlead" class="btn btn-sm btn-danger" @click="doDelete(p)">✕</button>
        </div>
        <p v-if="p.description" style="font-size:12px;color:var(--text2);line-height:1.6;margin-bottom:10px">{{ p.description }}</p>
        <div style="font-size:11px;color:var(--text3)">{{ p.member_count }} member{{ p.member_count !== 1 ? 's' : '' }}</div>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal-box">
        <div class="modal-head">
          <h3>New project</h3>
          <button class="btn btn-sm" @click="showCreate = false">✕</button>
        </div>
        <div class="field"><label>Name *</label><input class="input" v-model="form.name" placeholder="Payment Service" /></div>
        <div class="field"><label>Slug *</label><input class="input" v-model="form.slug" placeholder="payment-service" style="font-family:var(--mono)" /></div>
        <div class="field"><label>Description</label><textarea class="input" v-model="form.description" rows="2"></textarea></div>
        <div v-if="err" style="color:var(--red);font-size:12px;margin-bottom:10px">{{ err }}</div>
        <div class="modal-foot">
          <button class="btn" @click="showCreate = false">Cancel</button>
          <button class="btn btn-primary" :disabled="saving" @click="doCreate">
            <span v-if="saving" class="spinner" style="width:12px;height:12px"></span>
            Create
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { projectsApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth    = useAuthStore()
const toast   = useToastStore()
const projects = ref([])
const loading  = ref(true)
const showCreate = ref(false)
const saving  = ref(false)
const err     = ref('')
const form    = reactive({ name: '', slug: '', description: '' })

async function load() {
  loading.value = true
  const { data } = await projectsApi.list()
  projects.value = data.results ?? data
  loading.value  = false
}

async function doCreate() {
  if (!form.name || !form.slug) { err.value = 'Name and slug required'; return }
  saving.value = true; err.value = ''
  try {
    await projectsApi.create(form)
    showCreate.value = false
    toast.success('Project created')
    load()
  } catch (e) {
    err.value = e.response?.data ? Object.values(e.response.data).flat().join(' ') : 'Error'
  } finally { saving.value = false }
}

async function doDelete(p) {
  if (!confirm(`Delete project "${p.name}"?`)) return
  await projectsApi.delete(p.id)
  toast.success('Project deleted')
  load()
}

onMounted(load)
</script>
