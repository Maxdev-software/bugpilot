<template>
  <div class="topbar">
    <span class="topbar-title">Dashboard</span>
    <span style="font-size:11px;color:var(--text3)">{{ today }}</span>
  </div>
  <div class="page-content">
    <!-- Stats -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">Total tickets</div>
        <div class="stat-value">{{ stats.total ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Open</div>
        <div class="stat-value red">{{ stats.open ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Critical</div>
        <div class="stat-value orange">{{ stats.critical ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">AI analysed</div>
        <div class="stat-value accent">{{ stats.ai_analysed ?? '—' }}</div>
      </div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <!-- Recent critical -->
      <div class="card" style="padding:16px">
        <div style="font-size:12px;font-weight:600;color:var(--text2);margin-bottom:12px;display:flex;align-items:center;gap:6px">
          <span style="color:var(--red)">●</span> Critical &amp; open
        </div>
        <div v-if="loadingTickets" style="color:var(--text3);font-size:12px">Loading…</div>
        <div v-else-if="!criticalTickets.length" class="empty-state" style="padding:20px 0">
          <p>No critical issues 🎉</p>
        </div>
        <div v-else>
          <div
            v-for="t in criticalTickets" :key="t.id"
            style="padding:8px 0;border-bottom:1px solid var(--border);cursor:pointer"
            @click="$router.push('/tickets/' + t.id)"
          >
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">
              <span class="display-id">{{ t.display_id }}</span>
              <PriorityBadge :priority="t.priority" />
            </div>
            <div style="font-size:12px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{ t.title }}</div>
            <div style="font-size:11px;color:var(--text3);margin-top:2px">{{ t.assignee?.username ?? 'Unassigned' }}</div>
          </div>
        </div>
      </div>

      <!-- Priority breakdown -->
      <div class="card" style="padding:16px">
        <div style="font-size:12px;font-weight:600;color:var(--text2);margin-bottom:14px">Priority breakdown</div>
        <div v-for="row in breakdown" :key="row.label" style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
            <span :style="{color: row.color}">{{ row.label }}</span>
            <span style="font-family:var(--mono);color:var(--text2)">{{ row.val }}</span>
          </div>
          <div style="height:5px;background:var(--bg4);border-radius:3px;overflow:hidden">
            <div :style="{ width: barWidth(row.val) + '%', background: row.color, height: '100%', borderRadius: '3px', transition: 'width 0.4s' }"></div>
          </div>
        </div>

        <div style="margin-top:16px;border-top:1px solid var(--border);padding-top:14px">
          <div style="font-size:12px;font-weight:600;color:var(--text2);margin-bottom:12px">Status overview</div>
          <div v-for="row in statusBreakdown" :key="row.label" style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--border);font-size:12px">
            <span style="color:var(--text2)">{{ row.label }}</span>
            <span style="font-family:var(--mono)">{{ row.val }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi, ticketsApi } from '@/api'
import PriorityBadge from '@/components/tickets/PriorityBadge.vue'

const stats = ref({})
const criticalTickets = ref([])
const loadingTickets  = ref(true)

const today = new Date().toLocaleDateString('en-US', { weekday:'long', year:'numeric', month:'long', day:'numeric' })

const breakdown = computed(() => [
  { label: 'Critical', val: stats.value.critical ?? 0, color: 'var(--red)' },
  { label: 'Bug',      val: stats.value.bug      ?? 0, color: 'var(--orange)' },
  { label: 'Warning',  val: stats.value.warning  ?? 0, color: 'var(--blue)' },
])

const statusBreakdown = computed(() => [
  { label: 'Open',        val: stats.value.open        ?? 0 },
  { label: 'In Progress', val: stats.value.in_progress ?? 0 },
  { label: 'Resolved',    val: stats.value.resolved    ?? 0 },
])

const maxVal = computed(() => Math.max(stats.value.critical ?? 0, stats.value.bug ?? 0, stats.value.warning ?? 0, 1))
function barWidth(v) { return Math.round((v / maxVal.value) * 100) }

onMounted(async () => {
  const [s, t] = await Promise.all([
    statsApi.get(),
    ticketsApi.list({ priority: 'critical', status: 'open', page_size: 5 }),
  ])
  stats.value          = s.data
  criticalTickets.value = t.data.results ?? []
  loadingTickets.value  = false
})
</script>
