<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ClassAverageTrendPoint } from '../../api/dashboard'

const props = withDefaults(defineProps<{
  points: ClassAverageTrendPoint[]
  academicYears?: string[]
  selectedAcademicYear?: string
}>(), {
  academicYears: () => [],
  selectedAcademicYear: '',
})

const emit = defineEmits<{
  'update:selectedAcademicYear': [academicYear: string]
}>()

const MAX_VISIBLE_POINTS = 8
const CHART_LEFT = 8
const CHART_RIGHT = 98
const CHART_TOP = 6
const CHART_BOTTOM = 58
const yAxisTicks = [100, 50, 0]
const selectedClassId = ref<number | null>(null)

const classGroups = computed(() => {
  const groups = new Map<number, { class_id: number; class_name: string; points: ClassAverageTrendPoint[] }>()
  for (const point of props.points) {
    if (!groups.has(point.class_id)) {
      groups.set(point.class_id, {
        class_id: point.class_id,
        class_name: point.class_name || '未关联班级',
        points: [],
      })
    }
    groups.get(point.class_id)?.points.push(point)
  }
  return [...groups.values()]
})

const selectedGroup = computed(() => classGroups.value.find((item) => item.class_id === selectedClassId.value) || classGroups.value[0])

const visiblePoints = computed(() => {
  const points = selectedGroup.value?.points || []
  return points.slice(0, MAX_VISIBLE_POINTS).reverse()
})

const latestPoint = computed(() => visiblePoints.value[visiblePoints.value.length - 1] || null)
const scoreValues = computed(() => visiblePoints.value.map((point) => scoreNumber(point.average_score)))
const highestScore = computed(() => (scoreValues.value.length ? Math.max(...scoreValues.value) : null))
const lowestScore = computed(() => (scoreValues.value.length ? Math.min(...scoreValues.value) : null))
const scoreRange = computed(() => {
  if (highestScore.value === null || lowestScore.value === null) return '-'
  return (highestScore.value - lowestScore.value).toFixed(2)
})

const chartPolyline = computed(() =>
  visiblePoints.value
    .map((point, index) => {
      const x = xPosition(index)
      const y = yPosition(scoreNumber(point.average_score))
      return `${x},${y}`
    })
    .join(' '),
)

const chartAreaPolygon = computed(() => {
  if (!visiblePoints.value.length) return ''
  const firstX = xPosition(0)
  const lastX = xPosition(visiblePoints.value.length - 1)
  return `${firstX},${CHART_BOTTOM} ${chartPolyline.value} ${lastX},${CHART_BOTTOM}`
})

const chartBars = computed(() =>
  visiblePoints.value.map((point, index) => {
    const value = scoreNumber(point.average_score)
    const y = yPosition(value)
    const width = barWidth()
    return {
      key: `${point.exam_id}-${point.class_id}`,
      x: xPosition(index) - width / 2,
      y,
      width,
      height: CHART_BOTTOM - y,
    }
  }),
)

const chartDots = computed(() =>
  visiblePoints.value.map((point, index) => ({
    key: `${point.exam_id}-${point.class_id}`,
    x: xPosition(index),
    y: yPosition(scoreNumber(point.average_score)),
    isLatest: index === visiblePoints.value.length - 1,
  })),
)

const xAxisLabels = computed(() =>
  visiblePoints.value
    .map((point, index) => ({
      key: `${point.exam_id}-${point.class_id}`,
      x: xPosition(index),
      label: axisLabelText(point.exam_name),
      visible: shouldShowXAxisLabel(index),
    }))
    .filter((item) => item.visible),
)

watch(
  classGroups,
  (groups) => {
    if (!groups.length) {
      selectedClassId.value = null
      return
    }
    if (!groups.some((item) => item.class_id === selectedClassId.value)) {
      selectedClassId.value = groups[0].class_id
    }
  },
  { immediate: true },
)

