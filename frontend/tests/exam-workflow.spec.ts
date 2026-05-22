import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ExamWizard from '../src/components/exams/ExamWizard.vue'
import ExamDetailView from '../src/views/ExamDetailView.vue'
import { updateExamClasses, updateExamSubjects } from '../src/api/exams'
import { http } from '../src/api/http'

const routerMocks = vi.hoisted(() => ({
  route: undefined as unknown as { params: { id: string }; query: Record<string, string | undefined> },
  push: vi.fn(),
}))

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  const { reactive } = await import('vue')
  routerMocks.route = reactive({ params: { id: '7' }, query: {} })
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
  routerMocks.route.params.id = '7'
  routerMocks.route.query = {}
})

const buttonStub = { template: '<button><slot /></button>' }
const tableStub = {
  props: ['data'],
  template: '<div><slot /><div v-for="row in data" :key="row.id || row.exam_subject_id">{{ Object.values(row).join(" ") }}</div></div>',
}
const tableColumnStub = { props: ['label'], template: '<div>{{ label }}<slot /></div>' }

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((innerResolve, innerReject) => {
    resolve = innerResolve
    reject = innerReject
  })
  return { promise, resolve, reject }
}

function examRecord(id: number, name: string) {
  return {
    id,
    name,
    exam_type: 'school',
    term: '2026-2027-1',
    status: 'active',
    remark: null,
    classes: [{ id: 1, name: '一班' }],
    subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
  }
}

function scoreSheet(id: number, name: string) {
  return {
    exam: { id, name, exam_type: 'school', term: '2026-2027-1' },
    classes: [{ id: 1, name: '一班' }],
    subjects: [{ exam_subject_id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' }],
    students: [],
    scores: [],
  }
}

describe('exam wizard', () => {
  it('renders four required steps', () => {
    const wrapper = mount(ExamWizard, {
      global: {
        stubs: {
          'el-button': buttonStub,
          'el-form': { template: '<form><slot /></form>' },
          'el-form-item': { template: '<div><slot /></div>' },
          'el-input': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-step': { props: ['title'], template: '<span>{{ title }}</span>' },
          'el-steps': { template: '<div><slot /></div>' },
        },
      },
    })
    expect(wrapper.text()).toContain('基本信息')
    expect(wrapper.text()).toContain('参与班级')
    expect(wrapper.text()).toContain('考试科目')
    expect(wrapper.text()).toContain('确认创建')
  })

  it('uses patch for exam class and subject updates', async () => {
    setActivePinia(createPinia())
    const patch = vi.spyOn(http, 'patch').mockResolvedValue({ data: {} })

    await updateExamClasses(7, [1, 2])
    await updateExamSubjects(7, [{ course_id: 3, full_score: '100', pass_score: '60', excellent_score: '90' }])

    expect(patch).toHaveBeenCalledWith('/exams/7/classes', { class_ids: [1, 2] })
    expect(patch).toHaveBeenCalledWith('/exams/7/subjects', {
      subjects: [{ course_id: 3, full_score: '100', pass_score: '60', excellent_score: '90' }],
    })
  })

  it('renders score entry status summary and hides unknown raw exam type', async () => {
    routerMocks.route.params.id = '7'
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/exams/7') {
        return Promise.resolve({
          data: {
            id: 7,
            name: '期中考试',
            exam_type: 'district_mock',
            term: '2026-2027-1',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
          },
        })
      }
      if (url === '/exams/7/score-sheet') {
        return Promise.resolve({
          data: {
            exam: { id: 7, name: '期中考试', exam_type: 'district_mock', term: '2026-2027-1' },
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ exam_subject_id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' }],
            students: [
              { exam_student_id: 21, student_id: 1, class_id: 1, student_no: 'S001', name: '张三', status: 'active' },
              { exam_student_id: 22, student_id: 2, class_id: 1, student_no: 'S002', name: '李四', status: 'active' },
            ],
            scores: [{ exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null }],
          },
        })
      }
      return Promise.resolve({ data: {} })
    })

    const wrapper = mount(ExamDetailView, {
      global: {
        stubs: {
          'el-button': buttonStub,
          'el-table': tableStub,
          'el-table-column': tableColumnStub,
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('已录入')
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('未录入')
    expect(wrapper.text()).not.toContain('district_mock')
  })

  it('reloads exam detail when route id changes', async () => {
    routerMocks.route.params.id = '7'
    const get = vi.spyOn(http, 'get').mockImplementation((url: string) => {
      const id = url.includes('/8') ? 8 : 7
      if (url === `/exams/${id}`) {
        return Promise.resolve({
          data: {
            id,
            name: id === 7 ? '期中考试' : '期末考试',
            exam_type: 'school',
            term: '2026-2027-1',
            status: 'active',
            remark: null,
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', exam_date: null, status: 'active', remark: null }],
          },
        })
      }
      if (url === `/exams/${id}/score-sheet`) {
        return Promise.resolve({
          data: {
            exam: { id, name: id === 7 ? '期中考试' : '期末考试', exam_type: 'school', term: '2026-2027-1' },
            classes: [{ id: 1, name: '一班' }],
            subjects: [{ exam_subject_id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' }],
            students: [],
            scores: [],
          },
        })
      }
      return Promise.resolve({ data: {} })
    })
    const wrapper = mount(ExamDetailView, {
      global: {
        stubs: {
          'el-button': buttonStub,
          'el-table': tableStub,
          'el-table-column': tableColumnStub,
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('期中考试')

    routerMocks.route.params.id = '8'
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/exams/8')
    expect(get).toHaveBeenCalledWith('/exams/8/score-sheet')
    expect(wrapper.text()).toContain('期末考试')
  })

  it('ignores stale exam detail responses after a faster route change', async () => {
    routerMocks.route.params.id = '7'
    const firstExam = deferred<{ data: ReturnType<typeof examRecord> }>()
    const firstSheet = deferred<{ data: ReturnType<typeof scoreSheet> }>()
    const get = vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/exams/7') return firstExam.promise
      if (url === '/exams/7/score-sheet') return firstSheet.promise
      if (url === '/exams/8') return Promise.resolve({ data: examRecord(8, '期末考试') })
      if (url === '/exams/8/score-sheet') return Promise.resolve({ data: scoreSheet(8, '期末考试') })
      return Promise.resolve({ data: {} })
    })
    const wrapper = mount(ExamDetailView, {
      global: {
        stubs: {
          'el-button': buttonStub,
          'el-table': tableStub,
          'el-table-column': tableColumnStub,
        },
        directives: { loading: {} },
      },
    })

    routerMocks.route.params.id = '8'
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/exams/8')
    expect(get).toHaveBeenCalledWith('/exams/8/score-sheet')
    expect(wrapper.text()).toContain('期末考试')

    firstExam.resolve({ data: examRecord(7, '期中考试') })
    firstSheet.resolve({ data: scoreSheet(7, '期中考试') })
    await flushPromises()

    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).not.toContain('期中考试')
  })
})
