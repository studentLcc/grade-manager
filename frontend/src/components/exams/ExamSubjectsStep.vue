<script setup lang="ts">
import { Plus, Delete } from '@element-plus/icons-vue'
import type { CourseRecord } from '../../api/courses'

interface ExamSubjectForm {
  course_id: number | null
  full_score: string
  pass_score: string
  excellent_score: string
  exam_date?: string
  remark: string
}

const props = defineProps<{
  modelValue: ExamSubjectForm[]
  courses: CourseRecord[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ExamSubjectForm[]]
}>()

function updateSubject(index: number, patch: Partial<ExamSubjectForm>) {
  const next = props.modelValue.map((subject, subjectIndex) => (subjectIndex === index ? { ...subject, ...patch } : subject))
  emit('update:modelValue', next)
}

function addSubject() {
  emit('update:modelValue', [
    ...props.modelValue,
    { course_id: null, full_score: '100.00', pass_score: '60.00', excellent_score: '90.00', exam_date: '', remark: '' },
  ])
}

function removeSubject(index: number) {
  emit(
    'update:modelValue',
    props.modelValue.filter((_subject, subjectIndex) => subjectIndex !== index),
  )
}

function courseDisabled(courseId: number, currentIndex: number) {
  return props.modelValue.some((subject, index) => index !== currentIndex && subject.course_id === courseId)
}
</script>

<template>
  <section class="gm-subject-editor">
    <div v-for="(subject, index) in modelValue" :key="index" class="gm-subject-row">
      <el-select
        :model-value="subject.course_id"
        placeholder="考试科目"
        @update:model-value="updateSubject(index, { course_id: $event })"
      >
        <el-option
          v-for="course in courses"
          :key="course.id"
          :disabled="courseDisabled(course.id, index)"
          :label="course.course_name"
          :value="course.id"
        />
      </el-select>
      <el-input :model-value="subject.full_score" placeholder="满分" @update:model-value="updateSubject(index, { full_score: $event })" />
      <el-input :model-value="subject.pass_score" placeholder="及格分" @update:model-value="updateSubject(index, { pass_score: $event })" />
      <el-input
        :model-value="subject.excellent_score"
        placeholder="优秀分"
        @update:model-value="updateSubject(index, { excellent_score: $event })"
      />
      <el-date-picker
        :model-value="subject.exam_date"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="考试日期"
        @update:model-value="updateSubject(index, { exam_date: $event || '' })"
      />
      <el-input :model-value="subject.remark" placeholder="备注" @update:model-value="updateSubject(index, { remark: $event })" />
      <el-button :icon="Delete" circle aria-label="删除科目" @click="removeSubject(index)" />
    </div>

    <el-button :icon="Plus" @click="addSubject">添加科目</el-button>
  </section>
</template>
