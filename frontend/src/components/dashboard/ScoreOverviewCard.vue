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
    { label: '缺考', status: 'absent', fallback: props.overview?.absent_count ?? 0 },
    { label: '缓考', status: 'deferred', fallback: 0 },
    { label: '作弊', status: 'cheating', fallback: props.overview?.cheating_count ?? 0 },
    { label: '免考', status: 'exempt', fallback: 0 },
  ]
  return rows.map((row) => {
    const count = abnormalDistribution[row.status] ?? row.fallback
    return {
      label: row.label,
      count,
      percentage: abnormalTotal ? (count / abnormalTotal * 100).toFixed(2) : '0.00',
    }
  })
})

const distributionTotal = computed(() => {
  return props.overview?.abnormal_count ?? 0
})

const donutStyle = computed(() => {
  const total = distributionTotal.value
  if (!total) return { background: 'conic-gradient(#dce6ea 0 100%)' }
  const abnormal = Math.min(Number(props.overview?.abnormal_count || 0), total)
  const percent = (abnormal / total) * 100
  return { background: `conic-gradient(var(--gm-amber) 0 ${percent}%, #dce6ea ${percent}% 100%)` }
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
        <strong>{{ overview?.abnormal_count ?? 0 }}</strong>
      </div>
    </div>

    <div class="gm-abnormal-panel">
      <h3>异常状态分布</h3>
      <div class="gm-abnormal-content">
        <div class="gm-donut" :style="donutStyle">
          <div>
            <strong>{{ distributionTotal }}</strong>
            <span>合计</span>
          </div>
        </div>
        <div class="gm-distribution-list">
          <div v-for="item in distribution" :key="item.label" class="gm-distribution-row">
            <span>{{ item.label }}</span>
            <strong>{{ item.count }} 人</strong>
            <small>{{ item.percentage }}%</small>
          </div>
        </div>
      </div>
      <div class="gm-warning-panel">
        <h3>预警指标</h3>
        <div class="gm-indicator-list">
          <div>
            <span>低分预警</span>
            <strong>{{ overview?.low_score_warning ?? 0 }} 人</strong>
          </div>
          <div>
            <span>不及格</span>
            <strong>{{ overview?.failing_count ?? 0 }} 人</strong>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
