<template>
  <div class="topbar">
    <span class="topbar-title">Tickets</span>
    <button class="btn btn-primary" @click="showCreate = true">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      New ticket
    </button>
  </div>

  <div class="page-content">
    <div class="filter-row">
      <input class="search-input" v-model="search" placeholder="Search tickets…" @input="debouncedFetch" />
      <button
        v-for="p in priorities" :key="p.v"
        class="filter-chip" :class="{ active: filter.priority === p.v }"
        @click="toggleFilter('priority', p.v)"
      >{{ p.l }}</button>
      <div style="width:1px;height:16px;background:var(--border);margin:0 2px"></div>
      <button
        v-for="s in statuses" :key="s.v"
        class="filter-chip" :class="{ active: filter.status === s.v }"
        @click="toggleFilter('status', s.v)"
      >{{ s.l }}</button>
    </div>

    <div class="card" style="overflow:hidden">
      <div v-if="loading" style="padding:40px;text-align:center">
        <span class="spinner"></span>
      </div>
      <div v-else-if="!tickets.length" class="empty-state">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <p>No tickets found</p>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Assignee</th>
            <th>AI</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tickets" :key="t.id" @click="$router.push('/tickets/' + t.id)">
            <td><span class="display-id">{{ t.display_id }}</span></td>
            <td style="max-width:320px">
              <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:13px">{{ t.title }}</div>
              <div v-if="t.ai_summary" style="font-size:11px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px">{{ t.ai_summary }}</div>
            </td>
            <td><PriorityBadge :priority="t.priority" /></td>
            <td><StatusBadge :status="t.status" /></td>
            <td style="font-size:12px;color:var(--text2)">{{ t.assignee?.username ?? '—' }}</td>
            <td>
              <span v-if="t.ai_summary" style="color:var(--accent2);font-size:11px" title="AI analysed">✦</span>
              <span v-else style="color:var(--text3);font-size:11px">—</span>
            </td>
            <td style="font-size:11px;color:var(--text3);white-space:nowrap">{{ fmtDate(t.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="count > pageSize" style="display:flex;align-items:center;gap:8px;margin-top:12px;justify-content:flex-end">
      <span style="font-size:12px;color:var(--text3)">{{ count }} total</span>
      <button class="btn btn-sm" :disabled="page <= 1" @click="page--;fetch()">← Prev</button>
      <span style="font-size:12px;color:var(--text2)">{{ page }}</span>
      <button class="btn btn-sm" :disabled="page * pageSize >= count" @click="page++;fetch()">Next →</button>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal-box">
        <div class="modal-head">
          <h3>New ticket</h3>
          <button class="btn btn-sm" @click="showCreate = false">✕</button>
        </div>
        <div class="field">
          <label>Title *</label>
          <input class="input" v-model="newTicket.title" placeholder="Short description of the bug" />
        </div>
        <div class="field">
          <label>Description</label>
          <textarea class="input" v-model="newTicket.description" rows="3" placeholder="What happened?"></textarea>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="field">
            <label>Priority</label>
            <select class="input" v-model="newTicket.priority">
              <option value="critical">Critical</option>
              <option value="bug">Bug</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div class="field">
            <label>Assignee</label>
            <select class="input" v-model="newTicket.assignee">
              <option :value="null">— Unassigned —</option>
              <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}</option>
            </select>
          </div>
        </div>
        <div v-if="createError" style="color:var(--red);font-size:12px;margin-bottom:10px">{{ createError }}</div>
        <div class="modal-foot">
          <button class="btn" @click="showCreate = false">Cancel</button>
          <button class="btn btn-primary" :disabled="creating" @click="doCreate">
            <span v-if="creating" class="spinner" style="width:12px;height:12px"></span>
            Create ticket
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketsApi, authApi } from '@/api'
import { useToastStore } from '@/stores/toast'
import PriorityBadge from '@/components/tickets/PriorityBadge.vue'
import StatusBadge from '@/components/tickets/StatusBadge.vue'

const router = useRouter()
const toast  = useToastStore()

const tickets  = ref([])
const count    = ref(0)
const loading  = ref(true)
const page     = ref(1)
const pageSize = 20
const search   = ref('')
const filter   = reactive({ priority: '', status: '' })

const priorities = [
  { v: 'critical', l: 'Critical' },
  { v: 'bug',      l: 'Bug' },
  { v: 'warning',  l: 'Warning' },
]
const statuses = [
  { v: 'open',        l: 'Open' },
  { v: 'in_progress', l: 'In Progress' },
  { v: 'resolved',    l: 'Resolved' },
]

function toggleFilter(key, val) {
  filter[key] = filter[key] === val ? '' : val
  page.value = 1
  fetch()
}

async function fetch() {
  loading.value = true
  const params = { page: page.value }
  if (filter.priority) params.priority = filter.priority
  if (filter.status)   params.status   = filter.status
  if (search.value)    params.search   = search.value
  const { data } = await ticketsApi.list(params)
  tickets.value = data.results ?? []
  count.value   = data.count   ?? 0
  loading.value = false
}

let debounceTimer
function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1; fetch() }, 300)
}

function fmtDate(s) {
  if (!s) return '—'
  return new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const showCreate  = ref(false)
const creating    = ref(false)
const createError = ref('')
const users       = ref([])
const newTicket   = reactive({ title: '', description: '', priority: 'bug', assignee: null })

async function doCreate() {
  if (!newTicket.title.trim()) { createError.value = 'Title required'; return }
  creating.value = true; createError.value = ''
  try {
    const { data } = await ticketsApi.create(newTicket)
    showCreate.value = false
    toast.success(`Ticket ${data.display_id} created`)
    router.push('/tickets/' + data.id)
  } catch (e) {
    createError.value = e.response?.data ? Object.values(e.response.data).flat().join(' ') : 'Failed'
  } finally { creating.value = false }
}

onMounted(async () => {
  fetch()
  try { const { data } = await authApi.users(); users.value = data.results ?? data } catch {}
})
</script>
