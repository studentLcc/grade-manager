import { http } from './http'

interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ScheduleRecord {
  id: number
  class_id: number
  course_id: number
  weekday: number
  period_no: number
  start_time: string | null
  end_time: string | null
  location: string | null
  status: string
  remark: string | null
}

export interface ScheduleCreatePayload {
  class_id: number
  course_id: number
  weekday: number
  period_no: number
  start_time?: string | null
  end_time?: string | null
  location?: string | null
  remark?: string | null
}

export interface ScheduleUpdatePayload extends Partial<ScheduleCreatePayload> {
  status?: string
}

export function listSchedules(params: Record<string, unknown>) {
  return http.get<PageResponse<ScheduleRecord>>('/schedules', { params })
}

export function createSchedule(data: ScheduleCreatePayload) {
  return http.post<ScheduleRecord>('/schedules', data)
}

export function updateSchedule(id: number, data: ScheduleUpdatePayload) {
  return http.patch<ScheduleRecord>(`/schedules/${id}`, data)
}

export function removeSchedule(id: number) {
  return http.delete(`/schedules/${id}`)
}
