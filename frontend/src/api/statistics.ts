import { http } from './http'

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface StatisticsExamRef {
  id: number
  name: string
}

export interface OverallStatistics {
  average_score: string | number | null
  highest_score: string | number | null
  lowest_score: string | number | null
  pass_rate: string | number | null
  excellent_rate: string | number | null
}

export interface ComparisonItem {
  id: number
  name: string
  average_score: string | number | null
  highest_score: string | number | null
  lowest_score: string | number | null
  pass_rate: string | number | null
  excellent_rate: string | number | null
}

export interface StudentListItem {
  exam_student_id: number
  student_id: number
  student_no: string
  name: string
  class_id: number
  class_name: string | null
  course_name?: string
  exam_subject_id?: number
}

export interface StatisticsSummary {
  exam: StatisticsExamRef
  included_statuses: string[]
  overall: OverallStatistics
  class_comparison: ComparisonItem[]
  subject_comparison: ComparisonItem[]
  abnormal_counts: Record<string, number>
  missing_score_count: number
  abnormal_lists: Record<string, StudentListItem[]>
  missing_score_list: StudentListItem[]
}

export interface RankingRecord {
  rank: number
  exam_student_id: number
  student_id: number
  student_no: string
  name: string
  class_id: number
  class_name: string | null
  score: string | number | null
}

export interface RankingResponse {
  exam: StatisticsExamRef
  included_statuses: string[]
  rank_type: string
  exam_subject_id: number | null
  class_id: number | null
  items: RankingRecord[]
}

export interface SegmentRecord {
  label: string
  start: string | number | null
  end: string | number | null
  count: number
}

export interface SegmentResponse {
  exam: StatisticsExamRef
  included_statuses: string[]
  type: string
  exam_subject_id: number | null
  step: number
  items: SegmentRecord[]
}

export interface StudentHistoryRecord {
  exam_id: number
  exam_name: string
  class_id: number
  class_name: string | null
  total_score: string | number
  average_score: string | number
}

export interface StudentHistoryResponse {
  student_id: number
  items: StudentHistoryRecord[]
}

export interface ClassOverviewResponse {
  class_id: number
  items: ClassOverviewItem[]
}

export interface ClassOverviewItem {
  exam_id: number
  exam_name: string
  class_id: number
  class_name: string | null
  average_score: string | number
}

export function getExamStatisticsSummary(examId: number, params: Record<string, unknown>) {
  return http.get<StatisticsSummary>(`/statistics/exams/${examId}/summary`, { params })
}

export function getExamRankings(examId: number, params: Record<string, unknown>) {
  return http.get<RankingResponse>(`/statistics/exams/${examId}/rankings`, { params })
}

export function getExamSegments(examId: number, params: Record<string, unknown>) {
  return http.get<SegmentResponse>(`/statistics/exams/${examId}/segments`, { params })
}

export function getStudentHistory(studentId: number, params: Record<string, unknown> = {}) {
  return http.get<StudentHistoryResponse>(`/statistics/students/${studentId}/history`, { params })
}

export function getClassOverview(classId: number, params: Record<string, unknown> = {}) {
  return http.get<ClassOverviewResponse>(`/statistics/classes/${classId}/overview`, { params })
}
