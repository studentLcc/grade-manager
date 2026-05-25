<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listClasses, type ClassRecord } from '../api/classes'
import { getExam, type ExamRecord } from '../api/exams'
import {
  getExamRankings,
  getExamSegments,
  getExamStatisticsSummary,
  type ComparisonItem,
  type RankingRecord,
  type SegmentRecord,
  type StatisticsSummary,
  type StudentListItem,
} from '../api/statistics'

interface DisplayItem {
  label: string
  value: unknown
}

type StatsTabKey = 'overview' | 'rankings' | 'segments' | 'exceptions'
type ExceptionType = 'absent' | 'deferred' | 'cheating' | 'exempt' | 'missing'

const route = useRoute()
const router = useRouter()
const examId = computed(() => Number(route.params.id))
const baseLoading = ref(false)
const summaryLoading = ref(false)
const rankingsLoading = ref(false)
const segmentsLoading = ref(false)
const exam = ref<ExamRecord | null>(null)
const classes = ref<ClassRecord[]>([])
const summary = ref<StatisticsSummary>({} as StatisticsSummary)
const rankings = ref<RankingRecord[]>([])
const segments = ref<SegmentRecord[]>([])
const activeStatsTab = ref<StatsTabKey>('overview')
const activeExceptionType = ref<ExceptionType>('absent')
let routeVersion = 0
let baseRequestSeq = 0
let summaryRequestSeq = 0
let rankingRequestSeq = 0
let segmentRequestSeq = 0
let loadedBaseExamId: number | null = null

const filters = reactive({
  included_statuses: ['normal'],
  ranking_type: 'total',
  segment_type: 'total',
  exam_subject_id: undefined as number | undefined,
  segment_step: 10,
  class_id: undefined as number | undefined,
})

const statusOptions = [
  { label: '正常', value: 'normal' },
  { label: '缺考', value: 'absent' },
  { label: '缓考', value: 'deferred' },
  { label: '作弊', value: 'cheating' },
  { label: '免考', value: 'exempt' },
]

const abnormalTypes: Array<{ label: string; value: Exclude<ExceptionType, 'missing'> }> = [
  { label: '缺考', value: 'absent' },
  { label: '缓考', value: 'deferred' },
  { label: '作弊', value: 'cheating' },
  { label: '免考', value: 'exempt' },
]

const subjectOptions = computed(() => exam.value?.subjects || [])
const shouldShowRankingSubject = computed(() => filters.ranking_type === 'subject')
const shouldShowSegmentSubject = computed(() => filters.segment_type === 'subject')
const abnormalCounts = computed(() => summary.value.abnormal_counts || {})
const exceptionTotal = computed(() => abnormalTypes.reduce((total, item) => total + (abnormalCounts.value[item.value] || 0), 0) + (summary.value.missing_score_count || 0))
const loading = computed(
  () =>
    baseLoading.value ||
    summaryLoading.value ||
    (activeStatsTab.value === 'rankings' && rankingsLoading.value) ||
    (activeStatsTab.value === 'segments' && segmentsLoading.value),
)

const statsTabs = computed<Array<{ key: StatsTabKey; label: string; count?: number }>>(() => [
  { key: 'overview', label: '概览' },
  { key: 'rankings', label: '排名' },
  { key: 'segments', label: '分数段' },
  { key: 'exceptions', label: '异常名单', count: exceptionTotal.value },
])

const exceptionOptions = computed<Array<{ label: string; value: ExceptionType; count: number }>>(() => [
  ...abnormalTypes.map((item) => ({
    label: item.label,
    value: item.value,
    count: abnormalCounts.value[item.value] || 0,
  })),
  { label: '缺失成绩', value: 'missing', count: summary.value.missing_score_count || 0 },
])

const activeExceptionRows = computed<StudentListItem[]>(() => {
  if (activeExceptionType.value === 'missing') return summary.value.missing_score_list || []
  return summary.value.abnormal_lists?.[activeExceptionType.value] || []
})

