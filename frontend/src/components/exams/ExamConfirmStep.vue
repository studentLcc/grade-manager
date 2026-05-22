<script setup lang="ts">
import type { ClassRecord } from '../../api/classes'
import type { CourseRecord } from '../../api/courses'

interface ExamBasicForm {
  name: string
  exam_type: string
  term: string
  remark: string
}

interface ExamSubjectForm {
  course_id: number | null
  full_score: string
  pass_score: string
  excellent_score: string
  exam_date?: string
  remark: string
}

const props = defineProps<{
  basic: ExamBasicForm
  classIds: number[]
  subjects: ExamSubjectForm[]
  classes: ClassRecord[]
  courses: CourseRecord[]
}>()

const examTypeLabels: Record<string, string> = {
  school: '校级考试',
  quiz: '单元测验',
  midterm: '期中考试',
  final: '期末考试',
}

function className(classId: number) {
  return props.classes.find((item) => item.id === classId)?.name || `班级 ${classId}`
}

function examTypeLabel(examType: string) {
  return examType ? examTypeLabels[examType] || '其他考试' : '未设置'
}

function courseName(courseId: number | null) {
  if (!courseId) return '未选择科目'
  return props.courses.find((item) => item.id === courseId)?.course_name || `课程 ${courseId}`
}
</script>

<template>
  <section class="gm-confirm-list">
    <div>
      <span>考试名称</span>
      <strong>{{ basic.name || '未填写' }}</strong>
    </div>
    <div>
      <span>考试类型</span>
      <strong>{{ examTypeLabel(basic.exam_type) }}</strong>
    </div>
    <div>
      <span>学期</span>
      <strong>{{ basic.term || '未设置' }}</strong>
    </div>
    <div>
      <span>参与班级</span>
      <strong>{{ classIds.map(className).join('、') || '未选择' }}</strong>
    </div>
    <div>
      <span>考试科目</span>
      <ul>
        <li v-for="(subject, index) in subjects" :key="index">
          {{ courseName(subject.course_id) }}：满分 {{ subject.full_score }}，及格 {{ subject.pass_score }}，优秀 {{ subject.excellent_score }}
        </li>
      </ul>
    </div>
  </section>
</template>
