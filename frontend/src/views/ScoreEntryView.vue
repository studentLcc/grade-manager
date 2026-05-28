<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getScoreSheet,
  saveScores,
  type ScoreFailureItem,
  type ScoreSaveItem,
  type ScoreSheet,
} from '../api/scores'
import TableSurface from '../components/common/TableSurface.vue'
import ScoreEntryTable from '../components/scores/ScoreEntryTable.vue'
import ScoreImportDialog from '../components/scores/ScoreImportDialog.vue'

const route = useRoute()
const router = useRouter()
const examId = computed(() => Number(route.params.id))
const sheet = ref<ScoreSheet | null>(null)
const loading = ref(false)
const saving = ref(false)
const importVisible = ref(route.query.import === '1')
const failedItems = ref<ScoreFailureItem[]>([])
const dirtyItems = ref<ScoreSaveItem[]>([])
const savedItems = ref<ScoreSaveItem[]>([])
let loadSequence = 0
let saveSequence = 0
const isExamActive = computed(() => sheet.value?.exam.status === 'active')

const filters = reactive({
  class_id: undefined as number | undefined,
  subject_id: undefined as number | undefined,
  mode: 'focused' as 'focused' | 'whole',
})

const modeOptions = [
  { label: '聚焦录入', value: 'focused' },
  { label: '整场总览', value: 'whole' },
]
const selectedClassName = computed(() => {
  if (!filters.class_id) return ''
  return sheet.value?.classes.find((classRecord) => classRecord.id === filters.class_id)?.name || `班级 ${filters.class_id}`
})

async function loadSheet(id = examId.value) {
  const sequence = ++loadSequence
  saveSequence += 1
  const previousClassId = sheet.value?.exam.id === id ? filters.class_id : undefined
  const previousSubjectId = sheet.value?.exam.id === id ? filters.subject_id : undefined
  if (!Number.isFinite(id) || id <= 0) {
    sheet.value = null
    failedItems.value = []
    dirtyItems.value = []
    savedItems.value = []
    loading.value = false
    saving.value = false
    return
  }
  loading.value = true
  saving.value = false
  sheet.value = null
  failedItems.value = []
  dirtyItems.value = []
  savedItems.value = []
  try {
    const { data } = await getScoreSheet(id)
    if (sequence !== loadSequence) return
    sheet.value = data
    filters.class_id = data.classes.some((classRecord) => classRecord.id === previousClassId) ? previousClassId : data.classes[0]?.id
    filters.subject_id = data.subjects.some((subject) => subject.exam_subject_id === previousSubjectId) ? previousSubjectId : data.subjects[0]?.exam_subject_id
    failedItems.value = []
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

function handleTableChange(items: ScoreSaveItem[]) {
  dirtyItems.value = items
}

function reloadCurrentSheet() {
  return loadSheet(examId.value)
}

async function bulkSave() {
  if (!sheet.value || !isExamActive.value || dirtyItems.value.length === 0) return
  const savingExamId = examId.value
  const sequence = ++saveSequence
  saving.value = true
  try {
    const submittedItems = [...dirtyItems.value]
    const { data } = await saveScores(savingExamId, submittedItems)
    if (sequence !== saveSequence || savingExamId !== examId.value) return
    failedItems.value = data.failed_items || []
    if (data.failure_count > 0) {
      const failedKeys = new Set(failedItems.value.map((item) => `${item.exam_student_id}:${item.exam_subject_id}`))
      const failedIndexes = new Set(failedItems.value.map((item) => item.index).filter((index) => index !== undefined))
      dirtyItems.value = submittedItems.filter((item, index) => failedKeys.has(`${item.exam_student_id}:${item.exam_subject_id}`) || failedIndexes.has(index))
      savedItems.value = submittedItems.filter((item, index) => !failedKeys.has(`${item.exam_student_id}:${item.exam_subject_id}`) && !failedIndexes.has(index))
      ElMessage.warning('部分成绩保存失败，请查看单元格提示')
    } else {
      ElMessage.success('成绩已保存')
      await loadSheet(examId.value)
    }
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (sequence === saveSequence) saving.value = false
  }
}

watch(
  () => route.query.import,
  (value) => {
    importVisible.value = value === '1'
  },
)

watch(examId, loadSheet, { immediate: true })
</script>

<template>
  <section v-loading="loading" class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>{{ sheet?.exam.name || '成绩录入' }}</h1>
        <p>{{ sheet?.exam.term || '未设置学期' }}</p>
      </div>
      <div class="gm-toolbar">
        <el-button :disabled="!isExamActive" @click="importVisible = true">导入成绩</el-button>
        <el-button type="primary" :loading="saving" :disabled="!isExamActive" @click="bulkSave">批量保存</el-button>
      </div>
    </div>

    <section class="gm-page-card">
      <TableSurface>
        <template #toolbar>
          <div class="gm-filter-row gm-filter-row-wide">
            <el-select v-model="filters.class_id" placeholder="班级" clearable>
              <el-option v-for="classRecord in sheet?.classes || []" :key="classRecord.id" :label="classRecord.name" :value="classRecord.id" />
            </el-select>
            <el-select v-model="filters.subject_id" placeholder="科目" clearable>
              <el-option
                v-for="subject in sheet?.subjects || []"
                :key="subject.exam_subject_id"
                :label="subject.course_name || '未命名科目'"
                :value="subject.exam_subject_id"
              />
            </el-select>
            <el-segmented v-model="filters.mode" :options="modeOptions" />
            <el-button @click="router.push(`/exam-center/${examId}`)">考试详情</el-button>
          </div>
        </template>

        <ScoreEntryTable
          v-if="sheet"
          :mode="filters.mode"
          :class-id="filters.class_id"
          :subject-id="filters.subject_id"
          :students="sheet.students"
          :subjects="sheet.subjects"
          :scores="sheet.scores"
          :failed-items="failedItems"
          :saved-items="savedItems"
          :disabled="saving || !isExamActive"
          @change="handleTableChange"
        />
        <el-empty v-else description="暂无成绩单" />
      </TableSurface>
    </section>

    <ScoreImportDialog
      v-if="examId"
      v-model="importVisible"
      :exam-id="examId"
      :class-id="filters.class_id"
      :class-name="selectedClassName"
      :disabled="!isExamActive"
      @imported="reloadCurrentSheet"
    />
  </section>
</template>
