import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { nextTick } from 'vue'
import router from '../src/router'
import AppLayout from '../src/layouts/AppLayout.vue'

const routerMocks = vi.hoisted(() => ({
  route: undefined as unknown as { path: string },
  push: vi.fn(),
}))

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  const { reactive } = await import('vue')
  routerMocks.route = reactive({ path: '/dashboard' })
  return {
    ...actual,
    useRoute: () => routerMocks.route,
    useRouter: () => ({ push: routerMocks.push }),
  }
})

const passThroughStub = { template: '<div><slot /><slot name="dropdown" /></div>' }
const routerLinkStub = {
  props: ['to'],
  template: '<a :href="to"><slot /></a>',
}

function mountLayout(path: string) {
  routerMocks.route.path = path
  return mount(AppLayout, {
    global: {
      plugins: [createPinia()],
      stubs: {
        RouterLink: routerLinkStub,
        RouterView: { template: '<main />' },
        'el-button': { template: '<button><slot /></button>' },
        'el-dropdown': passThroughStub,
        'el-dropdown-item': { template: '<button><slot /></button>' },
        'el-dropdown-menu': passThroughStub,
        'el-icon': { template: '<span><slot /></span>' },
        'el-input': { template: '<input />' },
      },
    },
  })
}

describe('main navigation', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    routerMocks.push.mockReset()
    routerMocks.route.path = '/dashboard'
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('registers the score management route', () => {
    expect(router.getRoutes().map((route) => route.path)).toContain('/score-management')
  })

  it('renders sidebar items in the expected order', () => {
    const wrapper = mountLayout('/score-management')

    expect(wrapper.findAll('.gm-nav-item').map((link) => link.text().trim())).toEqual([
      '工作台',
      '班级与学生',
      '课程与课表',
      '考试中心',
      '成绩管理',
      '统计分析',
      '导入记录',
      '账号设置',
    ])
  })

  it('highlights score work routes as score management', async () => {
    const wrapper = mountLayout('/score-management')

    expect(wrapper.find('.gm-nav-item.is-active').text().trim()).toBe('成绩管理')

    routerMocks.route.path = '/exam-center/9/scores'
    await nextTick()
    expect(wrapper.find('.gm-nav-item.is-active').text().trim()).toBe('成绩管理')

    routerMocks.route.path = '/exam-center/9/statistics'
    await nextTick()
    expect(wrapper.find('.gm-nav-item.is-active').text().trim()).toBe('成绩管理')

    routerMocks.route.path = '/exam-center/9'
    await nextTick()
    expect(wrapper.find('.gm-nav-item.is-active').text().trim()).toBe('考试中心')

    routerMocks.route.path = '/imports/5'
    await nextTick()
    expect(wrapper.find('.gm-nav-item.is-active').text().trim()).toBe('导入记录')
  })
})
