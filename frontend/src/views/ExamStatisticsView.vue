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
} from '../api/statistics'

interface DisplayItem {
  label: string
  value: unknown
}

const route = useRoute()
const router = useRouter()
const examId = computed(() => Number(route.params.id))
const loading = ref(false)
const exam = ref<ExamRecord | null>(null)
const classes = ref<ClassRecord[]>([])
const summary = ref<StatisticsSummary>({} as StatisticsSummary)
const rankings = ref<RankingRecord[]>([])
const segments = ref<SegmentRecord[]>([])
let requestSeq = 0
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

const subjectOptions = computed(() => exam.value?.subjects || [])
const shouldShowSubject = computed(() => filters.ranking_type === 'subject' || filters.segment_type === 'subject')

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

function comparisonLabel(item: ComparisonItem, fallback: string) {
  return item.name || fallback
}

async function loadBase() {
  const targetExamId = examId.value
  const requestId = requestSeq
  const [examResponse, classResponse] = await Promise.all([getExam(targetExamId), listClasses({ status: 'active', page: 1, page_size: 100 })])
  if (requestId !== requestSeq || examId.value !== targetExamId) return false
  exam.value = examResponse.data
  classes.value = classResponse.data.items
  loadedBaseExamId = targetExamId
  return true
}

function resetExamState() {
  exam.value = null
  summary.value = {} as StatisticsSummary
  rankings.value = []
  segments.value = []
  filters.exam_subject_id = undefined
  loadedBaseExamId = null
}

async function loadStatistics() {
  const requestId = ++requestSeq
  const targetExamId = examId.value
  loading.value = true
  try {
    if (loadedBaseExamId !== targetExamId) {
      const loaded = await loadBase()
      if (!loaded) return
    }
    if (!ensureSubjectSelection()) {
      summary.value = {} as StatisticsSummary
      rankings.value = []
      segments.value = []
      return
    }
    const [summaryResponse, rankingResponse, segmentResponse] = await Promise.all([
      getExamStatisticsSummary(targetExamId, summaryParams()),
      getExamRankings(targetExamId, rankingParams()),
      getExamSegments(targetExamId, segmentParams()),
    ])
    if (requestId !== requestSeq || examId.value !== targetExamId) return
    summary.value = summaryResponse.data
    rankings.value = rankingResponse.data.items
    segments.value = segmentResponse.data.items
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === requestSeq) loading.value = false
  }
}

function ensureSubjectSelection() {
  if (!shouldShowSubject.value) return true
  if (filters.exam_subject_id) return true
  const firstSubject = subjectOptions.value[0]
  if (!firstSubject) return false
  filters.exam_subject_id = firstSubject.id
  return true
}

watch(
  () => examId.value,
  () => {
    resetExamState()
    loadStatistics()
  },
)

watch(
  () => [filters.included_statuses.join(','), filters.ranking_type, filters.segment_type, filters.exam_subject_id, filters.segment_step, filters.class_id],
  loadStatistics,
)

