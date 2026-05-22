import { defineStore } from 'pinia'

const TOKEN_KEY = 'grade-manager-token'
const TEACHER_KEY = 'grade-manager-teacher'

export interface Teacher {
  id: number
  username: string
  display_name: string
  email: string | null
  phone: string | null
  status: string
}

export interface AuthSession {
  access_token: string
  token_type: string
  teacher: Teacher
}

function readTeacher(): Teacher | null {
  const raw = localStorage.getItem(TEACHER_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as Teacher
  } catch {
    localStorage.removeItem(TEACHER_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) as string | null,
    teacher: readTeacher(),
  }),
  actions: {
    setSession(session: AuthSession) {
      this.token = session.access_token
      this.teacher = session.teacher
      localStorage.setItem(TOKEN_KEY, session.access_token)
      localStorage.setItem(TEACHER_KEY, JSON.stringify(session.teacher))
    },
    clearSession() {
      this.token = null
      this.teacher = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(TEACHER_KEY)
    },
  },
})
