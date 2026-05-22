import { http } from './http'

export interface ScoreSheetExam {
  id: number
  name: string
  exam_type: string | null
  term: string | null
  status: string
}

export interface ScoreSheetClass {
  id: number
  name: string
}

export interface ScoreSheetSubject {
  exam_subject_id: number
  course_id: number
  course_name: string | null
  full_score: string
  pass_score: string | null
  excellent_score: string | null
  status: string
}

export interface ScoreSheetStudent {
  exam_student_id: number
  student_id: number
  class_id: number
  student_no: string
  name: string
  status: string
}

export interface ScoreSheetScore {
  exam_student_id: number
  exam_subject_id: number
  score: string | null
  score_status: ScoreStatus
  remark: string | null
}

export interface ScoreSheet {
  exam: ScoreSheetExam
  classes: ScoreSheetClass[]
  subjects: ScoreSheetSubject[]
  students: ScoreSheetStudent[]
  scores: ScoreSheetScore[]
}

export type ScoreStatus = 'normal' | 'absent' | 'deferred' | 'cheating' | 'exempt'

export interface ScoreSaveItem {
  exam_student_id: number
  exam_subject_id: number
  score: string | null
  score_status: ScoreStatus
  remark?: string | null
}

export interface ScoreFailureItem {
  index?: number
  exam_student_id?: number | null
  exam_subject_id?: number | null
  reason: string
}

export interface ScoreSaveResult {
  success_count: number
  failure_count: number
  failed_items: ScoreFailureItem[]
}

export interface ScoreImportResult {
  batch_id: number | string
  status: string
  success_count: number
  failed_count: number
  error_summary?: string | null
}

export interface ImportErrorRecord {
  id: number
  batch_id: number
  row_number: number | null
  field: string | null
  raw_value: string | null
  reason: string
  raw_data: string | null
  created_at: string
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export function getScoreSheet(examId: number) {
  return http.get<ScoreSheet>(`/exams/${examId}/score-sheet`)
}

export function saveScores(examId: number, items: ScoreSaveItem[]) {
  return http.put<ScoreSaveResult>(`/exams/${examId}/scores`, { items })
}

export function downloadScoreTemplate(examId: number, classId?: number) {
  return http.get<Blob>(`/exams/${examId}/score-template`, {
    params: classId ? { class_id: classId } : undefined,
    responseType: 'blob',
  })
}

export function importScores(examId: number, file: File, overwriteExisting = false) {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<ScoreImportResult>(`/exams/${examId}/scores/import`, formData, {
    params: { overwrite_existing: overwriteExisting },
  })
}

export function listScoreImportErrors(batchId: number | string, params: Record<string, unknown>) {
  return http.get<PageResponse<ImportErrorRecord>>(`/imports/${batchId}/errors`, { params })
}
