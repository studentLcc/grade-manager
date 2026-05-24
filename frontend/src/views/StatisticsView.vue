<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listExams, type ExamRecord } from '../api/exams'

const router = useRouter()
const loading = ref(false)
const exams = ref<ExamRecord[]>([])
const total = ref(0)
let requestSeq = 0
let resettingPage = false

const filters = reactive({
  keyword: '',
  exam_type: '',
  term: '',
  status: 'active',
  page: 1,
  page_size: 20,
})

const typeOptions = [
  { label: '校级考试', value: 'school' },
  { label: '单元测验', value: 'quiz' },
  { label: '期中考试', value: 'midterm' },
  { label: '期末考试', value: 'final' },
]
const typeLabelMap = new Map(typeOptions.map((item) => [item.value, item.label]))

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

function examTypeLabel(examType: string | null) {
  return examType ? typeLabelMap.get(examType) || '其他考试' : '未设置'
}

function subjectSummary(exam: ExamRecord) {
  return exam.subjects.map((subject) => subject.course_name || '未命名科目').join('、') || '-'
}

function classSummary(exam: ExamRecord) {
  return exam.classes.map((classRecord) => classRecord.name).join('、') || '-'
}

async function loadExams() {
  const requestId = ++requestSeq
  loading.value = true
  try {
    const { data } = await listExams(compactParams(filters))
    if (requestId !== requestSeq) return
    exams.value = data.items
    total.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === requestSeq) loading.value = false
  }
}

watch(
  () => [filters.keyword, filters.exam_type, filters.term, filters.status],
  () => {
    if (filters.page !== 1) {
      resettingPage = true
      filters.page = 1
      return
    }
    loadExams()
  },
)

watch(
  () => [filters.page, filters.page_size],
  () => {
    if (resettingPage) resettingPage = false
    loadExams()
  },
)

onMounted(loadExams)
</script>

<template>
  <section class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>统计分析</h1>
        <p>选择考试进入后端统计结果页，查看排名、分数段、异常和缺失成绩。</p>
      </div>
      <el-button type="primary" @click="router.push('/exam-center')">进入考试中心</el-button>
    </div>

    <section class="gm-page-card">
      <div class="gm-filter-row gm-filter-row-wide">
        <el-input v-model="filters.keyword" placeholder="搜索考试名称" clearable />
        <el-select v-model="filters.exam_type" placeholder="考试类型" clearable>
          <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input v-model="filters.term" placeholder="学期" clearable />
      </div>

      <el-table v-loading="loading" border class="gm-data-table" :data="exams" empty-text="暂无可查看统计的考试">
        <el-table-column prop="name" label="考试名称" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">{{ examTypeLabel(row.exam_type) }}</template>
        </el-table-column>
        <el-table-column prop="term" label="学期" width="140" />
        <el-table-column label="班级" min-width="160">
          <template #default="{ row }">{{ classSummary(row) }}</template>
        </el-table-column>
        <el-table-column label="科目" min-width="160">
          <template #default="{ row }">{{ subjectSummary(row) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="130">
          <template #default="{ row }">
            <el-button text type="primary" @click="router.push(`/exam-center/${row.id}/statistics`)">查看统计</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="gm-pagination">
        <el-pagination v-model:current-page="filters.page" v-model:page-size="filters.page_size" layout="prev, pager, next, sizes" :total="total" />
      </div>
    </section>
  </section>
</template>
