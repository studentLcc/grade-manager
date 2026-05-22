import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import ImportErrorTable from '../src/components/imports/ImportErrorTable.vue'
import ImportDetailView from '../src/views/ImportDetailView.vue'
import ImportRecordsView from '../src/views/ImportRecordsView.vue'
import { http } from '../src/api/http'

const routerMocks = vi.hoisted(() => ({
  route: undefined as unknown as { params: { id: string } },
  push: vi.fn(),
}))

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  const { reactive } = await import('vue')
  routerMocks.route = reactive({ params: { id: '5' } })
  return {
    ...actual,
    useRoute: () => routerMocks.route,
    useRouter: () => ({ push: routerMocks.push }),
  }
})

enableAutoUnmount(afterEach)

beforeEach(() => {
  vi.restoreAllMocks()
  routerMocks.push.mockReset()
  routerMocks.route.params.id = '5'
})

const buttonStub = { template: '<button @click="$emit(\'click\')"><slot /></button>' }
const optionStub = { props: ['label'], template: '<option>{{ label }}</option>' }
const selectStub = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
}
const paginationStub = { template: '<div />' }
const tableStub = {
  props: ['data'],
  template: '<div><template v-for="row in data" :key="row.id"><slot :row="row" />{{ Object.values(row).join(" ") }}</template></div>',
}
const tableColumnStub = { props: ['label'], template: '<div>{{ label }}</div>' }

const globalStubs = {
  'el-button': buttonStub,
  'el-option': optionStub,
  'el-pagination': paginationStub,
  'el-select': selectStub,
  'el-table': tableStub,
  'el-table-column': tableColumnStub,
}

describe('import error table', () => {
  it('renders row level error fields', () => {
    const wrapper = mount(ImportErrorTable, {
      props: {
        errors: [{ id: 1, row_number: 3, field: 'student_no', raw_value: 'S001', reason: '学号重复' }],
      },
      global: {
        stubs: {
          'el-table': tableStub,
          'el-table-column': tableColumnStub,
        },
      },
    })
    expect(wrapper.text()).toContain('student_no')
    expect(wrapper.text()).toContain('学号重复')
  })

  it('renders backend target labels and partial success status in records list', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      data: {
        items: [
          {
            id: 5,
            import_type: 'scores',
            target_class_id: 1,
            target_class_name: '一班',
            target_exam_id: 9,
            target_exam_name: '期中考试',
            target_exam_subject_id: 11,
            target_exam_subject_name: '数学',
            file_name: 'scores.xlsx',
            status: 'partial_success',
            success_count: 18,
            failed_count: 2,
            created_at: '2026-05-22 10:00',
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
    })

    const wrapper = mount(ImportRecordsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('一班 / 期中考试 / 数学')
    expect(wrapper.text()).toContain('部分成功')
    expect(wrapper.text()).toContain('2')
  })

  it('renders import detail target label and workflow link from backend fields', async () => {
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/imports/5') {
        return Promise.resolve({
          data: {
            id: 5,
            import_type: 'scores',
            target_class_id: 1,
            target_class_name: '一班',
            target_exam_id: 9,
            target_exam_name: '期中考试',
            target_exam_subject_id: 11,
            target_exam_subject_name: '数学',
            file_name: 'scores.xlsx',
            status: 'partial_success',
            success_count: 18,
            failed_count: 2,
            created_at: '2026-05-22 10:00',
          },
        })
      }
      if (url === '/imports/5/errors') {
        return Promise.resolve({
          data: {
            items: [{ id: 1, row_number: 3, field: 'score', raw_value: 'bad', reason: '成绩格式错误' }],
            total: 1,
            page: 1,
            page_size: 20,
          },
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ImportDetailView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('一班 / 期中考试 / 数学')
    expect(wrapper.text()).toContain('部分成功')
    expect(wrapper.text()).toContain('成绩格式错误')

    await wrapper.find('button').trigger('click')
    expect(routerMocks.push).toHaveBeenCalledWith('/exam-center/9/scores?import=1')
  })

  it('reloads import detail when route id changes', async () => {
    const get = vi.spyOn(http, 'get').mockImplementation((url: string) => {
      const id = url.includes('/6') ? 6 : 5
      if (url === `/imports/${id}`) {
        return Promise.resolve({
          data: {
            id,
            import_type: 'scores',
            target_class_id: 1,
            target_class_name: '一班',
            target_exam_id: id === 5 ? 9 : 10,
            target_exam_name: id === 5 ? '期中考试' : '期末考试',
            target_exam_subject_id: 11,
            target_exam_subject_name: id === 5 ? '数学' : '英语',
            file_name: id === 5 ? 'midterm.xlsx' : 'final.xlsx',
            status: 'partial_success',
            success_count: 18,
            failed_count: id === 5 ? 2 : 1,
            created_at: '2026-05-22 10:00',
          },
        })
      }
      if (url === `/imports/${id}/errors`) {
        return Promise.resolve({
          data: {
            items: [{ id, row_number: 3, field: 'score', raw_value: 'bad', reason: id === 5 ? '期中错误' : '期末错误' }],
            total: 1,
            page: 1,
            page_size: 20,
          },
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ImportDetailView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('midterm.xlsx')

    routerMocks.route.params.id = '6'
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/imports/6')
    expect(get).toHaveBeenCalledWith('/imports/6/errors', expect.anything())
    expect(wrapper.text()).toContain('final.xlsx')
    expect(wrapper.text()).toContain('期末错误')
    expect(wrapper.text()).not.toContain('midterm.xlsx')
  })
})
