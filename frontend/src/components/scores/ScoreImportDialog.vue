<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { UploadRequestOptions } from 'element-plus'
import {
  downloadScoreTemplate,
  importScores,
  listScoreImportErrors,
  type ImportErrorRecord,
  type ScoreImportResult,
} from '../../api/scores'

const props = defineProps<{
  modelValue: boolean
  examId: number
  classId?: number | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  imported: [result: ScoreImportResult]
}>()

const result = ref<ScoreImportResult | null>(null)
const errors = ref<ImportErrorRecord[]>([])
const uploading = ref(false)
let uploadSequence = 0
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const importStatusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  success: '成功',
  partial_success: '部分成功',
  failed: '失败',
}

function statusLabel(status: string) {
  return importStatusLabels[status] || '未知状态'
}

async function downloadTemplate() {
  if (props.disabled) return
  try {
    const { data } = await downloadScoreTemplate(props.examId, props.classId || undefined)
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = `exam-${props.examId}-score-template.xlsx`
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    // Global http interceptor shows the user-facing error.
  }
}

async function uploadScoreFile(options: UploadRequestOptions) {
  if (props.disabled) return
  const sequence = ++uploadSequence
  const uploadExamId = props.examId
  uploading.value = true
  result.value = null
  errors.value = []
  try {
    const { data } = await importScores(uploadExamId, options.file)
    if (sequence !== uploadSequence || uploadExamId !== props.examId) return
    result.value = data
    emit('imported', data)
    if (data.batch_id && data.failed_count > 0) {
      try {
        const errorResponse = await listScoreImportErrors(data.batch_id, { page: 1, page_size: 100 })
        if (sequence !== uploadSequence || uploadExamId !== props.examId) return
        errors.value = errorResponse.data.items
      } catch {
        errors.value = []
      }
    }
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (sequence === uploadSequence) uploading.value = false
  }
}

watch(
  () => props.examId,
  () => {
    uploadSequence += 1
    result.value = null
    errors.value = []
    uploading.value = false
  },
)
</script>

<template>
  <el-dialog v-model="visible" title="导入成绩" width="680px">
    <div class="gm-import-actions">
      <el-button :disabled="disabled" @click="downloadTemplate">下载模板</el-button>
      <el-upload :http-request="uploadScoreFile" :disabled="disabled" :show-file-list="false" name="file">
        <el-button type="primary" :loading="uploading" :disabled="disabled">上传成绩文件</el-button>
      </el-upload>
    </div>

    <section v-if="result" class="gm-import-result">
      <div>
        <span>导入状态</span>
        <strong>{{ statusLabel(result.status) }}</strong>
      </div>
      <div>
        <span>成功</span>
        <strong>{{ result.success_count }}</strong>
      </div>
      <div>
        <span>失败</span>
        <strong>{{ result.failed_count }}</strong>
      </div>
      <RouterLink v-if="result.batch_id" class="gm-import-link" :to="`/imports/${result.batch_id}`">查看导入详情</RouterLink>
    </section>

    <el-table v-if="errors.length" :data="errors" empty-text="暂无错误">
      <el-table-column prop="row_number" label="行号" width="90" />
      <el-table-column prop="field" label="字段" width="120" />
      <el-table-column prop="raw_value" label="原始值" width="140" />
      <el-table-column prop="reason" label="原因" />
    </el-table>
  </el-dialog>
</template>
