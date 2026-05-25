<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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

function display(value: string | number | null | undefined, fallback = '-') {
  return value ?? fallback
}

const avatarInitial = computed(() => {
  const name = teacher.value?.display_name || teacher.value?.username || '账'
  return name.trim().slice(0, 1).toUpperCase()
})

const accountItems = computed(() => [
  { label: '用户名', value: display(teacher.value?.username) },
  { label: '邮箱', value: display(teacher.value?.email, '未填写') },
  { label: '手机号', value: display(teacher.value?.phone, '未填写') },
  { label: '账号编号', value: display(teacher.value?.id) },
])

const statusClass = computed(() => `is-${teacher.value?.status || 'unknown'}`)

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

    <section class="gm-page-card gm-account-card">
      <div class="gm-account-identity">
        <div class="gm-account-avatar">{{ avatarInitial }}</div>
        <div>
          <span>当前账号</span>
          <h2>{{ teacher?.display_name || '-' }}</h2>
          <p>{{ teacher?.username || '暂无用户名' }}</p>
        </div>
        <span class="gm-account-status" :class="statusClass">{{ statusLabel(teacher?.status) }}</span>
      </div>

      <div class="gm-account-info-grid">
        <div v-for="item in accountItems" :key="item.label" class="gm-account-info-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </section>
  </section>
</template>
