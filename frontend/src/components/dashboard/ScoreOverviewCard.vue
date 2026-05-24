<script setup lang="ts">
import { computed } from 'vue'
import type { ScoreOverview } from '../../api/dashboard'

const props = defineProps<{
  overview: ScoreOverview | null
}>()

const distribution = computed(() => {
  const abnormalTotal = distributionTotal.value
  const abnormalDistribution = props.overview?.abnormal_distribution || {}
  const rows = [
    { label: '缺考', status: 'absent', fallback: props.overview?.absent_count ?? 0, tone: '#d89614' },
    { label: '缓考', status: 'deferred', fallback: 0, tone: '#2f80ed' },
    { label: '作弊', status: 'cheating', fallback: props.overview?.cheating_count ?? 0, tone: '#d64545' },
    { label: '免考', status: 'exempt', fallback: 0, tone: '#2f9e63' },
    { label: '低分预警', status: 'low_score_warning', fallback: props.overview?.low_score_warning ?? 0, tone: '#5b6ee1' },
    { label: '不及格', status: 'failing_count', fallback: props.overview?.failing_count ?? 0, tone: '#7c5cc4' },
  ]
  return rows.map((row) => {
    const count = abnormalDistribution[row.status] ?? row.fallback
    return {
      label: row.label,
      count,
      percentage: abnormalTotal ? (count / abnormalTotal * 100).toFixed(2) : '0.00',
      tone: row.tone,
    }
  })
})

const distributionTotal = computed(() => {
  const abnormalDistribution = props.overview?.abnormal_distribution || {}
  const abnormalStatusTotal =
    (abnormalDistribution.absent ?? props.overview?.absent_count ?? 0) +
    (abnormalDistribution.deferred ?? 0) +
    (abnormalDistribution.cheating ?? props.overview?.cheating_count ?? 0) +
    (abnormalDistribution.exempt ?? 0)
  return abnormalStatusTotal + (props.overview?.low_score_warning ?? 0) + (props.overview?.failing_count ?? 0)
})

const donutStyle = computed(() => {
  const total = distributionTotal.value
  if (!total) return { background: 'conic-gradient(#dce6ea 0 100%)' }
  let cursor = 0
  const segments = distribution.value
    .filter((item) => item.count > 0)
    .map((item) => {
      const start = cursor
      cursor += (item.count / total) * 100
      return `${item.tone} ${start}% ${cursor}%`
    })
  return { background: `conic-gradient(${segments.join(', ')})` }
})

function display(value: string | number | null | undefined) {
  return value ?? '-'
}
</script>

<template>
  <section class="gm-page-card gm-score-overview">
    <div class="gm-section-title">
      <h2>成绩概览</h2>
    </div>
    <div class="gm-score-metrics">
      <div>
        <span>平均分</span>
        <strong>{{ display(overview?.average_score) }}</strong>
      </div>
      <div>
        <span>最高分</span>
        <strong>{{ display(overview?.highest_score) }}</strong>
      </div>
      <div>
        <span>最低分</span>
        <strong>{{ display(overview?.lowest_score) }}</strong>
      </div>
      <div>
        <span>异常人数</span>
        <strong>{{ distributionTotal }}</strong>
      </div>
    </div>

    <div class="gm-abnormal-panel">
      <div class="gm-abnormal-heading">
        <h3>异常状态分布</h3>
        <span class="gm-abnormal-summary">共 <strong>{{ distributionTotal }} 人</strong></span>
      </div>
      <div class="gm-abnormal-content">
        <div class="gm-donut" :style="donutStyle">
          <div>
            <span>异常合计</span>
            <strong>{{ distributionTotal }}人</strong>
          </div>
        </div>
        <div class="gm-abnormal-grid">
          <div v-for="item in distribution" :key="item.label" class="gm-abnormal-item">
            <span class="gm-abnormal-name">
              <i class="gm-abnormal-dot" :style="{ background: item.tone }" />
              {{ item.label }}
            </span>
            <strong>{{ item.count }} 人</strong>
            <small>{{ item.percentage }}%</small>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
