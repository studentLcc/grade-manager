import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import ScoreOverviewCard from '../src/components/dashboard/ScoreOverviewCard.vue'
import DashboardView from '../src/views/DashboardView.vue'
import ExamStatisticsView from '../src/views/ExamStatisticsView.vue'
import { http } from '../src/api/http'

const routerMocks = vi.hoisted(() => ({
  route: undefined as unknown as { params: { id: string } },
  push: vi.fn(),
}))

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  const { reactive } = await import('vue')
  routerMocks.route = reactive({ params: { id: '9' } })
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
  routerMocks.route.params.id = '9'
})

const buttonStub = { template: '<button><slot /></button>' }
const emptyStub = { props: ['description'], template: '<div>{{ description }}</div>' }
const iconStub = { template: '<span><slot /></span>' }
const optionStub = { props: ['label'], template: '<option>{{ label }}</option>' }
const selectStub = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
}
const inputNumberStub = { template: '<input />' }
const tableStub = {
  props: ['data'],
  template: '<div><template v-for="(row, index) in data" :key="row.id || row.rank || row.label || index"><slot :row="row" />{{ Object.values(row).join(" ") }}</template></div>',
}
const tableColumnStub = { props: ['label'], template: '<div>{{ label }}</div>' }

const globalStubs = {
  'el-button': buttonStub,
  'el-empty': emptyStub,
  'el-icon': iconStub,
  'el-input-number': inputNumberStub,
  'el-option': optionStub,
  'el-select': selectStub,
  'el-table': tableStub,
  'el-table-column': tableColumnStub,
}

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((innerResolve, innerReject) => {
    resolve = innerResolve
    reject = innerReject
  })
  return { promise, resolve, reject }
}

