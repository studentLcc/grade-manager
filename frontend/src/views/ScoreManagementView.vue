<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listClasses, type ClassRecord } from '../api/classes'
import { listCourses, type CourseRecord } from '../api/courses'
import { listExams, type ExamRecord } from '../api/exams'
import { listScoreRecords, saveScores, type ScoreRecord, type ScoreStatus } from '../api/scores'

type EditableScoreRecord = ScoreRecord & {
  saving?: boolean
}

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const loading = ref(false)
const records = ref<EditableScoreRecord[]>([])
const examOptions = ref<ExamRecord[]>([])
const classOptions = ref<ClassRecord[]>([])
const courseOptions = ref<CourseRecord[]>([])
const total = ref(0)
let requestSeq = 0
let examOptionsRequestSeq = 0
let classOptionsRequestSeq = 0
let courseOptionsRequestSeq = 0
let resettingPage = false

const filters = reactive({
  keyword: '',
  exam_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
  course_id: undefined as number | undefined,
  status: 'active',
  score_status: '',
  page: 1,
  page_size: 20,
})

const examStatusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '归档', value: 'archived' },
]

const scoreStatusOptions: Array<{ label: string; value: ScoreStatus }> = [
  { label: '正常', value: 'normal' },
  { label: '缺考', value: 'absent' },
  { label: '缓考', value: 'deferred' },
  { label: '作弊', value: 'cheating' },
  { label: '免考', value: 'exempt' },
]

const examStatusLabelMap = new Map(examStatusOptions.map((item) => [item.value, item.label]))
const scoreStatusLabelMap = new Map(scoreStatusOptions.map((item) => [item.value, item.label]))
const abnormalStatuses = new Set<ScoreStatus>(['absent', 'deferred', 'cheating', 'exempt'])

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

function examStatusLabel(status: string) {
  return examStatusLabelMap.get(status) || '未知状态'
}

function scoreStatusLabel(status: string) {
  return scoreStatusLabelMap.get(status as ScoreStatus) || '未知状态'
}

async function fetchAllPages<T>(
  request: (params: Record<string, unknown>) => Promise<{ data: PageResponse<T> }>,
  params: Record<string, unknown>,
) {
  const pageSize = 100
  const first = await request(compactParams({ ...params, page: 1, page_size: pageSize }))
  const items = [...first.data.items]
  const totalItems = first.data.total
  const pageCount = Math.ceil(totalItems / pageSize)

  for (let page = 2; page <= pageCount; page += 1) {
    const { data } = await request(compactParams({ ...params, page, page_size: pageSize }))
    items.push(...data.items)
  }

  return items
}

async function loadRecords() {
  const requestId = ++requestSeq
  loading.value = true
  try {
    const { data } = await listScoreRecords(compactParams(filters))
    if (requestId !== requestSeq) return
    records.value = data.items.map((record) => ({ ...record, remark: record.remark || '' }))
    total.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === requestSeq) loading.value = false
  }
}

