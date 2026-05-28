<template>
  <div class="gm-table-surface" :class="{ 'is-compact': compact }">
    <div v-if="$slots.toolbar" class="gm-table-toolbar">
      <slot name="toolbar" />
    </div>
    <div class="gm-table-viewport">
      <slot />
    </div>
    <div v-if="$slots.pagination" class="gm-pagination">
      <slot name="pagination" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  compact?: boolean
}>()
</script>
