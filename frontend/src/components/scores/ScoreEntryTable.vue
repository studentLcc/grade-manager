<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { ScoreFailureItem, ScoreSaveItem, ScoreSheetScore, ScoreStatus } from '../../api/scores'

interface ScoreTableStudent {
  exam_student_id: number
  student_id?: number
  class_id: number
  student_no: string
  name: string
  status?: string
}

interface ScoreTableSubject {
  exam_subject_id: number
  course_id?: number
  course_name: string | null
  full_score: string
  pass_score?: string | null
  excellent_score?: string | null
  status?: string
}

interface ScoreDraft {
  exam_student_id: number
  exam_subject_id: number
  score: number | null
  score_status: ScoreStatus
  remark: string | null
}

const props = defineProps<{
  mode: 'focused' | 'whole'
  students: ScoreTableStudent[]
  subjects: ScoreTableSubject[]
  scores: ScoreSheetScore[]
  failedItems: ScoreFailureItem[]
  savedItems?: ScoreSaveItem[]
  disabled?: boolean
  classId?: number | null
  subjectId?: number | null
}>()

const emit = defineEmits<{
  change: [items: ScoreSaveItem[]]
}>()

const scoreStatusOptions: Array<{ label: string; value: ScoreStatus }> = [
  { label: '正常', value: 'normal' },
  { label: '缺考', value: 'absent' },
  { label: '缓考', value: 'deferred' },
  { label: '作弊', value: 'cheating' },
  { label: '免考', value: 'exempt' },
]

const baselineScores = reactive(new Map<string, ScoreDraft>())
const dirtyScores = reactive(new Map<string, ScoreDraft>())

const visibleStudents = computed(() =>
  props.mode === 'whole' ? props.students : props.students.filter((student) => !props.classId || student.class_id === props.classId),
)
const visibleSubjects = computed(() =>
  props.mode === 'focused' && props.subjectId
    ? props.subjects.filter((subject) => subject.exam_subject_id === props.subjectId)
    : props.subjects,
)

function scoreKey(examStudentId: number, examSubjectId: number) {
  return `${examStudentId}:${examSubjectId}`
}

function normalizeScore(score: string | number | null | undefined) {
  if (score === null || score === undefined || score === '') return null
  const numeric = Number(score)
  return Number.isFinite(numeric) ? numeric : null
}

function draftFromScore(examStudentId: number, examSubjectId: number, score?: ScoreSheetScore): ScoreDraft {
  return {
    exam_student_id: examStudentId,
    exam_subject_id: examSubjectId,
    score: normalizeScore(score?.score),
    score_status: score?.score_status ?? 'normal',
    remark: score?.remark ?? null,
  }
}

function sameDraft(left: ScoreDraft, right: ScoreDraft) {
  return left.score === right.score && left.score_status === right.score_status && (left.remark || null) === (right.remark || null)
}

function ensureDraft(examStudentId: number, examSubjectId: number): ScoreDraft {
  const key = scoreKey(examStudentId, examSubjectId)
  return dirtyScores.get(key) || baselineScores.get(key) || draftFromScore(examStudentId, examSubjectId)
}

function setDraft(draft: ScoreDraft) {
  const key = scoreKey(draft.exam_student_id, draft.exam_subject_id)
  const baseline = baselineScores.get(key) || draftFromScore(draft.exam_student_id, draft.exam_subject_id)
  if (sameDraft(draft, baseline)) {
    dirtyScores.delete(key)
  } else {
    dirtyScores.set(key, draft)
  }
}

function updateScore(examStudentId: number, examSubjectId: number, score: number | null | undefined) {
  if (props.disabled) return
  const draft = ensureDraft(examStudentId, examSubjectId)
  const next = { ...draft, score: normalizeScore(score) }
  if (next.score !== null) next.score_status = 'normal'
  setDraft(next)
  emitChange()
}