const overallItems = computed<DisplayItem[]>(() => {
  const overall = summary.value.overall || {}
  return [
    { label: '平均分', value: overall.average_score ?? '-' },
    { label: '最高分', value: overall.highest_score ?? '-' },
    { label: '最低分', value: overall.lowest_score ?? '-' },
    { label: '及格率', value: overall.pass_rate ?? '-' },
    { label: '优秀率', value: overall.excellent_rate ?? '-' },
    { label: '缺失成绩', value: summary.value.missing_score_count ?? 0 },
  ]
})

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

function summaryParams() {
  return compactParams({
    included_statuses: filters.included_statuses.join(','),
  })
}

function rankingParams() {
  return compactParams({
    included_statuses: filters.included_statuses.join(','),
    class_id: filters.class_id,
    exam_subject_id: filters.ranking_type === 'subject' ? filters.exam_subject_id : undefined,
    rank_type: filters.ranking_type,
  })
}

function segmentParams() {
  return compactParams({
    included_statuses: filters.included_statuses.join(','),
    class_id: filters.class_id,
    exam_subject_id: filters.segment_type === 'subject' ? filters.exam_subject_id : undefined,
    type: filters.segment_type,
    step: filters.segment_step,
  })
}

function comparisonLabel(item: ComparisonItem, fallback: string) {
  return item.name || fallback
}

async function loadBase() {
  const targetExamId = examId.value
  const targetVersion = routeVersion
  const requestId = ++baseRequestSeq
  baseLoading.value = true
  try {
    const [examResponse, classResponse] = await Promise.all([getExam(targetExamId), listClasses({ status: 'active', page: 1, page_size: 100 })])
    if (requestId !== baseRequestSeq || routeVersion !== targetVersion || examId.value !== targetExamId) return false
    exam.value = examResponse.data
    classes.value = classResponse.data.items
    loadedBaseExamId = targetExamId
    return true
  } catch {
    return false
  } finally {
    if (requestId === baseRequestSeq) baseLoading.value = false
  }
}

async function ensureBase() {
  if (loadedBaseExamId === examId.value && exam.value) return true
  return loadBase()
}

function ensureSubjectSelection(kind: 'ranking' | 'segment') {
  const needsSubject = kind === 'ranking' ? shouldShowRankingSubject.value : shouldShowSegmentSubject.value
  if (!needsSubject) return true
  if (filters.exam_subject_id) return true
  const firstSubject = subjectOptions.value[0]
  if (!firstSubject) return false
  filters.exam_subject_id = firstSubject.id
  return false
}

async function loadSummary() {
  const targetExamId = examId.value
  const targetVersion = routeVersion
  const requestId = ++summaryRequestSeq
  summaryLoading.value = true
  try {
    const baseReady = await ensureBase()
    if (!baseReady) return
    const summaryResponse = await getExamStatisticsSummary(targetExamId, summaryParams())
    if (requestId !== summaryRequestSeq || routeVersion !== targetVersion || examId.value !== targetExamId) return
    summary.value = summaryResponse.data
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === summaryRequestSeq) summaryLoading.value = false
  }
}

async function loadRankings() {
  const targetExamId = examId.value
  const targetVersion = routeVersion
  const requestId = ++rankingRequestSeq
  rankingsLoading.value = true
  try {
    const baseReady = await ensureBase()
    if (!baseReady || !ensureSubjectSelection('ranking')) return
    const rankingResponse = await getExamRankings(targetExamId, rankingParams())
    if (requestId !== rankingRequestSeq || routeVersion !== targetVersion || examId.value !== targetExamId) return
    rankings.value = rankingResponse.data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === rankingRequestSeq) rankingsLoading.value = false
  }
}