describe('score overview card', () => {
  it('renders required score overview metrics and abnormal distribution labels', () => {
    const wrapper = mount(ScoreOverviewCard, {
      props: {
        overview: {
          latest_exam: { id: 9, name: '期中考试' },
          average_score: '82.50',
          highest_score: '100.00',
          lowest_score: '32.00',
          abnormal_count: 5,
          abnormal_distribution: { absent: 2, deferred: 1, cheating: 1, exempt: 1 },
          low_score_warning: 4,
          failing_count: 6,
          absent_count: 2,
          cheating_count: 1,
        },
      },
    })
    expect(wrapper.text()).toContain('平均分')
    expect(wrapper.text()).toContain('最高分')
    expect(wrapper.text()).toContain('最低分')
    expect(wrapper.text()).toContain('异常状态分布')
    expect(wrapper.text()).toContain('预警指标')
    expect(wrapper.find('.gm-donut strong').text()).toBe('5')
    const warningRows = wrapper.findAll('.gm-indicator-list div')
    expect(warningRows).toHaveLength(2)
    expect(warningRows[0].text()).toContain('低分预警')
    expect(warningRows[0].text()).toContain('4 人')
    expect(warningRows[0].text()).not.toContain('%')
    expect(warningRows[1].text()).toContain('不及格')
    expect(warningRows[1].text()).toContain('6 人')
    expect(warningRows[1].text()).not.toContain('%')
    const rows = wrapper.findAll('.gm-distribution-row')
    expect(rows).toHaveLength(4)
    expect(rows[0].text()).toContain('缺考')
    expect(rows[0].text()).toContain('2 人')
    expect(rows[0].text()).toContain('40.00%')
    expect(rows[1].text()).toContain('缓考')
    expect(rows[1].text()).toContain('1 人')
    expect(rows[1].text()).toContain('20.00%')
    expect(rows[2].text()).toContain('作弊')
    expect(rows[2].text()).toContain('1 人')
    expect(rows[2].text()).toContain('20.00%')
    expect(rows[3].text()).toContain('免考')
    expect(rows[3].text()).toContain('1 人')
    expect(rows[3].text()).toContain('20.00%')
    expect(wrapper.text()).not.toContain('13')
  })

  it('renders dashboard list data from backend items wrappers', async () => {
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/dashboard/summary') {
        return Promise.resolve({ data: { class_count: 1, student_count: 30, course_count: 4, recent_exam_count: 1, pending_score_count: 2 } })
      }
      if (url === '/dashboard/today-schedule') {
        return Promise.resolve({ data: { items: [{ id: 1, class_id: 1, class_name: null, course_id: 3, course_name: null, weekday: 5, period_no: 2, start_time: '09:00', end_time: '09:45', location: null }] } })
      }
      if (url === '/dashboard/recent-exams') {
        return Promise.resolve({ data: { items: [{ id: 9, name: '期末统考', exam_type: 'final', term: '2026' }] } })
      }
      if (url === '/dashboard/score-overview') {
        return Promise.resolve({
          data: {
            latest_exam: { id: 9, name: '期中考试' },
            average_score: '80.00',
            highest_score: '99.00',
            lowest_score: '50.00',
            abnormal_count: 0,
            abnormal_distribution: {},
            low_score_warning: 0,
            failing_count: 0,
            absent_count: 0,
            cheating_count: 0,
          },
        })
      }
      if (url === '/dashboard/class-average-trend') {
        return Promise.resolve({ data: { items: [{ exam_id: 9, exam_name: '期中考试', class_id: 1, class_name: null, average_score: '83.50' }] } })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(DashboardView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('未命名课程')
    expect(wrapper.text()).toContain('未关联班级')
    expect(wrapper.text()).toContain('期末统考')
    expect(wrapper.text()).toContain('2026')
    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).not.toContain('其他考试')
    expect(wrapper.text()).toContain('83.50')
    expect(wrapper.text()).not.toContain('2026 · -')
  })

  it('renders statistics backend fields and sends backend query parameter names', async () => {
    const get = vi.spyOn(http, 'get').mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      if (url === '/exams/9') {
        return Promise.resolve({
          data: {
            id: 9,
            name: '期中考试',
            exam_type: 'midterm',
            term: '2026',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
          },
        })
      }
      if (url === '/classes') {
        return Promise.resolve({ data: { items: [{ id: 1, name: '一班', grade: null, academic_year: null, status: 'active', remark: null }], total: 1, page: 1, page_size: 100 } })
      }
      if (url === '/statistics/exams/9/summary') {
        expect(config?.params).toEqual({ included_statuses: 'normal' })
        return Promise.resolve({
          data: {
            exam: { id: 9, name: '期中考试' },
            included_statuses: ['normal'],
            overall: { average_score: '82.00', highest_score: '99.00', lowest_score: '45.00', pass_rate: '50.00', excellent_rate: '50.00' },
            class_comparison: [{ id: 1, name: '一班', average_score: '82.00', highest_score: '99.00', lowest_score: '65.00', pass_rate: '100.00', excellent_rate: '50.00' }],
            subject_comparison: [{ id: 11, name: '数学', average_score: '82.00', highest_score: '99.00', lowest_score: '65.00', pass_rate: '100.00', excellent_rate: '50.00' }],
            abnormal_counts: { absent: 1 },
            missing_score_count: 1,
            abnormal_lists: { absent: [{ exam_student_id: 22, student_id: 2, student_no: 'S002', name: '李四', class_id: 1, class_name: '一班', course_name: '数学', exam_subject_id: 11 }] },
            missing_score_list: [{ exam_student_id: 23, student_id: 3, student_no: 'S003', name: '王五', class_id: 1, class_name: '一班', course_name: '数学', exam_subject_id: 11 }],
          },
        })
      }
      if (url === '/statistics/exams/9/rankings') {
        expect(config?.params).toMatchObject({ rank_type: 'total' })
        expect(config?.params).not.toHaveProperty('ranking_type')
        expect(config?.params).not.toHaveProperty('page')
        expect(config?.params).not.toHaveProperty('page_size')
        return Promise.resolve({ data: { items: [{ rank: 1, exam_student_id: 21, student_id: 1, student_no: 'S001', name: '张三', class_id: 1, class_name: '一班', score: '99.00' }], total: 1, page: 1, page_size: 50 } })
      }
      if (url === '/statistics/exams/9/segments') {
        expect(config?.params).toMatchObject({ type: 'total', step: 10 })
        expect(config?.params).not.toHaveProperty('segment_type')
        return Promise.resolve({ data: { items: [{ label: '90-100', start: '90.00', end: '100.00', count: 1 }], total: 1, page: 1, page_size: 50 } })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamStatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/statistics/exams/9/rankings', expect.objectContaining({ params: expect.objectContaining({ rank_type: 'total' }) }))
    expect(get).toHaveBeenCalledWith('/statistics/exams/9/rankings', expect.objectContaining({ params: expect.not.objectContaining({ page: expect.anything() }) }))
    expect(get).toHaveBeenCalledWith('/statistics/exams/9/segments', expect.objectContaining({ params: expect.objectContaining({ type: 'total', step: 10 }) }))
    expect(get).toHaveBeenCalledWith('/statistics/exams/9/summary', expect.objectContaining({ params: { included_statuses: 'normal' } }))
    expect(wrapper.text()).toContain('一班')
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('99.00')
    expect(wrapper.text()).toContain('90-100')
    expect(wrapper.text()).toContain('李四')
    expect(wrapper.text()).toContain('数学')
  })

  it('reloads statistics base metadata when reused for a new exam route id', async () => {
    const get = vi.spyOn(http, 'get').mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      const id = url.includes('/10') ? 10 : 9
      if (url === `/exams/${id}`) {
        return Promise.resolve({
          data: {
            id,
            name: id === 9 ? '期中考试' : '期末考试',
            exam_type: 'midterm',
            term: '2026',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [
              {
                id: id === 9 ? 11 : 22,
                course_id: id === 9 ? 3 : 4,
                course_name: id === 9 ? '数学' : '英语',
                full_score: '100',
                pass_score: '60',
                excellent_score: '90',
                exam_date: null,
                status: 'active',
                remark: null,
              },
            ],
          },
        })
      }
      if (url === '/classes') {
        return Promise.resolve({ data: { items: [{ id: 1, name: '一班', grade: null, academic_year: null, status: 'active', remark: null }], total: 1, page: 1, page_size: 100 } })
      }
      if (url === `/statistics/exams/${id}/summary`) {
        return Promise.resolve({
          data: {
            exam: { id, name: id === 9 ? '期中考试' : '期末考试' },
            included_statuses: ['normal'],
            overall: { average_score: '80.00', highest_score: '99.00', lowest_score: '50.00', pass_rate: '90.00', excellent_rate: '20.00' },
            class_comparison: [],
            subject_comparison: [{ id: id === 9 ? 11 : 22, name: id === 9 ? '数学' : '英语', average_score: '80.00', highest_score: '99.00', lowest_score: '50.00', pass_rate: '90.00', excellent_rate: '20.00' }],
            abnormal_counts: {},
            missing_score_count: 0,
            abnormal_lists: {},
            missing_score_list: [],
          },
        })
      }
      if (url === `/statistics/exams/${id}/rankings`) {
        expect(config?.params).not.toHaveProperty('exam_subject_id')
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], rank_type: 'total', exam_subject_id: null, class_id: null, items: [] } })
      }
      if (url === `/statistics/exams/${id}/segments`) {
        expect(config?.params).not.toHaveProperty('exam_subject_id')
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], type: 'total', exam_subject_id: null, step: 10, items: [] } })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamStatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('期中考试')

    routerMocks.route.params.id = '10'
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/exams/10')
    expect(get).toHaveBeenCalledWith('/statistics/exams/10/summary', expect.anything())
    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).toContain('英语')
    expect(wrapper.text()).not.toContain('数学')
  })

  it('ignores stale statistics base metadata responses after route changes', async () => {
    const firstExam = deferred<{ data: unknown }>()
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      const id = url.includes('/10') ? 10 : 9
      if (url === '/exams/9') return firstExam.promise
      if (url === '/exams/10') {
        return Promise.resolve({
          data: {
            id: 10,
            name: '期末考试',
            exam_type: 'final',
            term: '2026',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ id: 22, course_id: 4, course_name: '英语', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
          },
        })
      }
      if (url === '/classes') {
        return Promise.resolve({ data: { items: [{ id: 1, name: '一班', grade: null, academic_year: null, status: 'active', remark: null }], total: 1, page: 1, page_size: 100 } })
      }
      if (url === `/statistics/exams/${id}/summary`) {
        return Promise.resolve({
          data: {
            exam: { id, name: id === 10 ? '期末考试' : '期中考试' },
            included_statuses: ['normal'],
            overall: { average_score: '80.00', highest_score: '99.00', lowest_score: '50.00', pass_rate: '90.00', excellent_rate: '20.00' },
            class_comparison: [],
            subject_comparison: [{ id: id === 10 ? 22 : 11, name: id === 10 ? '英语' : '数学', average_score: '80.00', highest_score: '99.00', lowest_score: '50.00', pass_rate: '90.00', excellent_rate: '20.00' }],
            abnormal_counts: {},
            missing_score_count: 0,
            abnormal_lists: {},
            missing_score_list: [],
          },
        })
      }
      if (url === `/statistics/exams/${id}/rankings`) {
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], rank_type: 'total', exam_subject_id: null, class_id: null, items: [] } })
      }
      if (url === `/statistics/exams/${id}/segments`) {
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], type: 'total', exam_subject_id: null, step: 10, items: [] } })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamStatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })

    routerMocks.route.params.id = '10'
    await flushPromises()
    expect(wrapper.text()).toContain('期末考试')

    firstExam.resolve({
      data: {
        id: 9,
        name: '期中考试',
        exam_type: 'midterm',
        term: '2026',
        status: 'active',
        remark: null,
        classes: [{ id: 1, name: '一班' }],
        subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).toContain('英语')
    expect(wrapper.text()).not.toContain('期中考试')
    expect(wrapper.text()).not.toContain('数学')
  })

  it('defaults subject mode to the first subject before requesting subject statistics', async () => {
    const get = vi.spyOn(http, 'get').mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      if (url === '/exams/9') {
        return Promise.resolve({
          data: {
            id: 9,
            name: '期中考试',
            exam_type: 'midterm',
            term: '2026',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
          },
        })
      }
      if (url === '/classes') {
        return Promise.resolve({ data: { items: [], total: 0, page: 1, page_size: 100 } })
      }
      if (url === '/statistics/exams/9/summary') {
        expect(config?.params).toEqual({ included_statuses: 'normal' })
        return Promise.resolve({
          data: {
            exam: { id: 9, name: '期中考试' },
            included_statuses: ['normal'],
            overall: { average_score: '80.00', highest_score: '99.00', lowest_score: '50.00', pass_rate: '90.00', excellent_rate: '20.00' },
            class_comparison: [],
            subject_comparison: [],
            abnormal_counts: {},
            missing_score_count: 0,
            abnormal_lists: {},
            missing_score_list: [],
          },
        })
      }
      if (url === '/statistics/exams/9/rankings') {
        if (config?.params?.rank_type === 'subject') {
          expect(config.params.exam_subject_id).toBe(11)
        }
        return Promise.resolve({ data: { exam: { id: 9, name: '考试' }, included_statuses: ['normal'], rank_type: config?.params?.rank_type || 'total', exam_subject_id: config?.params?.exam_subject_id || null, class_id: null, items: [] } })
      }
      if (url === '/statistics/exams/9/segments') {
        if (config?.params?.type === 'subject') {
          expect(config.params.exam_subject_id).toBe(11)
        }
        return Promise.resolve({ data: { exam: { id: 9, name: '考试' }, included_statuses: ['normal'], type: config?.params?.type || 'total', exam_subject_id: config?.params?.exam_subject_id || null, step: 10, items: [] } })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamStatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    const selects = wrapper.findAll('select')
    await selects[1].setValue('subject')
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/statistics/exams/9/rankings', expect.objectContaining({ params: expect.objectContaining({ rank_type: 'subject', exam_subject_id: 11 }) }))
  })
})
