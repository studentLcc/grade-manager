import { http } from './http'

export interface DashboardSummary {
  class_count: number
  student_count: number
  course_count: number
  recent_exam_count: number
  pending_score_count: number
}

export interface TodayScheduleRecord {
  id: number
  class_id: number
  class_name: string | null
  course_id: number
  course_name: string | null
  weekday: number
  period_no: number
  start_time: string | null
  end_time: string | null
  location: string | null
}

export interface RecentExamRecord {
  id: number
  name: string
  exam_type: string | null
  term: string | null
}

export interface ListResponse<T> {
  items: T[]
}

export interface LatestExamRef {
  id: number
  name: string
}

export interface ScoreOverview {
  latest_exam: LatestExamRef | null
  average_score: string | number | null
  highest_score: string | number | null
  lowest_score: string | number | null
  abnormal_count: number
  abnormal_distribution: Record<string, number>
  normal_count: number
  reference_count: number
  low_score_warning: number
  failing_count: number
  absent_count: number
  cheating_count: number
}

export interface ClassAverageTrendPoint {
  exam_id: number
  exam_name: string
  class_id: number
  class_name: string | null
  average_score: string | number | null
}

export interface DashboardScoreOverviewParams {
  classId?: number | null
  academicYear?: string | null
}

export function getDashboardSummary() {
  return http.get<DashboardSummary>('/dashboard/summary')
}

export function getTodaySchedule() {
  return http.get<ListResponse<TodayScheduleRecord>>('/dashboard/today-schedule')
}

export function getRecentExams() {
  return http.get<ListResponse<RecentExamRecord>>('/dashboard/recent-exams')
}

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

export function getDashboardScoreOverview(params?: DashboardScoreOverviewParams | number | null) {
  const requestParams =
    typeof params === 'number' || params === null
      ? compactParams({ class_id: params })
      : compactParams({ class_id: params?.classId, academic_year: params?.academicYear })
  return http.get<ScoreOverview | null>(
    '/dashboard/score-overview',
    Object.keys(requestParams).length ? { params: requestParams } : undefined,
  )
}

export function getClassAverageTrend(academicYear?: string | null) {
  const params = compactParams({ academic_year: academicYear })
  return http.get<ListResponse<ClassAverageTrendPoint>>('/dashboard/class-average-trend', Object.keys(params).length ? { params } : undefined)
}
