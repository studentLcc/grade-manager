<script setup lang="ts">
import { computed } from 'vue'
import type { RecentExamRecord } from '../../api/dashboard'

const props = defineProps<{
  exams: RecentExamRecord[]
}>()

const MAX_VISIBLE_RECENT_EXAMS = 5
function examTypeLabel(examType: string | null) {
  return examType === 'school' ? '校级考试' : '其他考试'
}

const visibleExams = computed(() => props.exams.slice(0, MAX_VISIBLE_RECENT_EXAMS))
</script>

<template>
  <section class="gm-page-card gm-dashboard-list">
    <div class="gm-section-title">
      <h2>近期考试</h2>
    </div>
    <el-empty v-if="!exams.length" description="暂无近期考试" :image-size="64" />
    <div v-else class="gm-stack-list">
      <article v-for="exam in visibleExams" :key="exam.id" class="gm-list-row gm-recent-exam-row">
        <strong>{{ exam.name }}</strong>
        <span>{{ examTypeLabel(exam.exam_type) }}</span>
      </article>
    </div>
  </section>
</template>
