<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataAnalysis, Files, Notebook, Reading, School, User } from '@element-plus/icons-vue'
import { listClasses, type ClassRecord } from '../api/classes'
import {
  getClassAverageTrend,
  getDashboardScoreOverview,
  getDashboardSummary,
  getRecentExams,
  getTodaySchedule,
  type ClassAverageTrendPoint,
  type DashboardSummary,
  type RecentExamRecord,
  type ScoreOverview,
  type TodayScheduleRecord,
} from '../api/dashboard'
import ClassAverageTrend from '../components/dashboard/ClassAverageTrend.vue'
import MetricCard from '../components/dashboard/MetricCard.vue'
import RecentExams from '../components/dashboard/RecentExams.vue'
import ScoreOverviewCard from '../components/dashboard/ScoreOverviewCard.vue'
import TodaySchedule from '../components/dashboard/TodaySchedule.vue'

const router = useRouter()
const loading = ref(false)
const summary = ref<DashboardSummary>({
  class_count: 0,
  student_count: 0,
  course_count: 0,
  recent_exam_count: 0,
  pending_score_count: 0,
})
const schedules = ref<TodayScheduleRecord[]>([])
const exams = ref<RecentExamRecord[]>([])
const overview = ref<ScoreOverview | null>(null)
const trend = ref<ClassAverageTrendPoint[]>([])
const classes = ref<ClassRecord[]>([])
const selectedAcademicYear = ref('')
const selectedScoreClassId = ref<number | null>(null)

const academicYears = computed(() => {
  const years = new Set(classes.value.map((classRecord) => classRecord.academic_year).filter(Boolean) as string[])
  if (!years.size) years.add(currentAcademicYear())
  return [...years].sort((left, right) => right.localeCompare(left))
})

const scoreClassOptions = computed(() => {
  return classes.value
    .filter((classRecord) => classRecord.status === 'active')
    .filter((classRecord) => !selectedAcademicYear.value || classRecord.academic_year === selectedAcademicYear.value)
    .map((classRecord) => ({ id: classRecord.id, name: classRecord.name || '未命名班级' }))
})

async function loadDashboard() {
  loading.value = true
  try {
    const [summaryResponse, scheduleResponse, examResponse, classesResponse] = await Promise.all([
      getDashboardSummary(),
      getTodaySchedule(),
      getRecentExams(),
      listClasses({ status: 'active', page: 1, page_size: 1000 }),
    ])
    summary.value = summaryResponse.data
    schedules.value = scheduleResponse.data.items
    exams.value = examResponse.data.items
    classes.value = classesResponse.data.items
    syncAcademicYear()
    syncSelectedScoreClass()
    await loadAnalysisCards()
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    loading.value = false
  }
}

async function loadAnalysisCards() {
  const params = { classId: selectedScoreClassId.value, academicYear: selectedAcademicYear.value }
  const [overviewResponse, trendResponse] = await Promise.all([
    getDashboardScoreOverview(params),
    getClassAverageTrend(selectedAcademicYear.value),
  ])
  overview.value = overviewResponse.data
  trend.value = trendResponse.data.items
}

async function handleScoreClassChange(classId: number | null) {
  selectedScoreClassId.value = classId
  try {
    const response = await getDashboardScoreOverview({ classId, academicYear: selectedAcademicYear.value })
    overview.value = response.data
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function handleAcademicYearChange(academicYear: string) {
  selectedAcademicYear.value = academicYear
  syncSelectedScoreClass()
  try {
    await loadAnalysisCards()
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

function syncAcademicYear() {
  const availableYears = academicYears.value
  if (!selectedAcademicYear.value || !availableYears.includes(selectedAcademicYear.value)) {
    selectedAcademicYear.value = availableYears[0] || currentAcademicYear()
  }
}

function syncSelectedScoreClass() {
  if (selectedScoreClassId.value && !scoreClassOptions.value.some((classRecord) => classRecord.id === selectedScoreClassId.value)) {
    selectedScoreClassId.value = null
  }
}

function currentAcademicYear() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const startYear = month >= 9 ? year : year - 1
  return `${startYear}-${startYear + 1}`
}

onMounted(loadDashboard)
</script>

<template>
  <section v-loading="loading" class="gm-dashboard" aria-label="仪表盘">
    <div class="gm-page-header">
      <div>
        <h1>工作台</h1>
        <p>快速查看今日课程、近期考试和成绩处理概况。</p>
      </div>
      <div class="gm-header-actions">
        <el-button type="primary" :icon="Files" @click="router.push('/exam-center')">创建考试</el-button>
        <el-button :icon="User" @click="router.push('/classes-students')">导入学生</el-button>
        <el-button :icon="Notebook" @click="router.push('/exam-center')">录入成绩</el-button>
        <el-button :icon="DataAnalysis" @click="router.push('/statistics')">查看统计</el-button>
      </div>
    </div>

    <div class="gm-metrics">
      <MetricCard label="班级数" :value="summary.class_count" unit="个" tone="teal" :icon="School" />
      <MetricCard label="学生数" :value="summary.student_count" unit="人" tone="blue" :icon="User" />
      <MetricCard label="课程数" :value="summary.course_count" unit="门" tone="indigo" :icon="Reading" />
      <MetricCard label="待录入成绩" :value="summary.pending_score_count" unit="份" tone="amber" :icon="Notebook" />
    </div>

    <div class="gm-dashboard-grid">
      <TodaySchedule :schedules="schedules" />
      <RecentExams :exams="exams" />
      <ScoreOverviewCard
        :overview="overview"
        :class-options="scoreClassOptions"
        :selected-class-id="selectedScoreClassId"
        :academic-years="academicYears"
        :selected-academic-year="selectedAcademicYear"
        @update:selected-class-id="handleScoreClassChange"
        @update:selected-academic-year="handleAcademicYearChange"
      />
      <ClassAverageTrend
        :points="trend"
        :academic-years="academicYears"
        :selected-academic-year="selectedAcademicYear"
        @update:selected-academic-year="handleAcademicYearChange"
      />
    </div>
  </section>
</template>
