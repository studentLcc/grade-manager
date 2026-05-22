<script setup lang="ts">
import { computed } from 'vue'
import type { ClassAverageTrendPoint } from '../../api/dashboard'

const props = defineProps<{
  points: ClassAverageTrendPoint[]
}>()

const maxScore = computed(() => {
  const values = props.points.map((item) => Number(item.average_score || 0))
  return Math.max(...values, 100)
})

function pointLabel(point: ClassAverageTrendPoint) {
  return point.exam_name || point.class_name || '-'
}

function pointWidth(point: ClassAverageTrendPoint) {
  return `${Math.max((Number(point.average_score || 0) / maxScore.value) * 100, 4)}%`
}
</script>

<template>
  <section class="gm-page-card">
    <div class="gm-section-title">
      <h2>班级均分趋势</h2>
    </div>
    <el-empty v-if="!points.length" description="暂无趋势数据" :image-size="64" />
    <div v-else class="gm-trend-list">
      <div v-for="(point, index) in points" :key="`${pointLabel(point)}-${index}`" class="gm-trend-row">
        <span>{{ pointLabel(point) }}</span>
        <div class="gm-trend-track">
          <div :style="{ width: pointWidth(point) }" />
        </div>
        <strong>{{ point.average_score ?? '-' }}</strong>
      </div>
    </div>
  </section>
</template>
