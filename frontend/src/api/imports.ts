import { http } from './http'

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ImportBatchRecord {
  id: number
  import_type: string
  target_class_id?: number | null
  target_class_name?: string | null
  target_exam_id?: number | null
  target_exam_name?: string | null
  target_exam_subject_id?: number | null
  target_exam_subject_name?: string | null
  file_name: string
  status: string
  success_count: number
  failed_count: number
  created_at?: string | null
  imported_at?: string | null
  teacher_name?: string | null
  error_summary?: string | null
  [key: string]: unknown
}

export interface ImportErrorRecord {
  id: number
  row_number: number | null
  field: string | null
  raw_value: string | null
  reason: string
  raw_data?: string | null
  created_at?: string | null
}

export function listImports(params: Record<string, unknown>) {
  return http.get<PageResponse<ImportBatchRecord>>('/imports', { params })
}

export function getImportBatch(id: number) {
  return http.get<ImportBatchRecord>(`/imports/${id}`)
}

export function listImportErrors(id: number, params: Record<string, unknown>) {
  return http.get<PageResponse<ImportErrorRecord>>(`/imports/${id}/errors`, { params })
}
