<template>
  <div v-if="loading" style="padding:60px;text-align:center"><span class="spinner" style="width:20px;height:20px"></span></div>

  <template v-else-if="ticket">
    <div class="topbar">
      <button class="btn btn-sm" style="margin-right:6px" @click="$router.back()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <span class="topbar-title">
        <span class="display-id" style="font-size:13px;margin-right:8px">{{ ticket.display_id }}</span>
        {{ ticket.title }}
      </span>
      <button v-if="auth.isTeamlead" class="btn btn-sm" :disabled="reanalysing" @click="doReanalyse" title="Re-run AI analysis">
        <span v-if="reanalysing" class="spinner" style="width:11px;height:11px"></span>
        <span v-else>✦</span>
        Reanalyse
      </button>
      <button v-if="auth.isTeamlead" class="btn btn-sm btn-danger" @click="doDelete">Delete</button>
    </div>

    <div class="page-content" style="display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:start">
      <!-- Left column -->
      <div>
        <!-- Header -->
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap">
          <PriorityBadge :priority="ticket.priority" />
          <StatusBadge   :status="ticket.status" />
          <span style="font-size:11px;color:var(--text3)">opened {{ fmtDate(ticket.created_at) }}</span>
          <span v-if="ticket.reporter" style="font-size:11px;color:var(--text3)">by {{ ticket.reporter.username }}</span>
        </div>

        <div v-if="ticket.description" class="card" style="padding:14px 16px;margin-bottom:12px;font-size:13px;color:var(--text2);line-height:1.7;white-space:pre-wrap">{{ ticket.description }}</div>

        <div v-if="ticket.ai_summary" class="ai-block">
          <div class="ai-block-head">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            AI Analysis
            <span v-if="ticket.ai_model_used" style="margin-left:auto;font-size:10px;color:var(--text3);text-transform:none;letter-spacing:0;font-weight:400">{{ ticket.ai_model_used }}</span>
          </div>
          <div class="ai-section">
            <div class="ai-section-label">Summary</div>
            <div class="ai-section-body">{{ ticket.ai_summary }}</div>
          </div>
          <div v-if="ticket.ai_root_cause" class="ai-section">
            <div class="ai-section-label">Root cause</div>
            <div class="ai-section-body">{{ ticket.ai_root_cause }}</div>
          </div>
          <div v-if="ticket.ai_fix_suggestion" class="ai-section">
            <div class="ai-section-label">Fix suggestion</div>
            <div class="ai-fix">{{ ticket.ai_fix_suggestion }}</div>
          </div>
        </div>
        <div v-else class="card" style="padding:14px 16px;margin-bottom:12px;color:var(--text3);font-size:12px">
          No AI analysis yet. {{ auth.isTeamlead ? 'Use "Reanalyse" to trigger it.' : '' }}
        </div>

        <div v-if="ticket.ingest_log?.stacktrace" style="margin-bottom:12px">
          <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px">Stack trace</div>
          <pre style="background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius-lg);padding:12px 14px;font-size:11px;font-family:var(--mono);color:var(--text2);overflow-x:auto;white-space:pre-wrap;word-break:break-all;max-height:220px;overflow-y:auto">{{ ticket.ingest_log.stacktrace }}</pre>
        </div>

        <div style="font-size:12px;font-weight:600;color:var(--text2);margin-bottom:10px;margin-top:4px">
          Comments ({{ ticket.comments?.length ?? 0 }})
        </div>
        <div v-for="c in ticket.comments" :key="c.id" style="margin-bottom:10px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
            <div class="avatar-sm" style="width:22px;height:22px;font-size:10px">{{ c.author?.username?.[0]?.toUpperCase() }}</div>
            <span style="font-size:12px;font-weight:500">{{ c.author?.username }}</span>
            <span style="font-size:11px;color:var(--text3)">{{ fmtDate(c.created_at) }}</span>
            <button
              v-if="auth.user?.id === c.author?.id || auth.isTeamlead"
              class="btn btn-sm" style="margin-left:auto;padding:2px 6px;font-size:10px"
              @click="deleteComment(c.id)"
            >✕</button>
          </div>
          <div style="background:var(--bg2);border:1px solid var(--border);border-radius:var(--radius);padding:10px 12px;font-size:13px;color:var(--text2);line-height:1.6">{{ c.body }}</div>
        </div>

        <div style="margin-top:12px">
          <textarea class="input" v-model="commentBody" rows="3" placeholder="Add a comment…"></textarea>
          <button class="btn btn-primary" style="margin-top:8px" :disabled="!commentBody.trim() || postingComment" @click="addComment">
            <span v-if="postingComment" class="spinner" style="width:11px;height:11px"></span>
            Post comment
          </button>
        </div>
      </div>

      <div style="display:flex;flex-direction:column;gap:10px">
        <!-- Status -->
        <div class="card" style="padding:14px 16px">
          <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Status</div>
          <select class="input" :value="ticket.status" @change="changeStatus($event.target.value)" :disabled="!canEdit">
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="in_review">In Review</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="wont_fix">Won't Fix</option>
          </select>
        </div>

        <div class="card" style="padding:14px 16px">
          <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Priority</div>
          <select class="input" :value="ticket.priority" @change="changePriority($event.target.value)" :disabled="!auth.isTeamlead">
            <option value="critical">Critical</option>
            <option value="bug">Bug</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
        </div>

        <div class="card" style="padding:14px 16px">
          <div style="font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px">Assignee</div>
          <select class="input" :value="ticket.assignee?.id ?? ''" @change="changeAssignee($event.target.value)" :disabled="!auth.isTeamlead">
            <option value="">— Unassigned —</option>
            <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}</option>
          </select>
        </div>

        <div class="card" style="padding:14px 16px;font-size:12px">
          <div style="display:flex;flex-direction:column;gap:7px;color:var(--text2)">
            <div v-if="ticket.project"><span style="color:var(--text3)">Project</span> &nbsp; {{ ticket.project }}</div>
            <div v-if="ticket.ingest_log"><span style="color:var(--text3)">App</span> &nbsp; <span style="font-family:var(--mono)">{{ ticket.ingest_log.app_name }}</span></div>
            <div v-if="ticket.ingest_log"><span style="color:var(--text3)">Env</span> &nbsp; {{ ticket.ingest_log.environment }}</div>
            <div><span style="color:var(--text3)">Created</span> &nbsp; {{ fmtDate(ticket.created_at) }}</div>
            <div v-if="ticket.resolved_at"><span style="color:var(--text3)">Resolved</span> &nbsp; {{ fmtDate(ticket.resolved_at) }}</div>
            <div v-if="ticket.ai_analysed_at"><span style="color:var(--accent2)">✦ AI analysed</span> &nbsp; {{ fmtDate(ticket.ai_analysed_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </template>

  <div v-else class="empty-state" style="padding:60px">
    <p>Ticket not found.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ticketsApi, authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import PriorityBadge from '@/components/tickets/PriorityBadge.vue'
import StatusBadge from '@/components/tickets/StatusBadge.vue'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()
const toast  = useToastStore()

const ticket     = ref(null)
const loading    = ref(true)
const reanalysing = ref(false)
const users      = ref([])
const commentBody    = ref('')
const postingComment = ref(false)

const canEdit = computed(() => auth.isTeamlead || ticket.value?.assignee?.id === auth.user?.id)

function fmtDate(s) {
  if (!s) return '—'
  return new Date(s).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function load() {
  loading.value = true
  try {
    const { data } = await ticketsApi.get(route.params.id)
    ticket.value = data
  } catch { ticket.value = null }
  loading.value = false
}

async function changeStatus(val) {
  await ticketsApi.changeStatus(ticket.value.id, val)
  ticket.value.status = val
  toast.success('Status updated')
}

async function changePriority(val) {
  await ticketsApi.update(ticket.value.id, { priority: val })
  ticket.value.priority = val
  toast.success('Priority updated')
}

async function changeAssignee(val) {
  await ticketsApi.assign(ticket.value.id, val || null)
  await load()
  toast.success('Assignee updated')
}

async function doReanalyse() {
  reanalysing.value = true
  try {
    await ticketsApi.reanalyse(ticket.value.id)
    toast.success('Reanalysis queued — refresh in a few seconds')
  } catch { toast.error('Failed to queue reanalysis') }
  reanalysing.value = false
}

async function doDelete() {
  if (!confirm(`Delete ${ticket.value.display_id}?`)) return
  await ticketsApi.delete(ticket.value.id)
  toast.success('Ticket deleted')
  router.push('/tickets')
}

async function addComment() {
  if (!commentBody.value.trim()) return
  postingComment.value = true
  try {
    await ticketsApi.comments.create(ticket.value.id, commentBody.value)
    commentBody.value = ''
    await load()
  } catch { toast.error('Failed to post comment') }
  postingComment.value = false
}

async function deleteComment(cid) {
  if (!confirm('Delete comment?')) return
  await ticketsApi.comments.delete(ticket.value.id, cid)
  await load()
}

onMounted(async () => {
  load()
  try { const { data } = await authApi.users(); users.value = data.results ?? data } catch {}
})
</script>
