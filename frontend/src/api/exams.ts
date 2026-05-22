import { http } from './http'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ExamClassRecord {
  id: number
  name: string
}

export interface ExamSubjectRecord {
  id: number
  course_id: number
  course_name: string | null
  full_score: string
  pass_score: string | null
  excellent_score: string | null
  exam_date: string | null
  status: string
  remark: string | null
}

export interface ExamRecord {
  id: number
  name: string
  exam_type: string | null
  term: string | null
  status: string
  remark: string | null
  classes: ExamClassRecord[]
  subjects: ExamSubjectRecord[]
}

export interface ExamSubjectPayload {
  id?: number
  course_id: number
  full_score: string
  pass_score: string
  excellent_score: string
  status?: string
  exam_date?: string | null
  remark?: string | null
}

export interface ExamCreatePayload {
  name: string
  exam_type?: string | null
  term?: string | null
  remark?: string | null
  class_ids: number[]
  subjects: ExamSubjectPayload[]
}

export interface ExamUpdatePayload {
  name?: string
  exam_type?: string | null
  term?: string | null
  status?: string
  remark?: string | null
}

export function listExams(params: Record<string, unknown>) {
  return http.get<PageResponse<ExamRecord>>('/exams', { params })
}

export function createExam(data: ExamCreatePayload) {
  return http.post<ExamRecord>('/exams', data)
}

export function getExam(id: number) {
  return http.get<ExamRecord>(`/exams/${id}`)
}

export function updateExam(id: number, data: ExamUpdatePayload) {
  return http.patch<ExamRecord>(`/exams/${id}`, data)
}

export function removeExam(id: number) {
  return http.delete(`/exams/${id}`)
}

export function updateExamClasses(id: number, classIds: number[]) {
  return http.patch<ExamRecord>(`/exams/${id}/classes`, { class_ids: classIds })
}

export function updateExamSubjects(id: number, subjects: ExamSubjectPayload[]) {
  return http.patch<ExamRecord>(`/exams/${id}/subjects`, { subjects })
}
