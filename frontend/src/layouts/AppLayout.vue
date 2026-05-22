<script setup lang="ts">
import {
  Bell,
  Calendar,
  DataAnalysis,
  Files,
  Grid,
  House,
  Search,
  Setting,
  UploadFilled,
  User,
} from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activePath = computed(() => {
  if (route.path.startsWith('/exam-center')) return '/exam-center'
  if (route.path.startsWith('/imports')) return '/imports'
  return route.path
})

const navItems = [
  { path: '/dashboard', label: '工作台', icon: House },
  { path: '/classes-students', label: '班级与学生', icon: User },
  { path: '/courses-schedule', label: '课程与课表', icon: Calendar },
  { path: '/exam-center', label: '考试中心', icon: Files },
  { path: '/statistics', label: '统计分析', icon: DataAnalysis },
  { path: '/imports', label: '导入记录', icon: UploadFilled },
  { path: '/account', label: '账号设置', icon: Setting },
]

function logout() {
  auth.clearSession()
  router.push('/login')
}
</script>

<template>
  <div class="gm-shell">
    <aside class="gm-sidebar">
      <div class="gm-brand">
        <div class="gm-brand-mark">G</div>
        <div>
          <strong>Grade Manager</strong>
          <span>教师成绩管理</span>
        </div>
      </div>

      <nav class="gm-nav" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :class="['gm-nav-item', { 'is-active': activePath === item.path }]"
          :to="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <div class="gm-workspace">
      <header class="gm-topbar">
        <el-input class="gm-search" placeholder="搜索班级、学生、考试" :prefix-icon="Search" clearable />
        <div class="gm-topbar-actions">
          <el-button :icon="Grid" circle aria-label="快捷入口" />
          <el-button :icon="Bell" circle aria-label="通知" />
          <el-dropdown trigger="click">
            <button class="gm-user-button" type="button">
              <span class="gm-avatar">{{ auth.teacher?.display_name?.slice(0, 1) || 'T' }}</span>
              <span>{{ auth.teacher?.display_name || '教师' }}</span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/account')">账号设置</el-dropdown-item>
                <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="gm-main">
        <RouterView />
      </main>
    </div>
  </div>
</template>
