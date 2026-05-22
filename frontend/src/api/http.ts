import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'
import { useAuthStore } from '../stores/auth'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

function isPublicAuthEndpoint(url?: string) {
  if (!url) return false

  const pathname = new URL(url, window.location.origin).pathname
  return pathname.endsWith('/auth/login') || pathname.endsWith('/auth/register')
}

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || '系统错误，请稍后重试'
    const hadToken = Boolean(error.config?.headers?.Authorization || useAuthStore().token)
    const publicAuthEndpoint = isPublicAuthEndpoint(error.config?.url)

    if (status === 401 && hadToken && !publicAuthEndpoint) {
      useAuthStore().clearSession()
      await router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if ([400, 401, 403, 404, 409, 422].includes(status)) {
      ElMessage.error(message)
    } else {
      ElMessage.error('系统错误，请稍后重试')
    }

    return Promise.reject(error)
  },
)
