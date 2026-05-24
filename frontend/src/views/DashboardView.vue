<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataAnalysis, Files, Notebook, Reading, School, User } from '@element-plus/icons-vue'
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

async function loadDashboard() {
  loading.value = true
  try {
    const [summaryResponse, scheduleResponse, examResponse, overviewResponse, trendResponse] = await Promise.all([
      getDashboardSummary(),
      getTodaySchedule(),
      getRecentExams(),
      getDashboardScoreOverview(),
      getClassAverageTrend(),
    ])
    summary.value = summaryResponse.data
    schedules.value = scheduleResponse.data.items
    exams.value = examResponse.data.items
    overview.value = overviewResponse.data
    trend.value = trendResponse.data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    loading.value = false
  }
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
      <ScoreOverviewCard :overview="overview" />
      <ClassAverageTrend :points="trend" />
    </div>
  </section>
</template>
