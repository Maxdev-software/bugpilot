<template>
  <span class="badge" :class="`badge-${priority}`">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ priority: String })
const labels = { critical: 'CRITICAL', bug: 'BUG', warning: 'WARNING', info: 'INFO' }
const label  = computed(() => labels[props.priority] ?? props.priority?.toUpperCase())
</script>