onMounted(() => {
  resetExamState()
  loadStatistics()
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

    <section class="gm-page-card">
      <div class="gm-filter-row gm-filter-row-wide">
        <el-select v-model="filters.included_statuses" multiple collapse-tags placeholder="计入状态">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.ranking_type" placeholder="排名类型">
          <el-option label="总分排名" value="total" />
          <el-option label="单科排名" value="subject" />
        </el-select>
        <el-select v-model="filters.segment_type" placeholder="分段类型">
          <el-option label="总分分段" value="total" />
          <el-option label="单科分段" value="subject" />
        </el-select>
        <el-select v-if="shouldShowSubject" v-model="filters.exam_subject_id" placeholder="排名/分段科目" clearable>
          <el-option v-for="subject in subjectOptions" :key="subject.id" :label="subject.course_name || '未命名科目'" :value="subject.id" />
        </el-select>
        <el-input-number v-model="filters.segment_step" :min="1" :max="100" controls-position="right" />
        <el-select v-model="filters.class_id" placeholder="排名/分段班级" clearable>
          <el-option v-for="classRecord in classes" :key="classRecord.id" :label="classRecord.name" :value="classRecord.id" />
        </el-select>
      </div>
    </section>

    <div class="gm-stats-grid">
      <section class="gm-page-card">
        <h2>核心指标</h2>
        <div class="gm-stat-list">
          <div v-for="item in overallItems" :key="item.label">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>
      <section class="gm-page-card">
        <h2>班级对比</h2>
        <div class="gm-stat-list">
          <div v-for="(item, index) in summary.class_comparison || []" :key="comparisonLabel(item, `班级 ${index + 1}`)">
            <span>{{ comparisonLabel(item, `班级 ${index + 1}`) }}</span>
            <strong>{{ item.average_score ?? '-' }}</strong>
          </div>
        </div>
      </section>
      <section class="gm-page-card">
        <h2>科目对比</h2>
        <div class="gm-stat-list">
          <div v-for="(item, index) in summary.subject_comparison || []" :key="comparisonLabel(item, `科目 ${index + 1}`)">
            <span>{{ comparisonLabel(item, `科目 ${index + 1}`) }}</span>
            <strong>{{ item.average_score ?? '-' }}</strong>
          </div>
        </div>
      </section>
      <section class="gm-page-card">
        <h2>分数段</h2>
        <el-table border class="gm-data-table" :data="segments" empty-text="暂无分段数据">
          <el-table-column prop="label" label="分段" />
          <el-table-column prop="start" label="起始分" width="100" />
          <el-table-column prop="end" label="结束分" width="100" />
          <el-table-column prop="count" label="人数" width="100" />
        </el-table>
      </section>
    </div>

    <section class="gm-page-card">
      <h2>排名</h2>
      <el-table border class="gm-data-table" :data="rankings" empty-text="暂无排名数据">
        <el-table-column prop="rank" label="排名" width="80" />
        <el-table-column prop="name" label="学生" />
        <el-table-column prop="student_no" label="学号" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="score" label="成绩" />
      </el-table>
    </section>

    <div class="gm-stats-grid">
      <section class="gm-page-card">
        <h2>缺考名单</h2>
        <el-table border class="gm-data-table" :data="summary.abnormal_lists?.absent || []" empty-text="暂无缺考记录">
          <el-table-column prop="name" label="学生" />
          <el-table-column prop="student_no" label="学号" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column prop="course_name" label="科目" />
        </el-table>
      </section>
      <section class="gm-page-card">
        <h2>缓考名单</h2>
        <el-table border class="gm-data-table" :data="summary.abnormal_lists?.deferred || []" empty-text="暂无缓考记录">
          <el-table-column prop="name" label="学生" />
          <el-table-column prop="student_no" label="学号" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column prop="course_name" label="科目" />
        </el-table>
      </section>
      <section class="gm-page-card">
        <h2>作弊名单</h2>
        <el-table border class="gm-data-table" :data="summary.abnormal_lists?.cheating || []" empty-text="暂无作弊记录">
          <el-table-column prop="name" label="学生" />
          <el-table-column prop="student_no" label="学号" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column prop="course_name" label="科目" />
        </el-table>
      </section>
      <section class="gm-page-card">
        <h2>免考名单</h2>
        <el-table border class="gm-data-table" :data="summary.abnormal_lists?.exempt || []" empty-text="暂无免考记录">
          <el-table-column prop="name" label="学生" />
          <el-table-column prop="student_no" label="学号" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column prop="course_name" label="科目" />
        </el-table>
      </section>
    </div>

    <section class="gm-page-card">
      <h2>缺失成绩名单</h2>
      <el-table border class="gm-data-table" :data="summary.missing_score_list || []" empty-text="暂无缺失成绩">
        <el-table-column prop="name" label="学生" />
        <el-table-column prop="student_no" label="学号" />
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="course_name" label="科目" />
      </el-table>
    </section>
  </section>
</template>
