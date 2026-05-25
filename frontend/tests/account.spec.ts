import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AccountSettingsView from '../src/views/AccountSettingsView.vue'
import { http } from '../src/api/http'

enableAutoUnmount(afterEach)

const teacher = {
  id: 1,
  username: 'teacher1',
  display_name: '刘超',
  email: null,
  phone: null,
  status: 'active',
}

describe('account settings view', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    setActivePinia(createPinia())
    vi.spyOn(http, 'get').mockResolvedValue({ data: teacher })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders account information as a polished profile card', async () => {
    const wrapper = mount(AccountSettingsView, {
      global: {
        directives: { loading: {} },
      },
    })
    await flushPromises()

    expect(http.get).toHaveBeenCalledWith('/auth/me')
    expect(wrapper.find('.gm-account-card').exists()).toBe(true)
    expect(wrapper.find('.gm-account-identity').text()).toContain('刘超')
    expect(wrapper.find('.gm-account-avatar').text()).toBe('刘')
    expect(wrapper.find('.gm-account-status').text()).toContain('启用')
    expect(wrapper.findAll('.gm-account-info-item')).toHaveLength(4)
    expect(wrapper.find('.gm-account-info-grid').text()).toContain('teacher1')
  })
})
