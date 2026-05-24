<script setup lang="ts">
import { computed } from 'vue'
import type { ScoreOverview } from '../../api/dashboard'

interface ScoreClassOption {
  id: number
  name: string
}

interface StatusRowConfig {
  key: string
  label: string
  tone: string
  count: () => number
}

const props = withDefaults(defineProps<{
  overview: ScoreOverview | null
  classOptions?: ScoreClassOption[]
  selectedClassId?: number | null
  academicYears?: string[]
  selectedAcademicYear?: string
}>(), {
  classOptions: () => [],
  selectedClassId: null,
  academicYears: () => [],
  selectedAcademicYear: '',
})

const emit = defineEmits<{
  'update:selectedClassId': [classId: number | null]
  'update:selectedAcademicYear': [academicYear: string]
}>()

const statusRows = computed(() => {
  const abnormalDistribution = props.overview?.abnormal_distribution || {}
  const rows: StatusRowConfig[] = [
    { key: 'normal', label: '正常考试', tone: '#2f9e63', count: () => props.overview?.normal_count ?? 0 },
    { key: 'absent', label: '缺考', tone: '#d89614', count: () => abnormalDistribution.absent ?? props.overview?.absent_count ?? 0 },
    { key: 'deferred', label: '缓考', tone: '#2f80ed', count: () => abnormalDistribution.deferred ?? 0 },
    { key: 'cheating', label: '作弊', tone: '#d64545', count: () => abnormalDistribution.cheating ?? props.overview?.cheating_count ?? 0 },
    { key: 'exempt', label: '免考', tone: '#2f9e63', count: () => abnormalDistribution.exempt ?? 0 },
    { key: 'low-score', label: '低分预警', tone: '#5b6ee1', count: () => props.overview?.low_score_warning ?? 0 },
    { key: 'failing', label: '不及格', tone: '#7c5cc4', count: () => props.overview?.failing_count ?? 0 },
  ]

  const maxCount = Math.max(...rows.map((row) => row.count()), 1)
  return rows.map((row) => {
    const count = row.count()
    return {
      key: row.key,
      label: row.label,
      count,
      tone: row.tone,
      width: count ? `${Math.max((count / maxCount) * 100, 4).toFixed(2)}%` : '0%',
    }
  })
})

const abnormalTotal = computed(() => props.overview?.abnormal_count ?? 0)
const referenceCount = computed(() => props.overview?.reference_count ?? 0)
const normalCount = computed(() => props.overview?.normal_count ?? 0)

const donutStyle = computed(() => {
  const total = normalCount.value + abnormalTotal.value
  if (!total) return { background: 'conic-gradient(#dce6ea 0 100%)' }

  const segments = statusRows.value
    .filter((item) => ['normal', 'absent', 'deferred', 'cheating', 'exempt'].includes(item.key))
    .filter((item) => item.count > 0)

  let cursor = 0
  const gradient = segments.map((item) => {
    const start = cursor
    cursor += (item.count / total) * 100
    return `${item.tone} ${start}% ${cursor}%`
  })
  return { background: `conic-gradient(${gradient.join(', ')})` }
})

function display(value: string | number | null | undefined) {
  return value ?? '-'
}

function selectClass(classId: number | null) {
  emit('update:selectedClassId', classId)
}

function selectAcademicYear(academicYear: string) {
  emit('update:selectedAcademicYear', academicYear)
}
</script>

<template>
  <section class="gm-page-card gm-score-overview gm-dashboard-analysis-card">
    <div class="gm-section-title">
      <h2>成绩概览</h2>
      <el-select
        class="gm-academic-year-select"
        :model-value="selectedAcademicYear"
        placeholder="选择学年"
        @update:model-value="selectAcademicYear"
      >
        <el-option
          v-for="academicYear in academicYears"
          :key="academicYear"
          :label="`${academicYear} 学年`"
          :value="academicYear"
        />
      </el-select>
    </div>

    <div class="gm-score-class-filter gm-trend-class-strip" aria-label="成绩概览班级筛选">
      <button
        class="gm-score-class-chip gm-trend-class-chip"
        :class="{ 'is-active': selectedClassId === null }"
        type="button"
        @click="selectClass(null)"
      >
        全部
      </button>
      <button
        v-for="classOption in classOptions"
        :key="classOption.id"
        class="gm-score-class-chip gm-trend-class-chip"
        :class="{ 'is-active': selectedClassId === classOption.id }"
        type="button"
        @click="selectClass(classOption.id)"
      >
        {{ classOption.name }}
      </button>
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
        <span>正常考试</span>
        <strong>{{ normalCount }}</strong>
      </div>
    </div>

    <div class="gm-analysis-visual-panel gm-score-visuals">
      <div class="gm-donut-wrap">
        <div class="gm-donut" :style="donutStyle">
          <div>
            <span>正常考试</span>
            <strong>{{ normalCount }}人</strong>
          </div>
        </div>
      </div>

      <div class="gm-status-bar-area">
        <div class="gm-chart-heading">
          <span>状态人数分布</span>
          <span>共 {{ referenceCount }} 人次</span>
        </div>
        <div class="gm-status-bar-list">
          <div v-for="item in statusRows" :key="item.key" class="gm-status-bar-row">
            <span>{{ item.label }}</span>
            <div class="gm-status-track">
              <div class="gm-status-fill" :style="{ width: item.width, background: item.tone }" />
            </div>
            <strong>{{ item.count }} 人</strong>
          </div>
        </div>
      </div>
    </div>

    <div class="gm-status-info-grid">
      <div v-for="item in statusRows" :key="item.key" class="gm-status-info-item">
        <span class="gm-status-label">
          <i class="gm-status-dot" :style="{ background: item.tone }" />
          {{ item.label }}
        </span>
        <strong>{{ item.count }} 人</strong>
      </div>
    </div>
  </section>
</template>
