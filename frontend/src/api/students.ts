import { http } from './http'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface StudentRecord {
  id: number
  student_no: string
  name: string
  gender: string | null
  class_id: number | null
  status: string
  remark: string | null
}

export interface StudentImportResult {
  batch_id: number | string
  status: string
  success_count: number
  failed_count: number
}

export interface StudentCreatePayload {
  student_no: string
  name: string
  class_id?: number | null
  gender?: string | null
  remark?: string | null
}

export interface StudentUpdatePayload extends Partial<StudentCreatePayload> {
  status?: string
}

export function listStudents(params: Record<string, unknown>) {
  return http.get<PageResponse<StudentRecord>>('/students', { params })
}

export function createStudent(data: StudentCreatePayload) {
  return http.post<StudentRecord>('/students', data)
}

export function updateStudent(id: number, data: StudentUpdatePayload) {
  return http.patch<StudentRecord>(`/students/${id}`, data)
}

export function removeStudent(id: number) {
  return http.delete(`/students/${id}`)
}

export function downloadStudentTemplate() {
  return http.get<Blob>('/students/import-template', {
    responseType: 'blob',
  })
}

export function importStudents(targetClassId: number, file: File, updateExisting = false) {
  const formData = new FormData()
  formData.append('file', file)
  const params: Record<string, unknown> = { target_class_id: targetClassId }
  if (updateExisting) params.update_existing = true

  return http.post<StudentImportResult>('/students/import', formData, {
    params,
  })
}
