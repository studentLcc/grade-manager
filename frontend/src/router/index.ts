import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import ClassesStudentsView from '../views/ClassesStudentsView.vue'
import CoursesScheduleView from '../views/CoursesScheduleView.vue'
import ExamCenterView from '../views/ExamCenterView.vue'
import ExamDetailView from '../views/ExamDetailView.vue'
import ScoreManagementView from '../views/ScoreManagementView.vue'
import ScoreEntryView from '../views/ScoreEntryView.vue'
import ExamStatisticsView from '../views/ExamStatisticsView.vue'
import ImportRecordsView from '../views/ImportRecordsView.vue'
import ImportDetailView from '../views/ImportDetailView.vue'
import AccountSettingsView from '../views/AccountSettingsView.vue'
import StatisticsView from '../views/StatisticsView.vue'
import { useAuthStore } from '../stores/auth'

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
        { path: 'exam-center', component: ExamCenterView },
        { path: 'score-management', component: ScoreManagementView },
        { path: 'exam-center/:id', component: ExamDetailView },
        { path: 'exam-center/:id/scores', component: ScoreEntryView },
        { path: 'exam-center/:id/statistics', component: ExamStatisticsView },
        { path: 'statistics', component: StatisticsView },
        { path: 'imports', component: ImportRecordsView },
        { path: 'imports/:id', component: ImportDetailView },
        { path: 'account', component: AccountSettingsView },
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
