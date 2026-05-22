<script setup lang="ts">
import type { RecentExamRecord } from '../../api/dashboard'

defineProps<{
  exams: RecentExamRecord[]
}>()

const examTypeLabels: Record<string, string> = {
  school: '校级考试',
  quiz: '单元测验',
  midterm: '期中考试',
  final: '期末考试',
}

function examTypeLabel(examType: string | null) {
  if (!examType) return '未设置类型'
  return examTypeLabels[examType] || '其他考试'
}
</script>

<template>
  <section class="gm-page-card gm-dashboard-list">
    <div class="gm-section-title">
      <h2>近期考试</h2>
    </div>
    <el-empty v-if="!exams.length" description="暂无近期考试" :image-size="64" />
    <div v-else class="gm-stack-list">
      <article v-for="exam in exams" :key="exam.id" class="gm-list-row">
        <div>
          <strong>{{ exam.name }}</strong>
          <span>{{ exam.term || '未设置学期' }} · {{ examTypeLabel(exam.exam_type) }}</span>
        </div>
      </article>
    </div>
  </section>
</template>
