<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { UploadRequestOptions } from 'element-plus'
import ImportResultPanel from '../imports/ImportResultPanel.vue'
import ImportUploadDialog from '../imports/ImportUploadDialog.vue'
import { downloadBlob } from '../../utils/download'
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
  className?: string | null
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  imported: [result: ScoreImportResult]
}>()

const result = ref<ScoreImportResult | null>(null)
const errors = ref<ImportErrorRecord[]>([])
const uploading = ref(false)
const overwriteExisting = ref(false)
let uploadSequence = 0
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})
const importScope = computed(() => props.className || (props.classId ? `班级 ${props.classId}` : '全部班级'))

async function downloadTemplate() {
  if (props.disabled) return
  try {
    const { data } = await downloadScoreTemplate(props.examId, props.classId || undefined)
    downloadBlob(data, `exam-${props.examId}-score-template.xlsx`)
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
    const { data } = await importScores(uploadExamId, options.file, overwriteExisting.value)
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
  <ImportUploadDialog
    v-model="visible"
    v-model:option-value="overwriteExisting"
    title="导入成绩"
    context-label="导入范围"
    :context-value="importScope"
    option-label="覆盖已有成绩"
    :download-disabled="disabled"
    :option-disabled="disabled || uploading"
    :upload-disabled="disabled || uploading"
    :uploading="uploading"
    upload-idle-text="拖拽成绩文件到这里"
    :http-request="uploadScoreFile"
    @download="downloadTemplate"
  >
    <ImportResultPanel :result="result" />

    <el-table v-if="errors.length" border class="gm-data-table" :data="errors" empty-text="暂无错误">
      <el-table-column prop="row_number" label="行号" width="90" />
      <el-table-column prop="field" label="字段" width="120" />
      <el-table-column prop="raw_value" label="原始值" width="140" />
      <el-table-column prop="reason" label="原因" />
    </el-table>
  </ImportUploadDialog>
</template>
