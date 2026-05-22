import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../src/stores/auth'

describe('auth store', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('stores token and teacher after login success', async () => {
    const auth = useAuthStore()
    auth.setSession({
      access_token: 'token-1',
      token_type: 'bearer',
      teacher: { id: 1, username: 'teacher1', display_name: '王老师', email: null, phone: null, status: 'active' },
    })
    expect(auth.token).toBe('token-1')
    expect(auth.teacher?.display_name).toBe('王老师')
    expect(localStorage.getItem('grade-manager-token')).toBe('token-1')
  })

  it('clears session', () => {
    const auth = useAuthStore()
    auth.setSession({
      access_token: 'token-1',
      token_type: 'bearer',
      teacher: { id: 1, username: 'teacher1', display_name: '王老师', email: null, phone: null, status: 'active' },
    })
    auth.clearSession()
    expect(auth.token).toBeNull()
    expect(auth.teacher).toBeNull()
  })
})
