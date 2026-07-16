<template>
  <span class="badge" :class="`badge-${status}`">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String })
const labels = {
  open: 'Open', in_progress: 'In Progress', in_review: 'In Review',
  resolved: 'Resolved', closed: 'Closed', wont_fix: "Won't Fix",
}
const label = computed(() => labels[props.status] ?? props.status)
</script>
