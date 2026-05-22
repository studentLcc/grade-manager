import { http } from './http'
import type { AuthSession, Teacher } from '../stores/auth'

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  password: string
  display_name: string
  email?: string | null
  phone?: string | null
}

export function login(payload: LoginPayload) {
  return http.post<AuthSession>('/auth/login', payload)
}

export function register(payload: RegisterPayload) {
  return http.post<Teacher>('/auth/register', payload)
}

export function getCurrentTeacher() {
  return http.get<Teacher>('/auth/me')
}
