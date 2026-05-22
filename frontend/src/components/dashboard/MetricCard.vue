<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  label: string
  value: string | number
  tone: 'teal' | 'blue' | 'indigo' | 'amber' | 'purple' | 'green'
  icon: Component
}>()
</script>

<template>
  <article :class="['gm-card', 'gm-metric-card', `is-${tone}`]">
    <div class="gm-metric-icon">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div>
      <span>{{ label }}</span>
      <strong>{{ value }}</strong>
    </div>
  </article>
</template>