function updateStatus(examStudentId: number, examSubjectId: number, status: ScoreStatus) {
  if (props.disabled) return
  const draft = ensureDraft(examStudentId, examSubjectId)
  const next = { ...draft, score_status: status }
  if (status !== 'normal') next.score = null
  setDraft(next)
  emitChange()
}

function failureFor(examStudentId: number, examSubjectId: number) {
  return props.failedItems.find((item) => item.exam_student_id === examStudentId && item.exam_subject_id === examSubjectId)
}

function cellClass(examStudentId: number, examSubjectId: number) {
  return failureFor(examStudentId, examSubjectId) ? 'gm-score-cell has-error' : 'gm-score-cell'
}

function emitChange() {
  emit('change', Array.from(dirtyScores.values()).map(toSaveItem))
}

function toSaveItem(draft: ScoreDraft): ScoreSaveItem {
  return {
    exam_student_id: draft.exam_student_id,
    exam_subject_id: draft.exam_subject_id,
    score: draft.score === null ? null : String(draft.score),
    score_status: draft.score_status,
    remark: draft.remark,
  }
}

function resetDrafts() {
  baselineScores.clear()
  dirtyScores.clear()
  const existingScores = new Map(props.scores.map((score) => [scoreKey(score.exam_student_id, score.exam_subject_id), score]))
  props.students.forEach((student) => {
    props.subjects.forEach((subject) => {
      const key = scoreKey(student.exam_student_id, subject.exam_subject_id)
      baselineScores.set(key, draftFromScore(student.exam_student_id, subject.exam_subject_id, existingScores.get(key)))
    })
  })
  emitChange()
}

watch(() => [props.students, props.subjects, props.scores], resetDrafts, { immediate: true, deep: true })

watch(
  () => props.savedItems,
  (items) => {
    if (!items?.length) return
    items.forEach((item) => {
      const key = scoreKey(item.exam_student_id, item.exam_subject_id)
      const draft = draftFromScore(item.exam_student_id, item.exam_subject_id, {
        exam_student_id: item.exam_student_id,
        exam_subject_id: item.exam_subject_id,
        score: item.score,
        score_status: item.score_status,
        remark: item.remark ?? null,
      })
      baselineScores.set(key, draft)
      dirtyScores.delete(key)
    })
    emitChange()
  },
  { deep: true },
)
</script>

<template>
  <div class="gm-score-table">
    <span class="gm-sr-only">
      {{ visibleStudents.map((student) => `${student.student_no} ${student.name}`).join(' ') }}
      {{ visibleSubjects.map((subject) => subject.course_name || '未命名科目').join(' ') }}
    </span>
    <el-table border class="gm-data-table" :data="visibleStudents" empty-text="暂无考试学生">
      <el-table-column prop="student_no" label="学号" width="110" />
      <el-table-column prop="name" label="学生" width="110" />
      <el-table-column v-for="subject in visibleSubjects" :key="subject.exam_subject_id" :label="subject.course_name || '未命名科目'" min-width="210">
        <template #default="{ row }">
          <div :class="cellClass(row.exam_student_id, subject.exam_subject_id)">
            <span class="gm-score-subject">{{ subject.course_name || '未命名科目' }}</span>
            <el-input-number
              :model-value="ensureDraft(row.exam_student_id, subject.exam_subject_id).score"
              :min="0"
              :max="Number(subject.full_score)"
              :disabled="disabled || ensureDraft(row.exam_student_id, subject.exam_subject_id).score_status !== 'normal'"
              controls-position="right"
              @update:model-value="updateScore(row.exam_student_id, subject.exam_subject_id, $event)"
            />
            <el-select
              :model-value="ensureDraft(row.exam_student_id, subject.exam_subject_id).score_status"
              :disabled="disabled"
              @update:model-value="updateStatus(row.exam_student_id, subject.exam_subject_id, $event)"
            >
              <el-option v-for="item in scoreStatusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <small v-if="failureFor(row.exam_student_id, subject.exam_subject_id)">{{ failureFor(row.exam_student_id, subject.exam_subject_id)?.reason }}</small>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
