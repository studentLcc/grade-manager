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

const scorePage = {
  items: [
    {
      exam_id: 9,
      exam_name: '期中考试',
      term: '2026-2027-1',
      exam_status: 'active',
      class_id: 1,
      class_name: '一班',
      student_id: 2,
      student_no: 'S001',
      student_name: '张三',
      exam_student_id: 21,
      course_id: 3,
      course_name: '数学',
      exam_subject_id: 11,
      full_score: '100.00',
      score: '88.00',
      score_status: 'normal',
      remark: '进步明显',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

const examPage = {
  items: [{ id: 9, name: '期中考试' }],
  total: 1,
  page: 1,
  page_size: 100,
}

const classPage = {
  items: [{ id: 1, name: '一班' }],
  total: 1,
  page: 1,
  page_size: 100,
}

const coursePage = {
  items: [{ id: 3, course_name: '数学' }],
  total: 1,
  page: 1,
  page_size: 100,
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
        'el-tooltip': { template: '<span><slot /></span>' },
      },
      directives: { loading: {} },
    },
  })
}

describe('score management view', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    routerMocks.push.mockReset()
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/scores') return Promise.resolve({ data: scorePage })
      if (url === '/exams') return Promise.resolve({ data: examPage })
      if (url === '/classes') return Promise.resolve({ data: classPage })
      if (url === '/courses') return Promise.resolve({ data: coursePage })
      return Promise.resolve({ data: { items: [], total: 0, page: 1, page_size: 20 } })
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders score records instead of an exam workflow list', async () => {
    const wrapper = mountScoreManagement()
    await flushPromises()

    expect(http.get).toHaveBeenCalledWith(
      '/scores',
      expect.objectContaining({ params: expect.objectContaining({ status: 'active', page: 1, page_size: 20 }) }),
    )
    expect(wrapper.text()).toContain('成绩管理')
    expect(wrapper.text()).toContain('期中考试')
    expect(wrapper.text()).toContain('一班')
    expect(wrapper.text()).toContain('数学')
    expect(wrapper.text()).toContain('考试名称')
    expect(wrapper.text()).toContain('班级')
    expect(wrapper.text()).toContain('学生')
    expect(wrapper.text()).toContain('学号')
    expect(wrapper.text()).toContain('科目')
    expect(wrapper.text()).toContain('成绩')
    expect(wrapper.text()).toContain('状态')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('88.00')
    expect(wrapper.text()).toContain('正常')
    expect(wrapper.text()).not.toContain('成绩录入')
    expect(wrapper.text()).not.toContain('导入成绩')
    expect(wrapper.text()).not.toContain('创建考试')
  })

  it('offers a statistics entry for each score record exam', async () => {
    const wrapper = mountScoreManagement()
    await flushPromises()

    const actions = wrapper.find('.gm-score-actions')
    expect(actions.exists()).toBe(true)
    const buttons = actions.findAll('.gm-table-action')
    expect(buttons.map((button) => button.attributes('aria-label'))).toEqual(['保存', '查看统计'])

    await buttons[1].trigger('click')

    expect(routerMocks.push).toHaveBeenCalledWith('/exam-center/9/statistics')
  })

  it('saves one score record through the existing exam score endpoint', async () => {
    const wrapper = mountScoreManagement()
    await flushPromises()
    const put = vi.spyOn(http, 'put').mockResolvedValue({
      data: { success_count: 1, failure_count: 0, failed_items: [] },
    })
    const view = wrapper.vm as unknown as {
      records: Array<{ score: string; remark: string }>
      saveRecord: (record: { score: string; remark: string }) => Promise<void>
    }

    view.records[0].score = '91'
    view.records[0].remark = '稳定提升'
    await view.saveRecord(view.records[0])

    expect(put).toHaveBeenCalledWith('/exams/9/scores', {
      items: [
        {
          exam_student_id: 21,
          exam_subject_id: 11,
          score: '91',
          score_status: 'normal',
          remark: '稳定提升',
        },
      ],
    })
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
