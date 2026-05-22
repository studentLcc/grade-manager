<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listImports, type ImportBatchRecord } from '../api/imports'

const router = useRouter()
const loading = ref(false)
const records = ref<ImportBatchRecord[]>([])
const total = ref(0)
let requestSeq = 0
let resettingPage = false

const filters = reactive({
  import_type: '',
  status: '',
  page: 1,
  page_size: 20,
})

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

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

function typeLabel(type: string) {
  return typeLabels[type] || type || '-'
}

function statusLabel(status: string) {
  return statusLabels[status] || status || '-'
}

function importTime(row: ImportBatchRecord) {
  return row.imported_at || row.created_at || '-'
}

function targetLabel(row: ImportBatchRecord) {
  const parts = [row.target_class_name, row.target_exam_name, row.target_exam_subject_name].filter(Boolean)
  if (parts.length) return parts.join(' / ')
  if (row.target_exam_id) return `考试 ${row.target_exam_id}`
  if (row.target_class_id) return `班级 ${row.target_class_id}`
  return '-'
}

const displayRecords = computed(() =>
  records.value.map((record) => ({
    ...record,
    import_type_display: typeLabel(record.import_type),
    target_display: targetLabel(record),
    status_display: statusLabel(record.status),
    import_time_display: importTime(record),
  })),
)

async function loadRecords() {
  const requestId = ++requestSeq
  loading.value = true
  try {
    const { data } = await listImports(compactParams(filters))
    if (requestId !== requestSeq) return
    records.value = data.items
    total.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === requestSeq) loading.value = false
  }
}

watch(
  () => [filters.import_type, filters.status],
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
  () => [filters.page, filters.page_size],
  () => {
    if (resettingPage) resettingPage = false
    loadRecords()
  },
)

onMounted(loadRecords)
</script>

<template>
  <section class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>导入记录</h1>
        <p>查看学生导入和成绩导入批次，定位失败行并返回原流程处理。</p>
      </div>
    </div>

    <section class="gm-page-card">
      <div class="gm-filter-row">
        <el-select v-model="filters.import_type" placeholder="导入类型" clearable>
          <el-option label="学生导入" value="students" />
          <el-option label="成绩导入" value="scores" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable>
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="成功" value="success" />
          <el-option label="部分成功" value="partial_success" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="displayRecords" empty-text="暂无导入记录">
        <el-table-column label="导入类型" width="120">
          <template #default="{ row }">{{ row.import_type_display }}</template>
        </el-table-column>
        <el-table-column label="目标对象" min-width="180">
          <template #default="{ row }">{{ row.target_display }}</template>
        </el-table-column>
        <el-table-column prop="file_name" label="文件名" min-width="180" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">{{ row.status_display }}</template>
        </el-table-column>
        <el-table-column prop="success_count" label="成功数" width="100" />
        <el-table-column prop="failed_count" label="失败数" width="100" />
        <el-table-column label="导入时间" min-width="170">
          <template #default="{ row }">{{ row.import_time_display }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button text type="primary" @click="router.push(`/imports/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="gm-pagination">
        <el-pagination v-model:current-page="filters.page" v-model:page-size="filters.page_size" layout="prev, pager, next, sizes" :total="total" />
      </div>
    </section>
  </section>
</template>