async function loadSegments() {
  const targetExamId = examId.value
  const targetVersion = routeVersion
  const requestId = ++segmentRequestSeq
  segmentsLoading.value = true
  try {
    const baseReady = await ensureBase()
    if (!baseReady || !ensureSubjectSelection('segment')) return
    const segmentResponse = await getExamSegments(targetExamId, segmentParams())
    if (requestId !== segmentRequestSeq || routeVersion !== targetVersion || examId.value !== targetExamId) return
    segments.value = segmentResponse.data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === segmentRequestSeq) segmentsLoading.value = false
  }
}

function setStatsTab(tab: StatsTabKey) {
  activeStatsTab.value = tab
  if (tab === 'rankings') loadRankings()
  if (tab === 'segments') loadSegments()
  if ((tab === 'overview' || tab === 'exceptions') && !summary.value.exam) loadSummary()
}

function resetExamState() {
  routeVersion += 1
  exam.value = null
  summary.value = {} as StatisticsSummary
  rankings.value = []
  segments.value = []
  filters.exam_subject_id = undefined
  activeStatsTab.value = 'overview'
  activeExceptionType.value = 'absent'
  loadedBaseExamId = null
}

watch(
  () => examId.value,
  () => {
    resetExamState()
    loadSummary()
  },
)

watch(
  () => filters.included_statuses.join(','),
  () => {
    loadSummary()
    if (activeStatsTab.value === 'rankings') loadRankings()
    if (activeStatsTab.value === 'segments') loadSegments()
  },
)

watch(
  () => [filters.ranking_type, filters.exam_subject_id, filters.class_id],
  () => {
    if (activeStatsTab.value === 'rankings') loadRankings()
  },
)

watch(
  () => [filters.segment_type, filters.exam_subject_id, filters.segment_step, filters.class_id],
  () => {
    if (activeStatsTab.value === 'segments') loadSegments()
  },
)

onMounted(() => {
  resetExamState()
  loadSummary()
})
</script>

