import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AxiosRequestConfig } from 'axios'

const mocks = vi.hoisted(() => ({
  authStore: {
    token: 'token-1' as string | null,
    clearSession: vi.fn(),
  },
  errorMessage: vi.fn(),
  routerPush: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: mocks.errorMessage,
  },
}))

vi.mock('../src/stores/auth', () => ({
  useAuthStore: () => mocks.authStore,
}))

vi.mock('../src/router', () => ({
  default: {
    push: mocks.routerPush,
  },
}))

describe('http interceptor', () => {
  beforeEach(() => {
    mocks.authStore.token = 'token-1'
    mocks.authStore.clearSession.mockReset()
    mocks.errorMessage.mockReset()
    mocks.routerPush.mockReset()
  })

  it('preserves backend auth errors for login 401 responses', async () => {
    const { http } = await import('../src/api/http')
    const config: AxiosRequestConfig = {
      url: '/auth/login',
      adapter: (requestConfig) =>
        Promise.reject({
          config: requestConfig,
          response: {
            status: 401,
            data: { message: '用户名或密码错误' },
          },
        }),
    }

    await expect(http.request(config)).rejects.toMatchObject({
      response: { status: 401 },
    })

    expect(mocks.authStore.clearSession).not.toHaveBeenCalled()
    expect(mocks.routerPush).not.toHaveBeenCalled()
    expect(mocks.errorMessage).toHaveBeenCalledWith('用户名或密码错误')
  })

  it('expires session for token-bearing auth me 401 responses', async () => {
    const { http } = await import('../src/api/http')
    const config: AxiosRequestConfig = {
      url: '/auth/me',
      adapter: (requestConfig) =>
        Promise.reject({
          config: requestConfig,
          response: {
            status: 401,
            data: { message: '未认证' },
          },
        }),
    }

    await expect(http.request(config)).rejects.toMatchObject({
      response: { status: 401 },
    })

    expect(mocks.authStore.clearSession).toHaveBeenCalledOnce()
    expect(mocks.routerPush).toHaveBeenCalledWith('/login')
    expect(mocks.errorMessage).toHaveBeenCalledWith('登录已过期，请重新登录')
  })
})
