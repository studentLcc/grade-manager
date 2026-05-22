import { http } from './http'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ClassRecord {
  id: number
  name: string
  grade: string | null
  academic_year: string | null
  status: string
  remark: string | null
}

export interface ClassCreatePayload {
  name: string
  grade?: string | null
  academic_year?: string | null
  remark?: string | null
}

export interface ClassUpdatePayload extends Partial<ClassCreatePayload> {
  status?: string
}

export function listClasses(params: Record<string, unknown>) {
  return http.get<PageResponse<ClassRecord>>('/classes', { params })
}

export function createClass(data: ClassCreatePayload) {
  return http.post<ClassRecord>('/classes', data)
}

export function updateClass(id: number, data: ClassUpdatePayload) {
  return http.patch<ClassRecord>(`/classes/${id}`, data)
}

export function removeClass(id: number) {
  return http.delete(`/classes/${id}`)
}
