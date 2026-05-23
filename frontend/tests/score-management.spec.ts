import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { computed, h, inject, provide, type ComputedRef, type VNode } from 'vue'
import ScoreManagementView from '../src/views/ScoreManagementView.vue'
import { http } from '../src/api/http'

const routerMocks = vi.hoisted(() => ({
  push: vi.fn(),
}))

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRouter: () => ({ push: routerMocks.push }),
  }
})

enableAutoUnmount(afterEach)

type TableRow = Record<string, unknown>
const tableRowsKey = Symbol('score-management-table-rows')

const buttonStub = { emits: ['click'], template: '<button @click="$emit(\'click\')"><slot /></button>' }
const inputStub = { template: '<input />' }
const optionStub = { props: ['label'], template: '<option>{{ label }}</option>' }
const paginationStub = { template: '<nav />' }
const selectStub = { template: '<select><slot /></select>' }
const tableStub = {
  props: ['data'],
  setup(props: { data?: TableRow[] }, { slots }: { slots: { default?: () => VNode[] } }) {
    const rows = computed(() => props.data || [])
    provide(tableRowsKey, rows)
    return () =>
      h('div', [
        slots.default?.(),
        ...rows.value.map((row) => h('div', { key: String(row.id || row.name || '') }, Object.values(row).join(' '))),
      ])
  },
}
const tableColumnStub = {
  props: ['label'],
  setup(props: { label?: string }, { slots }: { slots: { default?: (scope: { row: TableRow }) => VNode[] } }) {
    const rows = inject<ComputedRef<TableRow[]>>(tableRowsKey, computed(() => []))
    return () => {
      const children: Array<string | VNode> = [props.label || '']
      if (slots.default) {
        for (const row of rows.value) {
          children.push(...slots.default({ row }))
        }
      }
      return h('div', children)
    }
  },
}

const examPage = {
  items: [
    {
      id: 9,
      name: '期中考试',
      exam_type: 'midterm',
      term: '2026-2027-1',
      status: 'active',
      remark: null,
      classes: [{ id: 1, name: '一班' }],
      subjects: [
        {
          id: 11,
          course_id: 3,
          course_name: '数学',
          full_score: '100',
          pass_score: '60',
          excellent_score: '90',
          exam_date: null,
          status: 'active',
          remark: null,
        },
      ],
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

function mountScoreManagement() {
  return mount(ScoreManagementView, {
    global: {
      stubs: {
        'el-button': buttonStub,
        'el-input': inputStub,
        'el-option': optionStub,
        'el-pagination': paginationStub,
        'el-select': selectStub,
        'el-table': tableStub,
        'el-table-column': tableColumnStub,
      },
      directives: { loading: {} },
    },
  })
}

describe('score management view', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    routerMocks.push.mockReset()
    vi.spyOn(http, 'get').mockResolvedValue({ data: examPage })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders a score-focused exam list without exam creation controls', async () => {
    const wrapper = mountScoreManagement()
    await flushPromises()

    expect(http.get).toHaveBeenCalledWith(
      '/exams',
      expect.objectContaining({ params: expect.objectContaining({ status: 'active', page: 1, page_size: 20 }) }),
    )
    expect(wrapper.text()).toContain('成绩管理')
    expect(wrapper.text()).toContain('成绩录入')
    expect(wrapper.text()).toContain('导入成绩')
    expect(wrapper.text()).toContain('查看统计')
    expect(wrapper.text()).toContain('考试详情')
    expect(wrapper.text()).toContain('考试名称')
    expect(wrapper.text()).toContain('参与班级')
    expect(wrapper.text()).toContain('科目')
    expect(wrapper.text()).toContain('期中考试')
    expect(wrapper.text()).not.toContain('创建考试')
  })

  it('routes score management row actions to existing exam workflows', async () => {
    const wrapper = mountScoreManagement()
    await flushPromises()

    const buttons = wrapper.findAll('button')
    const scoreEntryButton = buttons.find((button) => button.text() === '成绩录入')
    const importButton = buttons.find((button) => button.text() === '导入成绩')
    const statisticsButton = buttons.find((button) => button.text() === '查看统计')
    const detailButton = buttons.find((button) => button.text() === '考试详情')

    expect(scoreEntryButton).toBeDefined()
    expect(importButton).toBeDefined()
    expect(statisticsButton).toBeDefined()
    expect(detailButton).toBeDefined()

    await scoreEntryButton?.trigger('click')
    await importButton?.trigger('click')
    await statisticsButton?.trigger('click')
    await detailButton?.trigger('click')

    expect(routerMocks.push).toHaveBeenNthCalledWith(1, '/exam-center/9/scores')
    expect(routerMocks.push).toHaveBeenNthCalledWith(2, '/exam-center/9/scores?import=1')
    expect(routerMocks.push).toHaveBeenNthCalledWith(3, '/exam-center/9/statistics')
    expect(routerMocks.push).toHaveBeenNthCalledWith(4, '/exam-center/9')
  })

  it('resets score management pagination when filters change', async () => {
    const wrapper = mountScoreManagement()
    await flushPromises()
    const view = wrapper.vm as unknown as { filters: { keyword: string; page: number } }

    view.filters.page = 3
    view.filters.keyword = '期末'
    await wrapper.vm.$nextTick()

    expect(view.filters.page).toBe(1)
  })
})
