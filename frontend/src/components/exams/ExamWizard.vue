<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createExam, type ExamCreatePayload, type ExamRecord } from '../../api/exams'
import { listClasses, type ClassRecord } from '../../api/classes'
import { listCourses, type CourseRecord } from '../../api/courses'
import ExamBasicStep from './ExamBasicStep.vue'
import ExamClassesStep from './ExamClassesStep.vue'
import ExamSubjectsStep from './ExamSubjectsStep.vue'
import ExamConfirmStep from './ExamConfirmStep.vue'

interface ExamSubjectForm {
  course_id: number | null
  full_score: string
  pass_score: string
  excellent_score: string
  exam_date?: string
  remark: string
}

export interface ExamWizardState {
  basic: { name: string; exam_type: string; term: string; remark: string }
  class_ids: number[]
  subjects: ExamSubjectForm[]
}

const emit = defineEmits<{
  created: [exam: ExamRecord]
}>()

const activeStep = ref(0)
const classes = ref<ClassRecord[]>([])
const courses = ref<CourseRecord[]>([])
const saving = ref(false)

const state = reactive<ExamWizardState>({
  basic: { name: '', exam_type: '', term: '', remark: '' },
  class_ids: [],
  subjects: [{ course_id: null, full_score: '100.00', pass_score: '60.00', excellent_score: '90.00', exam_date: '', remark: '' }],
})

const stepTitles = ['基本信息', '参与班级', '考试科目', '确认创建']
const isLastStep = computed(() => activeStep.value === stepTitles.length - 1)

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

async function fetchAllPages<T>(request: (params: Record<string, unknown>) => Promise<{ data: { items: T[]; total: number } }>) {
  const pageSize = 100
  const first = await request({ page: 1, page_size: pageSize, status: 'active' })
  const items = [...first.data.items]
  const pageCount = Math.ceil(first.data.total / pageSize)
  for (let page = 2; page <= pageCount; page += 1) {
    const { data } = await request(compactParams({ page, page_size: pageSize, status: 'active' }))
    items.push(...data.items)
  }
  return items
}

function thresholdValid(subject: ExamSubjectForm) {
  const fullScore = Number(subject.full_score)
  const passScore = Number(subject.pass_score)
  const excellentScore = Number(subject.excellent_score)
  return [fullScore, passScore, excellentScore].every(Number.isFinite) && 0 <= passScore && passScore <= excellentScore && excellentScore <= fullScore
}

function validateCurrentStep() {
  if (activeStep.value === 0 && !state.basic.name.trim()) {
    ElMessage.warning('请输入考试名称')
    return false
  }
  if (activeStep.value === 1 && state.class_ids.length === 0) {
    ElMessage.warning('请选择参与班级')
    return false
  }
  if (activeStep.value >= 2) {
    if (state.subjects.length === 0) {
      ElMessage.warning('请添加考试科目')
      return false
    }
    const courseIds = state.subjects.map((subject) => subject.course_id).filter((courseId): courseId is number => Boolean(courseId))
    if (courseIds.length !== state.subjects.length) {
      ElMessage.warning('请选择每个考试科目')
      return false
    }
    if (new Set(courseIds).size !== courseIds.length) {
      ElMessage.warning('考试科目不能重复')
      return false
    }
    if (state.subjects.some((subject) => !subject.full_score || !subject.pass_score || !subject.excellent_score || !thresholdValid(subject))) {
      ElMessage.warning('分数阈值必须满足 0 <= 及格分 <= 优秀分 <= 满分')
      return false
    }
  }
  return true
}

function nextStep() {
  if (!validateCurrentStep()) return
  if (!isLastStep.value) activeStep.value += 1
}

function previousStep() {
  if (activeStep.value > 0) activeStep.value -= 1
}

function buildPayload(): ExamCreatePayload {
  return {
    name: state.basic.name.trim(),
    exam_type: state.basic.exam_type || null,
    term: state.basic.term || null,
    remark: state.basic.remark?.trim() || null,
    class_ids: [...state.class_ids],
    subjects: state.subjects.map((subject) => ({
      course_id: Number(subject.course_id),
      full_score: subject.full_score,
      pass_score: subject.pass_score,
      excellent_score: subject.excellent_score,
      exam_date: subject.exam_date || null,
      remark: subject.remark?.trim() || null,
    })),
  }
}

async function submit() {
  if (!validateCurrentStep()) return
  saving.value = true
  try {
    const { data } = await createExam(buildPayload())
    emit('created', data)
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    const [classItems, courseItems] = await Promise.all([fetchAllPages(listClasses), fetchAllPages(listCourses)])
    classes.value = classItems
    courses.value = courseItems
  } catch {
    // Global http interceptor shows the user-facing error.
  }
})
</script>

<template>
  <section class="gm-wizard">
    <span class="gm-sr-only">{{ stepTitles.join(' ') }}</span>
    <el-steps :active="activeStep" finish-status="success" align-center>
      <el-step v-for="title in stepTitles" :key="title" :title="title" />
    </el-steps>

    <div class="gm-wizard-panel">
      <ExamBasicStep v-if="activeStep === 0" v-model="state.basic" />
      <ExamClassesStep v-else-if="activeStep === 1" v-model="state.class_ids" :classes="classes" />
      <ExamSubjectsStep v-else-if="activeStep === 2" v-model="state.subjects" :courses="courses" />
      <ExamConfirmStep v-else :basic="state.basic" :class-ids="state.class_ids" :subjects="state.subjects" :classes="classes" :courses="courses" />
    </div>

    <div class="gm-wizard-actions">
      <el-button :disabled="activeStep === 0" @click="previousStep">上一步</el-button>
      <el-button v-if="!isLastStep" type="primary" @click="nextStep">下一步</el-button>
      <el-button v-else type="primary" :loading="saving" @click="submit">确认创建</el-button>
    </div>
  </section>
</template>
