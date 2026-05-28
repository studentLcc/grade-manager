<script setup lang="ts">
import { computed } from 'vue'
import type { TodayScheduleRecord } from '../../api/dashboard'

const props = defineProps<{
  schedules: TodayScheduleRecord[]
}>()

const MAX_VISIBLE_SCHEDULES = 5
const visibleSchedules = computed(() => props.schedules.slice(0, MAX_VISIBLE_SCHEDULES))
</script>

<template>
  <section class="gm-page-card gm-dashboard-list">
    <div class="gm-section-title">
      <h2>今日课表</h2>
    </div>
    <el-empty v-if="!schedules.length" description="今日暂无课程" :image-size="64" />
    <div v-else class="gm-stack-list">
      <article v-for="schedule in visibleSchedules" :key="schedule.id" class="gm-list-row">
        <div>
          <strong>第 {{ schedule.period_no || '-' }} 节</strong>
          <span>{{ schedule.course_name || '未命名课程' }}</span>
        </div>
        <small>{{ schedule.class_name || '未关联班级' }}</small>
      </article>
    </div>
  </section>
</template>
