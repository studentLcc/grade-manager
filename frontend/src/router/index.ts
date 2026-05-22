import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import ClassesStudentsView from '../views/ClassesStudentsView.vue'
import CoursesScheduleView from '../views/CoursesScheduleView.vue'
import { useAuthStore } from '../stores/auth'

const placeholder = (title: string) => ({
  template: `<section class="gm-page-card"><h1>${title}</h1><p>该功能将在后续任务中实现。</p></section>`,
})

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/register', component: RegisterView, meta: { public: true } },
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: DashboardView },
        { path: 'classes-students', component: ClassesStudentsView },
        { path: 'courses-schedule', component: CoursesScheduleView },
        { path: 'exam-center', component: placeholder('考试中心') },
        { path: 'exam-center/:id', component: placeholder('考试详情') },
        { path: 'exam-center/:id/scores', component: placeholder('成绩录入') },
        { path: 'exam-center/:id/statistics', component: placeholder('考试统计') },
        { path: 'statistics', component: placeholder('综合统计') },
        { path: 'imports', component: placeholder('导入记录') },
        { path: 'imports/:id', component: placeholder('导入详情') },
        { path: 'account', component: placeholder('账号设置') },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.token) return { path: '/login', query: { redirect: to.fullPath } }
  return true
})

export default router