async function loadExamOptions() {
  const requestId = ++examOptionsRequestSeq
  try {
    const items = await fetchAllPages(listExams, { status: filters.status })
    if (requestId !== examOptionsRequestSeq) return
    examOptions.value = items
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function loadClassOptions() {
  const requestId = ++classOptionsRequestSeq
  try {
    const items = await fetchAllPages(listClasses, { status: 'active' })
    if (requestId !== classOptionsRequestSeq) return
    classOptions.value = items
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function loadCourseOptions() {
  const requestId = ++courseOptionsRequestSeq
  try {
    const items = await fetchAllPages(listCourses, { status: 'active' })
    if (requestId !== courseOptionsRequestSeq) return
    courseOptions.value = items
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function saveRecord(record: EditableScoreRecord) {
  if (record.saving || record.exam_status !== 'active') return
  record.saving = true
  const score = record.score_status === 'normal' ? record.score?.trim() || null : null
  try {
    const { data } = await saveScores(record.exam_id, [
      {
        exam_student_id: record.exam_student_id,
        exam_subject_id: record.exam_subject_id,
        score,
        score_status: record.score_status,
        remark: record.remark?.trim() || null,
      },
    ])
    if (data.failure_count > 0) {
      ElMessage.warning(data.failed_items[0]?.reason || '成绩保存失败')
      return
    }
    ElMessage.success('成绩已保存')
    await loadRecords()
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    record.saving = false
  }
}

function handleScoreStatusChange(record: EditableScoreRecord) {
  if (abnormalStatuses.has(record.score_status)) {
    record.score = null
  }
}

watch(
  () => [filters.keyword, filters.exam_id, filters.class_id, filters.course_id, filters.status, filters.score_status],
  () => {
    if (filters.page !== 1) {
      resettingPage = true
      filters.page = 1
      return
    }
    loadRecords()
  },
)

watch(
  () => filters.status,
  () => {
    filters.exam_id = undefined
    loadExamOptions()
  },
)

watch(
  () => [filters.page, filters.page_size],
  () => {
    if (resettingPage) {
      resettingPage = false
    }
    loadRecords()
  },
)

onMounted(async () => {
  await Promise.all([loadRecords(), loadExamOptions(), loadClassOptions(), loadCourseOptions()])
})
</script>

<template>
  <section class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>成绩管理</h1>
        <p>按学生和科目逐条维护成绩，快速筛选、复核并保存单条成绩记录。</p>
      </div>
    </div>

    <section class="gm-page-card">
      <div class="gm-filter-row gm-filter-row-wide">
        <el-input v-model="filters.keyword" placeholder="搜索考试、学生、学号或科目" clearable />
        <el-select v-model="filters.exam_id" placeholder="考试" clearable>
          <el-option v-for="exam in examOptions" :key="exam.id" :label="exam.name" :value="exam.id" />
        </el-select>
        <el-select v-model="filters.class_id" placeholder="班级" clearable>
          <el-option v-for="classRecord in classOptions" :key="classRecord.id" :label="classRecord.name" :value="classRecord.id" />
        </el-select>
        <el-select v-model="filters.course_id" placeholder="科目" clearable>
          <el-option v-for="course in courseOptions" :key="course.id" :label="course.course_name" :value="course.id" />
        </el-select>
        <el-select v-model="filters.score_status" placeholder="成绩状态" clearable>
          <el-option v-for="item in scoreStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="filters.status" placeholder="考试状态">
          <el-option v-for="item in examStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>

      <el-table v-loading="loading" border class="gm-data-table" :data="records" empty-text="暂无成绩">
        <el-table-column prop="exam_name" label="考试名称" min-width="140" />
        <el-table-column prop="term" label="学期" width="130" />
        <el-table-column prop="class_name" label="班级" width="110" />
        <el-table-column prop="student_no" label="学号" width="110" />
        <el-table-column prop="student_name" label="学生" width="100" />
        <el-table-column prop="course_name" label="科目" width="110" />
        <el-table-column prop="full_score" label="满分" width="90" />
        <el-table-column label="成绩" width="130">
          <template #default="{ row }">
            <el-input v-model="row.score" :disabled="row.score_status !== 'normal' || row.exam_status !== 'active'" placeholder="成绩" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-select v-model="row.score_status" :disabled="row.exam_status !== 'active'" @change="handleScoreStatusChange(row)">
              <el-option v-for="item in scoreStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <span class="gm-sr-only">{{ scoreStatusLabel(row.score_status) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="备注" min-width="140">
          <template #default="{ row }">
            <el-input v-model="row.remark" :disabled="row.exam_status !== 'active'" placeholder="备注" />
          </template>
        </el-table-column>
        <el-table-column label="考试状态" width="100">
          <template #default="{ row }">
            {{ examStatusLabel(row.exam_status) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button text type="primary" :loading="row.saving" :disabled="row.exam_status !== 'active'" @click="saveRecord(row)">保存</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="gm-pagination">
        <el-pagination v-model:current-page="filters.page" v-model:page-size="filters.page_size" layout="prev, pager, next, sizes" :total="total" />
      </div>
    </section>
  </section>
</template>
