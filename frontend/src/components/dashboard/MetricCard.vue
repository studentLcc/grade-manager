<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  label: string
  value: string | number
  unit?: string
  tone: 'teal' | 'blue' | 'indigo' | 'amber' | 'purple' | 'green'
  icon: Component
}>()
</script>

<template>
  <article :class="['gm-card', 'gm-metric-card', `is-${tone}`]">
    <div class="gm-metric-icon">
      <el-icon><component :is="icon" /></el-icon>
    </div>
    <div class="gm-metric-body">
      <span class="gm-metric-label">{{ label }}</span>
      <div class="gm-metric-number">
        <strong class="gm-metric-value">{{ value }}</strong>
        <span v-if="unit" class="gm-metric-unit">{{ unit }}</span>
      </div>
    </div>
  </article>
</template>