function scoreNumber(value: string | number | null | undefined) {
  const parsed = Number(value ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

function axisLabelText(value: string | null | undefined) {
  const text = value || '未命名考试'
  return text.length > 6 ? `${text.slice(0, 6)}...` : text
}

function scoreText(value: string | number | null | undefined) {
  return value ?? '-'
}

function metricText(value: number | null) {
  return value === null ? '-' : value.toFixed(2)
}

function xPosition(index: number) {
  if (visiblePoints.value.length <= 1) return (CHART_LEFT + CHART_RIGHT) / 2
  return CHART_LEFT + (index / (visiblePoints.value.length - 1)) * (CHART_RIGHT - CHART_LEFT)
}

function yPosition(value: number) {
  const normalized = Math.min(Math.max(value, 0), 100)
  return CHART_BOTTOM - (normalized / 100) * (CHART_BOTTOM - CHART_TOP)
}

function barWidth() {
  if (visiblePoints.value.length <= 1) return 10
  return Math.max(5, Math.min(9, (CHART_RIGHT - CHART_LEFT) / visiblePoints.value.length / 2))
}

function shouldShowXAxisLabel(index: number) {
  const total = visiblePoints.value.length
  if (total <= 4) return true
  const step = Math.ceil((total - 1) / 3)
  return index === 0 || index === total - 1 || index % step === 0
}

function selectAcademicYear(academicYear: string) {
  emit('update:selectedAcademicYear', academicYear)
}
</script>

<template>
  <section class="gm-page-card gm-trend-card gm-dashboard-analysis-card">
    <div class="gm-section-title">
      <h2>班级均分趋势</h2>
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

    <el-empty v-if="!points.length" description="暂无趋势数据" :image-size="64" />
    <template v-else>
      <div class="gm-trend-class-strip" aria-label="班级筛选">
        <button
          v-for="group in classGroups"
          :key="group.class_id"
          class="gm-trend-class-chip"
          :class="{ 'is-active': group.class_id === selectedGroup?.class_id }"
          type="button"
          @click="selectedClassId = group.class_id"
        >
          {{ group.class_name }}
        </button>
      </div>

      <div class="gm-trend-summary">
        <div>
          <span>当前班级</span>
          <strong class="gm-trend-selected-class">{{ selectedGroup?.class_name }}</strong>
        </div>
        <div>
          <span>最新均分</span>
          <strong>{{ scoreText(latestPoint?.average_score) }}</strong>
        </div>
        <div>
          <span>最高均分</span>
          <strong>{{ metricText(highestScore) }}</strong>
        </div>
        <div>
          <span>波动范围</span>
          <strong>{{ scoreRange }}</strong>
        </div>
      </div>

      <div class="gm-analysis-visual-panel gm-trend-chart-shell">
        <svg class="gm-trend-chart" viewBox="0 0 100 72" role="img" :aria-label="`${selectedGroup?.class_name}均分趋势`">
          <line
            v-for="tick in yAxisTicks"
            :key="tick"
            class="gm-trend-grid-line"
            :x1="CHART_LEFT"
            :y1="yPosition(tick)"
            :x2="CHART_RIGHT"
            :y2="yPosition(tick)"
          />
          <line class="gm-trend-axis-y" :x1="CHART_LEFT" :y1="CHART_TOP" :x2="CHART_LEFT" :y2="CHART_BOTTOM" />
          <line class="gm-trend-axis-x" :x1="CHART_LEFT" :y1="CHART_BOTTOM" :x2="CHART_RIGHT" :y2="CHART_BOTTOM" />
          <rect
            v-for="bar in chartBars"
            :key="bar.key"
            class="gm-trend-bar"
            :x="bar.x"
            :y="bar.y"
            :width="bar.width"
            :height="bar.height"
            rx="1.2"
          />
          <polygon v-if="chartAreaPolygon" class="gm-trend-area" :points="chartAreaPolygon" />
          <polyline v-if="visiblePoints.length > 1" class="gm-trend-line" :points="chartPolyline" />
          <circle
            v-for="dot in chartDots"
            :key="dot.key"
            class="gm-trend-dot"
            :class="{ 'is-latest': dot.isLatest }"
            :cx="dot.x"
            :cy="dot.y"
            r="2"
          />
          <text
            v-for="tick in yAxisTicks"
            :key="`label-${tick}`"
            class="gm-trend-axis-label"
            :x="CHART_LEFT - 2"
            :y="yPosition(tick) + 1.2"
            text-anchor="end"
          >
            {{ tick }}
          </text>
          <text
            v-for="label in xAxisLabels"
            :key="label.key"
            class="gm-trend-x-label"
            :x="label.x"
            y="68"
            text-anchor="middle"
          >
            {{ label.label }}
          </text>
        </svg>
        <div class="gm-analysis-legend">
          <span><i class="is-line" />折线：均分变化</span>
          <span><i class="is-bar" />柱状：单次考试均分</span>
        </div>
      </div>

      <div class="gm-trend-point-list">
        <div v-for="point in visiblePoints" :key="`${point.exam_id}-${point.class_id}`" class="gm-trend-point">
          <span class="gm-trend-point-label">{{ point.exam_name || '未命名考试' }}</span>
          <strong class="gm-trend-point-value">{{ scoreText(point.average_score) }}</strong>
        </div>
      </div>
    </template>
  </section>
</template>
