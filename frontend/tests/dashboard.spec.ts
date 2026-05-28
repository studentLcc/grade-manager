import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { computed, h, inject, markRaw, provide, type ComputedRef, type VNode } from 'vue'
import { School } from '@element-plus/icons-vue'
import ClassAverageTrend from '../src/components/dashboard/ClassAverageTrend.vue'
import MetricCard from '../src/components/dashboard/MetricCard.vue'
import RecentExams from '../src/components/dashboard/RecentExams.vue'
import ScoreOverviewCard from '../src/components/dashboard/ScoreOverviewCard.vue'
import TodaySchedule from '../src/components/dashboard/TodaySchedule.vue'
import DashboardView from '../src/views/DashboardView.vue'
import ExamStatisticsView from '../src/views/ExamStatisticsView.vue'
import StatisticsView from '../src/views/StatisticsView.vue'
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
const optionStub = { props: ['label', 'value'], template: '<option :value="value">{{ label }}</option>' }
const selectStub = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template: '<select :value="modelValue" @change="$emit(\'update:modelValue\', $event.target.value)"><slot /></select>',
}
const inputNumberStub = { template: '<input />' }
const inputStub = { template: '<input />' }
const paginationStub = { template: '<div />' }
type TableRow = Record<string, unknown>
const tableRowsKey = Symbol('tableRows')
const tableStub = {
  props: ['data'],
  setup(props: { data?: TableRow[] }, { slots }: { slots: { default?: () => VNode[] } }) {
    const rows = computed(() => props.data || [])
    provide(tableRowsKey, rows)
    return () =>
      h('div', [
        slots.default?.(),
        ...rows.value.map((row) => h('div', { key: String(row.id || row.rank || row.label || '') }, Object.values(row).join(' '))),
      ])
  },
}
const tableColumnStub = {
  props: ['label'],
  setup(props: { label?: string }, { slots }: { slots: { default?: (scope: { row: TableRow }) => VNode[] } }) {
    const rows = inject<ComputedRef<TableRow[]>>(tableRowsKey, computed(() => []))
    return () => {
      const children: (string | VNode)[] = [props.label || '']
      if (slots.default) {
        for (const row of rows.value) {
          children.push(...slots.default({ row }))
        }
      }
      return h('div', children)
    }
  },
}

