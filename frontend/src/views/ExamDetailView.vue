<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getExam, type ExamRecord } from '../api/exams'
import { getScoreSheet, type ScoreSheet } from '../api/scores'

const route = useRoute()
const router = useRouter()
const exam = ref<ExamRecord | null>(null)
const scoreSheet = ref<ScoreSheet | null>(null)
const loading = ref(false)
const examId = computed(() => Number(route.params.id))
let loadSequence = 0
const scoreSummary = computed(() => {
  const sheet = scoreSheet.value
  if (!sheet) return { entered: 0, missing: 0, abnormal: 0, total: 0 }
  const total = sheet.students.length * sheet.subjects.length
  const entered = sheet.scores.length
  const abnormal = sheet.scores.filter((score) => score.score_status !== 'normal').length
  return { entered, missing: Math.max(total - entered, 0), abnormal, total }
})

const examTypeLabels: Record<string, string> = {
  school: '校级考试',
  quiz: '单元测验',
  midterm: '期中考试',
  final: '期末考试',
}
const statusLabels: Record<string, string> = {
  active: '启用',
  inactive: '停用',
  archived: '归档',
}

function examTypeLabel(examType: string | null | undefined) {
  return examType ? examTypeLabels[examType] || '其他考试' : '未设置'
}

function statusLabel(status: string | undefined) {
  return status ? statusLabels[status] || '未知状态' : '-'
}

async function loadExam(id: number) {
  const sequence = ++loadSequence
  if (!Number.isFinite(id) || id <= 0) {
    exam.value = null
    scoreSheet.value = null
    loading.value = false
    return
  }
  loading.value = true
  exam.value = null
  scoreSheet.value = null
  try {
    const [examResponse, sheetResponse] = await Promise.all([getExam(id), getScoreSheet(id)])
    if (sequence !== loadSequence) return
    exam.value = examResponse.data
    scoreSheet.value = sheetResponse.data
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

watch(examId, loadExam, { immediate: true })
</script>

<template>
  <section v-loading="loading" class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>{{ exam?.name || '考试详情' }}</h1>
        <p>{{ exam?.term || '未设置学期' }}</p>
      </div>
      <div class="gm-toolbar">
        <el-button type="primary" @click="router.push(`/exam-center/${examId}/scores`)">录入成绩</el-button>
        <el-button @click="router.push(`/exam-center/${examId}/scores?import=1`)">导入成绩</el-button>
        <el-button @click="router.push(`/exam-center/${examId}/statistics`)">查看统计</el-button>
      </div>
    </div>

    <section class="gm-page-card">
      <h2>基本信息</h2>
      <div class="gm-detail-grid">
        <div><span>考试类型</span><strong>{{ examTypeLabel(exam?.exam_type) }}</strong></div>
        <div><span>状态</span><strong>{{ statusLabel(exam?.status) }}</strong></div>
        <div><span>备注</span><strong>{{ exam?.remark || '-' }}</strong></div>
      </div>
    </section>

    <section class="gm-page-card">
      <h2>参与班级</h2>
      <div class="gm-chip-row">
        <span v-for="classRecord in exam?.classes || []" :key="classRecord.id" class="gm-chip">{{ classRecord.name }}</span>
      </div>
    </section>

    <section class="gm-page-card">
      <h2>考试科目</h2>
      <el-table :data="exam?.subjects || []" empty-text="暂无科目">
        <el-table-column prop="course_name" label="科目" />
        <el-table-column prop="full_score" label="满分" width="100" />
        <el-table-column prop="pass_score" label="及格分" width="100" />
        <el-table-column prop="excellent_score" label="优秀分" width="100" />
        <el-table-column prop="exam_date" label="考试日期" width="140" />
        <el-table-column prop="remark" label="备注" />
      </el-table>
    </section>

    <section class="gm-page-card">
      <h2>成绩录入状态</h2>
      <div class="gm-detail-grid">
        <div><span>应录入</span><strong>{{ scoreSummary.total }}</strong></div>
        <div><span>已录入</span><strong>{{ scoreSummary.entered }}</strong></div>
        <div><span>未录入</span><strong>{{ scoreSummary.missing }}</strong></div>
        <div><span>异常状态</span><strong>{{ scoreSummary.abnormal }}</strong></div>
      </div>
    </section>
  </section>
</template>
