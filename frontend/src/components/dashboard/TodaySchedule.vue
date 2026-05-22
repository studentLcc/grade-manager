<script setup lang="ts">
import type { TodayScheduleRecord } from '../../api/dashboard'

defineProps<{
  schedules: TodayScheduleRecord[]
}>()
</script>

<template>
  <section class="gm-page-card gm-dashboard-list">
    <div class="gm-section-title">
      <h2>今日课表</h2>
    </div>
    <el-empty v-if="!schedules.length" description="今日暂无课程" :image-size="64" />
    <div v-else class="gm-stack-list">
      <article v-for="schedule in schedules" :key="schedule.id" class="gm-list-row">
        <div>
          <strong>第 {{ schedule.period_no || '-' }} 节</strong>
          <span>{{ schedule.course_name || '未命名课程' }}</span>
        </div>
        <small>{{ schedule.class_name || '未关联班级' }}</small>
      </article>
    </div>
  </section>
</template>