const globalStubs = {
  'el-button': buttonStub,
  'el-empty': emptyStub,
  'el-icon': iconStub,
  'el-input': inputStub,
  'el-input-number': inputNumberStub,
  'el-option': optionStub,
  'el-pagination': paginationStub,
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
  it('separates metric labels, values, and units for dashboard summary cards', () => {
    const wrapper = mount(MetricCard, {
      props: {
        label: '班级数',
        value: 12,
        unit: '个',
        tone: 'teal',
        icon: markRaw(School),
      },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('.gm-metric-label').text()).toBe('班级数')
    expect(wrapper.find('.gm-metric-value').text()).toBe('12')
    expect(wrapper.find('.gm-metric-unit').text()).toBe('个')
  })

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
          normal_count: 8,
          reference_count: 13,
          low_score_warning: 4,
          failing_count: 6,
          absent_count: 2,
          cheating_count: 1,
        },
        classOptions: [
          { id: 1, name: '一班' },
          { id: 2, name: '二班' },
        ],
        selectedClassId: null,
        academicYears: ['2026-2027', '2025-2026'],
        selectedAcademicYear: '2026-2027',
      },
      global: { stubs: globalStubs },
    })
    expect(wrapper.text()).toContain('平均分')
    expect(wrapper.find('.gm-score-overview > .gm-section-title h2').text()).toBe('成绩概览')
    expect(wrapper.find('.gm-academic-year-select').exists()).toBe(true)
    expect(wrapper.find('.gm-academic-year-select').attributes('value')).toBe('2026-2027')
    expect(wrapper.find('.gm-score-class-filter').classes()).toContain('gm-trend-class-strip')
    expect(wrapper.find('.gm-score-class-chip').classes()).toContain('gm-trend-class-chip')
    expect(wrapper.findAll('.gm-score-class-chip').map((chip) => chip.text())).toEqual(['全部', '一班', '二班'])
    expect(wrapper.find('.gm-score-class-chip.is-active').text()).toBe('全部')
    expect(wrapper.text()).toContain('最高分')
    expect(wrapper.text()).toContain('最低分')
    expect(wrapper.text()).toContain('正常考试')
    expect(wrapper.text()).toContain('状态人数分布')
    expect(wrapper.text()).toContain('共 13 人次')
    expect(wrapper.text()).not.toContain('预警指标')
    expect(wrapper.find('.gm-donut span').text()).toBe('正常考试')
    expect(wrapper.find('.gm-donut strong').text()).toBe('8人')
    expect(wrapper.find('.gm-score-visuals').exists()).toBe(true)
    expect(wrapper.findAll('.gm-status-bar-row')).toHaveLength(7)
    const rows = wrapper.findAll('.gm-status-info-item')
    expect(rows).toHaveLength(7)
    expect(rows[0].text()).toContain('正常考试')
    expect(rows[0].text()).toContain('8 人')
    expect(rows[1].text()).toContain('缺考')
    expect(rows[1].text()).toContain('2 人')
    expect(rows[2].text()).toContain('缓考')
    expect(rows[2].text()).toContain('1 人')
    expect(rows[3].text()).toContain('作弊')
    expect(rows[3].text()).toContain('1 人')
    expect(rows[4].text()).toContain('免考')
    expect(rows[4].text()).toContain('1 人')
    expect(rows[5].text()).toContain('低分预警')
    expect(rows[5].text()).toContain('4 人')
    expect(rows[6].text()).toContain('不及格')
    expect(rows[6].text()).toContain('6 人')
  })

  it('emits selected academic year changes from the score overview title selector', async () => {
    const wrapper = mount(ScoreOverviewCard, {
      props: {
        overview: null,
        academicYears: ['2026-2027', '2025-2026'],
        selectedAcademicYear: '2026-2027',
      },
      global: { stubs: globalStubs },
    })

    await wrapper.find('.gm-academic-year-select').setValue('2025-2026')

    expect(wrapper.emitted('update:selectedAcademicYear')?.[0]).toEqual(['2025-2026'])
  })

  it('emits selected class changes from the score overview class chips', async () => {
    const wrapper = mount(ScoreOverviewCard, {
      props: {
        overview: null,
        classOptions: [
          { id: 1, name: '一班' },
          { id: 2, name: '二班' },
        ],
        selectedClassId: null,
      },
      global: { stubs: globalStubs },
    })

    await wrapper.findAll('.gm-score-class-chip')[2].trigger('click')

    expect(wrapper.emitted('update:selectedClassId')?.[0]).toEqual([2])
  })

  it('renders class average data as a selected class trend instead of a long bar list', async () => {
    const wrapper = mount(ClassAverageTrend, {
      props: {
        points: [
          { exam_id: 12, exam_name: '期末考试', class_id: 1, class_name: '一班', average_score: '86.00' },
          { exam_id: 12, exam_name: '期末考试', class_id: 2, class_name: '二班', average_score: '83.00' },
          { exam_id: 11, exam_name: '期中考试', class_id: 1, class_name: '一班', average_score: '80.00' },
          { exam_id: 11, exam_name: '期中考试', class_id: 2, class_name: '二班', average_score: '78.00' },
        ],
        academicYears: ['2026-2027', '2025-2026'],
        selectedAcademicYear: '2026-2027',
      },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('.gm-trend-card > .gm-section-title h2').text()).toBe('班级均分趋势')
    expect(wrapper.find('.gm-academic-year-select').attributes('value')).toBe('2026-2027')
    expect(wrapper.findAll('.gm-trend-class-chip').map((chip) => chip.text())).toEqual(['一班', '二班'])
    expect(wrapper.find('.gm-trend-selected-class').text()).toContain('一班')
    expect(wrapper.find('.gm-trend-chart').exists()).toBe(true)
    expect(wrapper.findAll('.gm-trend-bar')).toHaveLength(2)
    expect(wrapper.find('.gm-trend-axis-x').exists()).toBe(true)
    expect(wrapper.find('.gm-trend-axis-y').exists()).toBe(true)
    expect(wrapper.findAll('.gm-trend-grid-line')).toHaveLength(3)
    expect(wrapper.find('.gm-trend-area').exists()).toBe(true)
    expect(wrapper.findAll('.gm-trend-axis-label').map((item) => item.text())).toEqual(['100', '50', '0'])
    expect(wrapper.findAll('.gm-trend-x-label').map((item) => item.text())).toEqual(['期中考试', '期末考试'])
    expect(wrapper.findAll('.gm-trend-point-label').map((item) => item.text())).toEqual(['期中考试', '期末考试'])
    expect(wrapper.findAll('.gm-trend-row')).toHaveLength(0)

    await wrapper.findAll('.gm-trend-class-chip')[1].trigger('click')

    expect(wrapper.find('.gm-trend-selected-class').text()).toContain('二班')
    expect(wrapper.findAll('.gm-trend-point-value').map((item) => item.text())).toEqual(['78.00', '83.00'])

    await wrapper.find('.gm-academic-year-select').setValue('2025-2026')

    expect(wrapper.emitted('update:selectedAcademicYear')?.[0]).toEqual(['2025-2026'])
  })

  it('marks empty class average trend cards for compact adaptive layout', () => {
    const wrapper = mount(ClassAverageTrend, {
      props: {
        points: [],
        academicYears: ['2026-2027'],
        selectedAcademicYear: '2026-2027',
      },
      global: { stubs: globalStubs },
    })

    expect(wrapper.find('.gm-dashboard-analysis-card').classes()).toContain('is-empty')
    expect(wrapper.text()).toContain('暂无趋势数据')
    expect(wrapper.find('.gm-trend-class-strip').exists()).toBe(false)
  })

  it('uses readable trend axis labels for academic-year prefixed exam names', () => {
    const wrapper = mount(ClassAverageTrend, {
      props: {
        points: [
          { exam_id: 14, exam_name: '2026-2027 学年综合诊断', class_id: 1, class_name: '一班', average_score: '86.00' },
          { exam_id: 13, exam_name: '2026-2027 学年期末考试', class_id: 1, class_name: '一班', average_score: '83.00' },
          { exam_id: 12, exam_name: '2026-2027 学年期中考试', class_id: 1, class_name: '一班', average_score: '80.00' },
        ],
        academicYears: ['2026-2027'],
        selectedAcademicYear: '2026-2027',
      },
      global: { stubs: globalStubs },
    })

    expect(wrapper.findAll('.gm-trend-x-label').map((item) => item.text())).toEqual(['期中考试', '期末考试', '综合诊断'])
  })

  it('keeps recent exams compact, single-line, and limited to the nearest few records', () => {
    const wrapper = mount(RecentExams, {
      props: {
        exams: Array.from({ length: 7 }, (_, index) => ({
          id: index + 1,
          name: `2026-2027 学年第 ${index + 1} 次考试`,
          term: '2026-2027-1',
          exam_type: index === 0 ? 'school' : 'final',
        })),
      },
      global: { stubs: globalStubs },
    })

    const rows = wrapper.findAll('.gm-recent-exam-row')
    expect(rows).toHaveLength(5)
    expect(wrapper.text()).toContain('第 1 次考试')
    expect(wrapper.text()).toContain('第 5 次考试')
    expect(wrapper.text()).not.toContain('第 6 次考试')
    expect(rows[0].find('strong').text()).toContain('第 1 次考试')
    expect(rows[0].find('span').text()).toBe('校级考试')
    expect(rows[0].text()).not.toContain('2026-2027-1')
    expect(rows[1].find('span').text()).toBe('其他考试')
    expect(rows[1].text()).not.toContain('期末考试')
    expect(rows[0].find('div').exists()).toBe(false)
  })

  it('keeps today schedule compact and limited to the first five records', () => {
    const wrapper = mount(TodaySchedule, {
      props: {
        schedules: Array.from({ length: 7 }, (_, index) => ({
          id: index + 1,
          class_id: index + 1,
          class_name: `演示 ${index + 1} 班`,
          course_id: index + 1,
          course_name: `课程 ${index + 1}`,
          weekday: 1,
          period_no: index + 1,
          start_time: null,
          end_time: null,
          location: null,
        })),
      },
      global: { stubs: globalStubs },
    })

    const rows = wrapper.findAll('.gm-list-row')
    expect(rows).toHaveLength(5)
    expect(wrapper.text()).toContain('课程 1')
    expect(wrapper.text()).toContain('课程 5')
    expect(wrapper.text()).not.toContain('课程 6')
  })

  it('renders dashboard list data from backend items wrappers', async () => {
    vi.spyOn(http, 'get').mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      if (url === '/dashboard/summary') {
        return Promise.resolve({ data: { class_count: 1, student_count: 30, course_count: 4, recent_exam_count: 1, pending_score_count: 2 } })
      }
      if (url === '/dashboard/today-schedule') {
        return Promise.resolve({ data: { items: [{ id: 1, class_id: 1, class_name: null, course_id: 3, course_name: null, weekday: 5, period_no: 2, start_time: '09:00', end_time: '09:45', location: null }] } })
      }
      if (url === '/dashboard/recent-exams') {
        return Promise.resolve({ data: { items: [{ id: 9, name: '期末统考', exam_type: 'final', term: '2026' }] } })
      }
      if (url === '/classes') {
        expect(config?.params).toMatchObject({ status: 'active', page: 1, page_size: 100 })
        return Promise.resolve({
          data: {
            items: [
              { id: 1, name: '一班', grade: '七年级', academic_year: '2026-2027', status: 'active', remark: null },
              { id: 2, name: '上一学年班', grade: '七年级', academic_year: '2025-2026', status: 'active', remark: null },
            ],
            total: 2,
            page: 1,
            page_size: 100,
          },
        })
      }
      if (url === '/dashboard/score-overview') {
        expect(config?.params?.academic_year).toBe('2026-2027')
        if (config?.params?.class_id === 1) {
          return Promise.resolve({
            data: {
              latest_exam: { id: 9, name: '期中考试' },
              average_score: '83.50',
              highest_score: '95.00',
              lowest_score: '60.00',
              abnormal_count: 0,
              abnormal_distribution: {},
              normal_count: 1,
              reference_count: 1,
              low_score_warning: 0,
              failing_count: 0,
              absent_count: 0,
              cheating_count: 0,
            },
          })
        }
        return Promise.resolve({
          data: {
            latest_exam: { id: 9, name: '期中考试' },
            average_score: '80.00',
            highest_score: '99.00',
            lowest_score: '50.00',
            abnormal_count: 0,
            abnormal_distribution: {},
            normal_count: 1,
            reference_count: 1,
            low_score_warning: 0,
            failing_count: 0,
            absent_count: 0,
            cheating_count: 0,
          },
        })
      }
      if (url === '/dashboard/class-average-trend') {
        expect(config?.params?.academic_year).toBe('2026-2027')
        return Promise.resolve({ data: { items: [{ exam_id: 9, exam_name: '期中考试', class_id: 1, class_name: '一班', average_score: '83.50' }] } })
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
    expect(wrapper.text()).toContain('其他考试')
    expect(wrapper.find('.gm-recent-exam-row span').text()).toBe('其他考试')
    expect(wrapper.findAll('.gm-academic-year-select')).toHaveLength(2)
    expect(wrapper.findAll('.gm-score-class-chip').map((chip) => chip.text())).toEqual(['全部', '一班'])
    expect(wrapper.text()).toContain('83.50')
    expect(wrapper.text()).not.toContain('2026 · -')
    expect(wrapper.text()).not.toContain('快捷操作')

    const headerActions = wrapper.find('.gm-header-actions')
    expect(headerActions.exists()).toBe(true)
    const buttons = headerActions.findAll('button')
    expect(buttons.map((button) => button.text())).toEqual(['创建考试', '导入学生', '录入成绩', '查看统计'])
    expect(wrapper.findAll('.gm-metric-unit').map((unit) => unit.text())).toEqual(['个', '人', '门', '份'])

    await buttons[1].trigger('click')
    expect(routerMocks.push).toHaveBeenCalledWith('/classes-students')
    await buttons[3].trigger('click')
    expect(routerMocks.push).toHaveBeenCalledWith('/statistics')

    await wrapper.findAll('.gm-score-class-chip')[1].trigger('click')
    await flushPromises()

    expect(http.get).toHaveBeenCalledWith('/dashboard/score-overview', { params: { academic_year: '2026-2027', class_id: 1 } })
    expect(wrapper.find('.gm-score-class-chip.is-active').text()).toBe('一班')
  })

  it('keeps score overview and class trend academic year filters independent', async () => {
    const get = vi.spyOn(http, 'get').mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      if (url === '/dashboard/summary') {
        return Promise.resolve({ data: { class_count: 2, student_count: 60, course_count: 4, recent_exam_count: 2, pending_score_count: 0 } })
      }
      if (url === '/dashboard/today-schedule') {
        return Promise.resolve({ data: { items: [] } })
      }
      if (url === '/dashboard/recent-exams') {
        return Promise.resolve({ data: { items: [] } })
      }
      if (url === '/classes') {
        return Promise.resolve({
          data: {
            items: [
              { id: 1, name: '一班', grade: '七年级', academic_year: '2026-2027', status: 'active', remark: null },
              { id: 2, name: '往届一班', grade: '七年级', academic_year: '2025-2026', status: 'active', remark: null },
            ],
            total: 2,
            page: 1,
            page_size: 100,
          },
        })
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
            normal_count: 1,
            reference_count: 1,
            low_score_warning: 0,
            failing_count: 0,
            absent_count: 0,
            cheating_count: 0,
          },
        })
      }
      if (url === '/dashboard/class-average-trend') {
        const academicYear = config?.params?.academic_year
        return Promise.resolve({
          data: {
            items: [
              {
                exam_id: academicYear === '2025-2026' ? 8 : 9,
                exam_name: academicYear === '2025-2026' ? '往届期中考试' : '期中考试',
                class_id: academicYear === '2025-2026' ? 2 : 1,
                class_name: academicYear === '2025-2026' ? '往届一班' : '一班',
                average_score: academicYear === '2025-2026' ? '76.00' : '83.50',
              },
            ],
          },
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(DashboardView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()
    get.mockClear()

    await wrapper.findAll('.gm-academic-year-select')[1].setValue('2025-2026')
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/dashboard/class-average-trend', { params: { academic_year: '2025-2026' } })
    expect(get).not.toHaveBeenCalledWith('/dashboard/score-overview', expect.anything())
    expect(wrapper.findAll('.gm-academic-year-select')[0].attributes('value')).toBe('2026-2027')
    expect(wrapper.findAll('.gm-academic-year-select')[1].attributes('value')).toBe('2025-2026')
    expect(wrapper.text()).toContain('往届一班')
  })

  it('renders top-level statistics as a functional exam entry list', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      data: {
        items: [
          {
            id: 9,
            name: '期末考试',
            exam_type: 'final',
            term: '2026',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
    })

    const wrapper = mount(StatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('统计分析')
    expect(wrapper.text()).not.toContain('后续任务')
    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).toContain('考试名称')

    const statisticsButton = wrapper.findAll('button').find((button) => button.text() === '查看统计')
    expect(statisticsButton).toBeDefined()
    await statisticsButton?.trigger('click')
    expect(routerMocks.push).toHaveBeenCalledWith('/exam-center/9/statistics')
  })

  it('organizes exam statistics into focused sections and loads detail tables on demand', async () => {
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
        expect(config?.params).toMatchObject({ rank_type: 'total', page: 1, page_size: 20 })
        expect(config?.params).not.toHaveProperty('ranking_type')
        return Promise.resolve({
          data: {
            exam: { id: 9, name: '期中考试' },
            included_statuses: ['normal'],
            rank_type: 'total',
            exam_subject_id: null,
            class_id: null,
            total: 1,
            page: 1,
            page_size: 20,
            items: [{ rank: 1, exam_student_id: 21, student_id: 1, student_no: 'S001', name: '张三', class_id: 1, class_name: '一班', score: '99.00' }],
          },
        })
      }
      if (url === '/statistics/exams/9/segments') {
        expect(config?.params).toMatchObject({ type: 'total', step: 10, page: 1, page_size: 20 })
        expect(config?.params).not.toHaveProperty('segment_type')
        return Promise.resolve({
          data: {
            exam: { id: 9, name: '期中考试' },
            included_statuses: ['normal'],
            type: 'total',
            exam_subject_id: null,
            step: 10,
            total: 1,
            page: 1,
            page_size: 20,
            items: [{ label: '90-100', start: '90.00', end: '100.00', count: 1 }],
          },
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamStatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/statistics/exams/9/summary', expect.objectContaining({ params: { included_statuses: 'normal' } }))
    expect(get).not.toHaveBeenCalledWith('/statistics/exams/9/rankings', expect.anything())
    expect(get).not.toHaveBeenCalledWith('/statistics/exams/9/segments', expect.anything())
    expect(wrapper.find('.gm-stats-tabs').exists()).toBe(true)
    expect(wrapper.find('.gm-overview-section').exists()).toBe(true)
    expect(wrapper.find('.gm-ranking-section').exists()).toBe(false)
    expect(wrapper.find('.gm-segment-section').exists()).toBe(false)
    expect(wrapper.find('.gm-exception-section').exists()).toBe(false)
    expect(wrapper.text()).toContain('一班')
    expect(wrapper.text()).toContain('数学')

    await wrapper.findAll('.gm-stats-tab')[1].trigger('click')
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/statistics/exams/9/rankings', expect.objectContaining({ params: expect.objectContaining({ rank_type: 'total', page: 1, page_size: 20 }) }))
    expect(wrapper.find('.gm-ranking-section').exists()).toBe(true)
    expect(wrapper.find('.gm-ranking-section .gm-pagination').exists()).toBe(true)
    expect(wrapper.find('.gm-overview-section').exists()).toBe(false)
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('99.00')

    await wrapper.findAll('.gm-stats-tab')[2].trigger('click')
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/statistics/exams/9/segments', expect.objectContaining({ params: expect.objectContaining({ type: 'total', step: 10, page: 1, page_size: 20 }) }))
    expect(wrapper.find('.gm-segment-section').exists()).toBe(true)
    expect(wrapper.find('.gm-segment-section .gm-pagination').exists()).toBe(true)
    expect(wrapper.find('.gm-ranking-section').exists()).toBe(false)
    expect(wrapper.text()).toContain('90-100')

    await wrapper.findAll('.gm-stats-tab')[3].trigger('click')
    await flushPromises()

    expect(wrapper.find('.gm-exception-section').exists()).toBe(true)
    expect(wrapper.findAll('.gm-exception-table')).toHaveLength(1)
    expect(wrapper.text()).toContain('李四')
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
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], rank_type: 'total', exam_subject_id: null, class_id: null, total: 0, page: 1, page_size: 20, items: [] } })
      }
      if (url === `/statistics/exams/${id}/segments`) {
        expect(config?.params).not.toHaveProperty('exam_subject_id')
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], type: 'total', exam_subject_id: null, step: 10, total: 0, page: 1, page_size: 20, items: [] } })
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
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], rank_type: 'total', exam_subject_id: null, class_id: null, total: 0, page: 1, page_size: 20, items: [] } })
      }
      if (url === `/statistics/exams/${id}/segments`) {
        return Promise.resolve({ data: { exam: { id, name: '考试' }, included_statuses: ['normal'], type: 'total', exam_subject_id: null, step: 10, total: 0, page: 1, page_size: 20, items: [] } })
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
        return Promise.resolve({ data: { exam: { id: 9, name: '考试' }, included_statuses: ['normal'], rank_type: config?.params?.rank_type || 'total', exam_subject_id: config?.params?.exam_subject_id || null, class_id: null, total: 0, page: Number(config?.params?.page || 1), page_size: Number(config?.params?.page_size || 20), items: [] } })
      }
      if (url === '/statistics/exams/9/segments') {
        if (config?.params?.type === 'subject') {
          expect(config.params.exam_subject_id).toBe(11)
        }
        return Promise.resolve({ data: { exam: { id: 9, name: '考试' }, included_statuses: ['normal'], type: config?.params?.type || 'total', exam_subject_id: config?.params?.exam_subject_id || null, step: 10, total: 0, page: Number(config?.params?.page || 1), page_size: Number(config?.params?.page_size || 20), items: [] } })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamStatisticsView, {
      global: { stubs: globalStubs, directives: { loading: {} } },
    })
    await flushPromises()

    await wrapper.findAll('.gm-stats-tab')[1].trigger('click')
    await flushPromises()

    const selects = wrapper.findAll('select')
    await selects[1].setValue('subject')
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/statistics/exams/9/rankings', expect.objectContaining({ params: expect.objectContaining({ rank_type: 'subject', exam_subject_id: 11 }) }))
  })
})
