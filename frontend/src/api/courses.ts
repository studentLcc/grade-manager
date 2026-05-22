import { http } from './http'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface CourseRecord {
  id: number
  course_name: string
  status: string
  remark: string | null
}

export interface CourseCreatePayload {
  course_name: string
  remark?: string | null
}

export interface CourseUpdatePayload extends Partial<CourseCreatePayload> {
  status?: string
}

export function listCourses(params: Record<string, unknown>) {
  return http.get<PageResponse<CourseRecord>>('/courses', { params })
}

export function createCourse(data: CourseCreatePayload) {
  return http.post<CourseRecord>('/courses', data)
}

export function updateCourse(id: number, data: CourseUpdatePayload) {
  return http.patch<CourseRecord>(`/courses/${id}`, data)
}

export function removeCourse(id: number) {
  return http.delete(`/courses/${id}`)
}
