<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getCurrentTeacher } from '../api/auth'
import { useAuthStore, type Teacher } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)
const teacher = ref<Teacher | null>(auth.teacher)

const statusLabels: Record<string, string> = {
  active: '启用',
  inactive: '停用',
  archived: '归档',
}

function statusLabel(status: string | undefined) {
  return status ? statusLabels[status] || status : '-'
}

async function loadTeacher() {
  loading.value = true
  try {
    const { data } = await getCurrentTeacher()
    teacher.value = data
    auth.teacher = data
    localStorage.setItem('grade-manager-teacher', JSON.stringify(data))
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    loading.value = false
  }
}

onMounted(loadTeacher)
</script>

<template>
  <section v-loading="loading" class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>账号设置</h1>
        <p>查看当前教师账号信息。</p>
      </div>
    </div>

    <section class="gm-page-card">
      <h2>账号信息</h2>
      <div class="gm-detail-grid">
        <div><span>显示名称</span><strong>{{ teacher?.display_name || '-' }}</strong></div>
        <div><span>用户名</span><strong>{{ teacher?.username || '-' }}</strong></div>
        <div><span>邮箱</span><strong>{{ teacher?.email || '-' }}</strong></div>
        <div><span>手机号</span><strong>{{ teacher?.phone || '-' }}</strong></div>
        <div><span>状态</span><strong>{{ statusLabel(teacher?.status) }}</strong></div>
      </div>
    </section>
  </section>
</template>
