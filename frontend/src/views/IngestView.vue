<template>
  <div class="topbar">
    <span class="topbar-title">Ingest logs</span>
  </div>

  <div class="page-content" style="display:grid;grid-template-columns:380px 1fr;gap:16px;align-items:start">
    <!-- Sender panel -->
    <div class="card" style="padding:18px 20px">
      <div style="font-size:13px;font-weight:500;margin-bottom:4px">Send test log</div>
      <div style="font-size:12px;color:var(--text3);margin-bottom:16px">Simulates an external app POSTing a crash log</div>

      <div class="field">
        <label>X-Ingest-Token</label>
        <input class="input" v-model="token" placeholder="ingest-secret-token-change-me" style="font-family:var(--mono);font-size:11px" />
      </div>
      <div class="field">
        <label>App name</label>
        <input class="input" v-model="form.app_name" placeholder="payment-service" />
      </div>
      <div class="field">
        <label>Environment</label>
        <select class="input" v-model="form.environment">
          <option>production</option>
          <option>staging</option>
          <option>development</option>
        </select>
      </div>
      <div class="field">
        <label>Level</label>
        <select class="input" v-model="form.level">
          <option>CRITICAL</option>
          <option>ERROR</option>
          <option>WARNING</option>
          <option>INFO</option>
        </select>
      </div>
      <div class="field">
        <label>Message</label>
        <input class="input" v-model="form.message" placeholder="Exception: No API key provided" />
      </div>
      <div class="field">
        <label>Stack trace</label>
        <textarea class="input" v-model="form.stacktrace" rows="7" placeholder="Traceback (most recent call last):&#10;  File…"></textarea>
      </div>

      <!-- Quick fill presets -->
      <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px">
        <button class="btn btn-sm" v-for="p in presets" :key="p.label" @click="applyPreset(p)">{{ p.label }}</button>
      </div>

      <div v-if="result" style="padding:10px 12px;border-radius:var(--radius);font-size:12px;margin-bottom:12px"
        :style="result.ok ? 'background:var(--green-bg);border:1px solid var(--green);color:var(--green)' : 'background:var(--red-bg);border:1px solid var(--red);color:var(--red)'">
        {{ result.msg }}
      </div>

      <button class="btn btn-primary" style="width:100%;justify-content:center" :disabled="sending" @click="send">
        <span v-if="sending" class="spinner" style="width:12px;height:12px"></span>
        {{ sending ? 'Sending…' : 'Send log' }}
      </button>

      <!-- API reference -->
      <details style="margin-top:16px">
        <summary style="font-size:11px;color:var(--text3);cursor:pointer;user-select:none">API reference</summary>
        <pre style="background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius);padding:10px;font-size:10px;font-family:var(--mono);color:var(--text2);margin-top:8px;overflow-x:auto;white-space:pre">POST /api/v1/ingest/log/
Header: X-Ingest-Token: &lt;token&gt;

{
  "app_name": "my-service",
  "environment": "production",
  "level": "ERROR",
  "message": "...",
  "stacktrace": "...",
  "project_slug": "my-project"
}

→ 202 { log_id, task_id, status }</pre>
      </details>
    </div>

    <!-- Log list -->
    <div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div style="font-size:13px;font-weight:500;color:var(--text2)">Recent ingest logs</div>
        <button class="btn btn-sm" @click="loadLogs">↻ Refresh</button>
      </div>
      <div class="card" style="overflow:hidden">
        <div v-if="logsLoading" style="padding:30px;text-align:center"><span class="spinner"></span></div>
        <div v-else-if="!logs.length" class="empty-state" style="padding:24px 0">
          <p>No logs yet. Send one →</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>App</th>
              <th>Level</th>
              <th>Message</th>
              <th>Status</th>
              <th>Received</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in logs" :key="l.id" style="cursor:default">
              <td><code style="font-size:10px;color:var(--text3);font-family:var(--mono)">{{ l.id.slice(0,8) }}…</code></td>
              <td style="font-family:var(--mono);font-size:11px">{{ l.app_name }}</td>
              <td><span :class="`level-${l.level}`" style="font-size:11px;font-weight:600;font-family:var(--mono)">{{ l.level }}</span></td>
              <td style="max-width:260px"><div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px">{{ l.message }}</div></td>
              <td>
                <span class="badge" :class="statusClass(l.processing_status)">{{ l.processing_status }}</span>
              </td>
              <td style="font-size:11px;color:var(--text3);white-space:nowrap">{{ fmtDate(l.received_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ingestApi } from '@/api'
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const token = ref('ingest-secret-token-change-me')
const sending = ref(false)
const result  = ref(null)
const logs    = ref([])
const logsLoading = ref(true)

const form = reactive({
  app_name: 'payment-service',
  environment: 'production',
  level: 'ERROR',
  message: '',
  stacktrace: '',
})

const presets = [
  {
    label: 'NullPointer',
    app_name: 'auth-service', environment: 'production', level: 'CRITICAL',
    message: 'NullPointerException in UserService.authenticate()',
    stacktrace: `java.lang.NullPointerException
  at com.app.UserService.authenticate(UserService.java:87)
  at com.app.AuthController.login(AuthController.java:43)
  at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)`,
  },
  {
    label: 'Redis timeout',
    app_name: 'api-gateway', environment: 'production', level: 'ERROR',
    message: 'redis.exceptions.TimeoutError: Timeout connecting to server',
    stacktrace: `Traceback (most recent call last):
  File "/app/gateway/cache.py", line 31, in get
    return self.client.get(key)
  File "/env/lib/redis/client.py", line 892, in execute_command
    return self.retry.call_with_retry(...)
redis.exceptions.TimeoutError: Timeout connecting to server`,
  },
  {
    label: 'OOM',
    app_name: 'realtime-svc', environment: 'production', level: 'CRITICAL',
    message: 'FATAL: JavaScript heap out of memory',
    stacktrace: `FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed - JavaScript heap out of memory
 1: 0xb7c9e0 node::Abort() [node]
 2: 0xa9455e node::FatalError(char const*, char const*) [node]
 3: 0xd74f8e v8::Utils::ReportOOMFailure(...)
    at ws/handler.js:204`,
  },
]

function applyPreset(p) {
  form.app_name    = p.app_name
  form.environment = p.environment
  form.level       = p.level
  form.message     = p.message
  form.stacktrace  = p.stacktrace
}

async function send() {
  if (!form.message) { toast.error('Message required'); return }
  sending.value = true; result.value = null
  try {
    const { data } = await ingestApi.send(form, token.value)
    result.value = { ok: true, msg: `✓ Log ${data.log_id.slice(0,8)}… queued (task ${data.task_id.slice(0,8)}…)` }
    toast.success('Log received, AI analysis queued')
    setTimeout(loadLogs, 1500)
  } catch (e) {
    const msg = e.response?.status === 403 ? 'Invalid ingest token' : (e.response?.data?.detail ?? 'Send failed')
    result.value = { ok: false, msg }
    toast.error(msg)
  } finally { sending.value = false }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    const { data } = await ingestApi.logs()
    logs.value = data.results ?? data
  } catch {}
  logsLoading.value = false
}

function statusClass(s) {
  return { pending: 'badge-warning', processing: 'badge-info', done: 'badge-resolved', failed: 'badge-critical' }[s] ?? ''
}

function fmtDate(s) {
  return new Date(s).toLocaleString('en-US', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' })
}

onMounted(loadLogs)
</script>