<template>
  <section v-loading="loading" class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>{{ exam?.name || '考试统计' }}</h1>
        <p>统计口径由后端接口计算，筛选条件变更后重新加载。</p>
      </div>
      <el-button @click="router.push(`/exam-center/${examId}`)">返回考试详情</el-button>
    </div>

    <section class="gm-page-card gm-stats-control-card">
      <div class="gm-filter-row gm-filter-row-wide gm-stats-filter-row">
        <el-select v-model="filters.included_statuses" multiple collapse-tags placeholder="计入状态">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>
      <div class="gm-stats-tabs" role="tablist" aria-label="统计视图">
        <button
          v-for="tab in statsTabs"
          :key="tab.key"
          type="button"
          class="gm-stats-tab"
          :class="{ 'is-active': activeStatsTab === tab.key }"
          role="tab"
          :aria-selected="activeStatsTab === tab.key"
          @click="setStatsTab(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <strong v-if="tab.count !== undefined">{{ tab.count }}</strong>
        </button>
      </div>
    </section>

    <div v-if="activeStatsTab === 'overview'" class="gm-overview-section gm-stats-panel-grid">
      <section class="gm-page-card gm-stats-section">
        <h2>核心指标</h2>
        <div class="gm-stat-metric-grid">
          <div v-for="item in overallItems" :key="item.label" class="gm-stat-metric">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <section class="gm-page-card gm-stats-section">
        <h2>班级对比</h2>
        <div class="gm-stat-list">
          <div v-for="(item, index) in summary.class_comparison || []" :key="comparisonLabel(item, `班级 ${index + 1}`)">
            <span>{{ comparisonLabel(item, `班级 ${index + 1}`) }}</span>
            <strong>{{ item.average_score ?? '-' }}</strong>
          </div>
        </div>
      </section>

      <section class="gm-page-card gm-stats-section">
        <h2>科目对比</h2>
        <div class="gm-stat-list">
          <div v-for="(item, index) in summary.subject_comparison || []" :key="comparisonLabel(item, `科目 ${index + 1}`)">
            <span>{{ comparisonLabel(item, `科目 ${index + 1}`) }}</span>
            <strong>{{ item.average_score ?? '-' }}</strong>
          </div>
        </div>
      </section>
    </div>

    <section v-else-if="activeStatsTab === 'rankings'" class="gm-page-card gm-ranking-section">
      <div class="gm-section-title">
        <h2>排名</h2>
      </div>
      <div class="gm-filter-row gm-filter-row-wide gm-stats-inner-filter">
        <el-select v-model="filters.ranking_type" placeholder="排名类型">
          <el-option label="总分排名" value="total" />
          <el-option label="单科排名" value="subject" />
        </el-select>
        <el-select v-if="shouldShowRankingSubject" v-model="filters.exam_subject_id" placeholder="排名科目" clearable>
          <el-option v-for="subject in subjectOptions" :key="subject.id" :label="subject.course_name || '未命名科目'" :value="subject.id" />
        </el-select>
        <el-select v-model="filters.class_id" placeholder="排名班级" clearable>
          <el-option v-for="classRecord in classes" :key="classRecord.id" :label="classRecord.name" :value="classRecord.id" />
        </el-select>
      </div>
      <el-table v-loading="rankingsLoading" border class="gm-data-table" :data="rankings" empty-text="暂无排名数据">
        <el-table-column prop="rank" label="排名" width="80" />
        <el-table-column prop="name" label="学生" />
        <el-table-column prop="student_no" label="学号" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="score" label="成绩" />
      </el-table>
    </section>

    <section v-else-if="activeStatsTab === 'segments'" class="gm-page-card gm-segment-section">
      <div class="gm-section-title">
        <h2>分数段</h2>
      </div>
      <div class="gm-filter-row gm-filter-row-wide gm-stats-inner-filter">
        <el-select v-model="filters.segment_type" placeholder="分段类型">
          <el-option label="总分分段" value="total" />
          <el-option label="单科分段" value="subject" />
        </el-select>
        <el-select v-if="shouldShowSegmentSubject" v-model="filters.exam_subject_id" placeholder="分段科目" clearable>
          <el-option v-for="subject in subjectOptions" :key="subject.id" :label="subject.course_name || '未命名科目'" :value="subject.id" />
        </el-select>
        <el-input-number v-model="filters.segment_step" :min="1" :max="100" controls-position="right" />
        <el-select v-model="filters.class_id" placeholder="分段班级" clearable>
          <el-option v-for="classRecord in classes" :key="classRecord.id" :label="classRecord.name" :value="classRecord.id" />
        </el-select>
      </div>
      <el-table v-loading="segmentsLoading" border class="gm-data-table" :data="segments" empty-text="暂无分段数据">
        <el-table-column prop="label" label="分段" />
        <el-table-column prop="start" label="起始分" width="100" />
        <el-table-column prop="end" label="结束分" width="100" />
        <el-table-column prop="count" label="人数" width="100" />
      </el-table>
    </section>

    <section v-else class="gm-page-card gm-exception-section">
      <div class="gm-section-title">
        <h2>异常与缺失</h2>
      </div>
      <div class="gm-exception-tabs" role="tablist" aria-label="异常类型">
        <button
          v-for="item in exceptionOptions"
          :key="item.value"
          type="button"
          class="gm-exception-type-chip"
          :class="{ 'is-active': activeExceptionType === item.value }"
          role="tab"
          :aria-selected="activeExceptionType === item.value"
          @click="activeExceptionType = item.value"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.count }}</strong>
        </button>
      </div>
      <el-table border class="gm-data-table" :class="'gm-exception-table'" :data="activeExceptionRows" empty-text="暂无记录">
        <el-table-column prop="name" label="学生" />
        <el-table-column prop="student_no" label="学号" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="course_name" label="科目" />
      </el-table>
    </section>
  </section>
</template>
