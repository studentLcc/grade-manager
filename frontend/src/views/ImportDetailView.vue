<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getImportBatch, listImportErrors, type ImportBatchRecord, type ImportErrorRecord } from '../api/imports'
import TablePagination from '../components/common/TablePagination.vue'
import TableSurface from '../components/common/TableSurface.vue'
import ImportErrorTable from '../components/imports/ImportErrorTable.vue'

const route = useRoute()
const router = useRouter()
const batchId = computed(() => Number(route.params.id))
const loading = ref(false)
const batch = ref<ImportBatchRecord | null>(null)
const errors = ref<ImportErrorRecord[]>([])
const total = ref(0)
const page = reactive({ page: 1, page_size: 20 })
let requestSeq = 0

const typeLabels: Record<string, string> = {
  students: '学生导入',
  scores: '成绩导入',
  student: '学生导入',
  score: '成绩导入',
}

const statusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  success: '成功',
  partial_success: '部分成功',
  failed: '失败',
  completed: '已完成',
  partial_failed: '部分失败',
}

function typeLabel(type: string | undefined) {
  return type ? typeLabels[type] || type : '-'
}

function statusLabel(status: string | undefined) {
  return status ? statusLabels[status] || status : '-'
}

function importTime(record: ImportBatchRecord | null) {
  return record?.imported_at || record?.created_at || '-'
}

function targetLabel(record: ImportBatchRecord | null) {
  if (!record) return '-'
  const parts = [record.target_class_name, record.target_exam_name, record.target_exam_subject_name].filter(Boolean)
  if (parts.length) return parts.join(' / ')
  if (record.target_exam_id) return `考试 ${record.target_exam_id}`
  if (record.target_class_id) return `班级 ${record.target_class_id}`
  return '-'
}

function workflowLink(record: ImportBatchRecord | null) {
  if (!record) return null
  if (record.target_exam_id) return `/exam-center/${record.target_exam_id}/scores?import=1`
  if (record.target_class_id) return `/classes-students?class_id=${record.target_class_id}`
  return null
}

async function loadDetail() {
  const requestId = ++requestSeq
  const targetBatchId = batchId.value
  loading.value = true
  try {
    const [batchResponse, errorResponse] = await Promise.all([getImportBatch(targetBatchId), listImportErrors(targetBatchId, page)])
    if (requestId !== requestSeq || batchId.value !== targetBatchId) return
    batch.value = batchResponse.data
    errors.value = errorResponse.data.items
    total.value = errorResponse.data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === requestSeq) loading.value = false
  }
}

function resetDetailState() {
  page.page = 1
  batch.value = null
  errors.value = []
  total.value = 0
}

watch(
  batchId,
  () => {
    resetDetailState()
    loadDetail()
  },
  { immediate: true },
)
</script>

<template>
  <section v-loading="loading" class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>导入详情</h1>
        <p>{{ batch?.file_name || '查看导入批次元数据和失败原因。' }}</p>
      </div>
      <div class="gm-toolbar">
        <el-button v-if="workflowLink(batch)" type="primary" @click="router.push(workflowLink(batch)!)">返回原流程</el-button>
        <el-button @click="router.push('/imports')">返回列表</el-button>
      </div>
    </div>

    <section class="gm-page-card">
      <h2>批次信息</h2>
      <div class="gm-detail-grid">
        <div><span>导入类型</span><strong>{{ typeLabel(batch?.import_type) }}</strong></div>
        <div><span>目标对象</span><strong>{{ targetLabel(batch) }}</strong></div>
        <div><span>状态</span><strong>{{ statusLabel(batch?.status) }}</strong></div>
        <div><span>成功数</span><strong>{{ batch?.success_count ?? 0 }}</strong></div>
        <div><span>失败数</span><strong>{{ batch?.failed_count ?? 0 }}</strong></div>
        <div><span>导入时间</span><strong>{{ importTime(batch) }}</strong></div>
      </div>
    </section>

    <section class="gm-page-card">
      <div class="gm-section-title">
        <h2>行级错误</h2>
      </div>
      <TableSurface>
        <template #toolbar>
          <div class="gm-filter-row">
            <span>失败行 {{ total }} 条</span>
          </div>
        </template>

        <ImportErrorTable :errors="errors" />

        <template #pagination>
          <TablePagination v-model:current-page="page.page" v-model:page-size="page.page_size" :total="total" @change="loadDetail" />
        </template>
      </TableSurface>
    </section>
  </section>
</template>
