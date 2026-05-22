import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import ScoreEntryTable from '../src/components/scores/ScoreEntryTable.vue'
import ScoreImportDialog from '../src/components/scores/ScoreImportDialog.vue'
import ScoreEntryView from '../src/views/ScoreEntryView.vue'
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

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((innerResolve, innerReject) => {
    resolve = innerResolve
    reject = innerReject
  })
  return { promise, resolve, reject }
}

function scoreSheet(id: number, name: string, status = 'active') {
  return {
    exam: { id, name, exam_type: 'school', term: '2026-2027-1', status },
    classes: [{ id: 1, name: '一班' }],
    subjects: [{ exam_subject_id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' }],
    students: [
      { exam_student_id: 21, student_id: 1, class_id: 1, student_no: 'S001', name: '张三', status: 'active' },
      { exam_student_id: 22, student_id: 2, class_id: 1, student_no: 'S002', name: '李四', status: 'active' },
    ],
    scores: [],
  }
}

function multiScoreSheet(id: number, name: string, status = 'active') {
  return {
    exam: { id, name, exam_type: 'school', term: '2026-2027-1', status },
    classes: [
      { id: 1, name: '一班' },
      { id: 2, name: '二班' },
    ],
    subjects: [
      { exam_subject_id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' },
      { exam_subject_id: 12, course_id: 4, course_name: '语文', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' },
    ],
    students: [
      { exam_student_id: 21, student_id: 1, class_id: 1, student_no: 'S001', name: '张三', status: 'active' },
      { exam_student_id: 22, student_id: 2, class_id: 2, student_no: 'S002', name: '李四', status: 'active' },
    ],
    scores: [],
  }
}

describe('score entry table', () => {
  it('supports focused and whole-exam modes', () => {
    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        students: [{ exam_student_id: 1, name: '张三', student_no: 'S001', class_id: 1 }],
        subjects: [{ exam_subject_id: 1, course_name: '数学', full_score: '100.00' }],
        scores: [],
        failedItems: [],
      },
      global: {
        stubs: {
          'el-input-number': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-table': { template: '<div />' },
          'el-table-column': { template: '<div />' },
        },
      },
    })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('数学')
  })

  it('whole-exam mode ignores the class filter', () => {
    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        classId: 1,
        students: [
          { exam_student_id: 1, name: '张三', student_no: 'S001', class_id: 1 },
          { exam_student_id: 2, name: '李四', student_no: 'S002', class_id: 2 },
        ],
        subjects: [{ exam_subject_id: 1, course_name: '数学', full_score: '100.00' }],
        scores: [],
        failedItems: [],
      },
      global: {
        stubs: {
          'el-input-number': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-table': { template: '<div />' },
          'el-table-column': { template: '<div />' },
        },
      },
    })

    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('李四')
  })

  it('does not emit existing scores as dirty until a cell changes', async () => {
    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        students: [{ exam_student_id: 1, name: '张三', student_no: 'S001', class_id: 1 }],
        subjects: [{ exam_subject_id: 1, course_name: '数学', full_score: '100.00' }],
        scores: [{ exam_student_id: 1, exam_subject_id: 1, score: '88', score_status: 'normal', remark: null }],
        failedItems: [],
      },
      global: {
        stubs: {
          'el-input-number': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-table': { template: '<div />' },
          'el-table-column': { template: '<div />' },
        },
      },
    })
    await flushPromises()

    const initialChanges = wrapper.emitted('change') || []
    expect(initialChanges[initialChanges.length - 1]?.[0]).toEqual([])

    const view = wrapper.vm as unknown as { updateScore: (examStudentId: number, examSubjectId: number, score: number) => void }
    view.updateScore(1, 1, 90)
    await flushPromises()

    const changedEvents = wrapper.emitted('change') || []
    expect(changedEvents[changedEvents.length - 1]?.[0]).toEqual([
      { exam_student_id: 1, exam_subject_id: 1, score: '90', score_status: 'normal', remark: null },
    ])
  })

  it('builds baseline drafts from keyed score lookups', async () => {
    const scores = [{ exam_student_id: 1, exam_subject_id: 1, score: '88', score_status: 'normal' as const, remark: null }]
    scores.find = vi.fn(() => {
      throw new Error('linear score lookup used')
    }) as typeof scores.find

    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        students: [{ exam_student_id: 1, name: '张三', student_no: 'S001', class_id: 1 }],
        subjects: [{ exam_subject_id: 1, course_name: '数学', full_score: '100.00' }],
        scores,
        failedItems: [],
      },
      global: {
        stubs: {
          'el-input-number': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-table': { template: '<div />' },
          'el-table-column': { template: '<div />' },
        },
      },
    })
    await flushPromises()

    const initialChanges = wrapper.emitted('change') || []
    expect(initialChanges[initialChanges.length - 1]?.[0]).toEqual([])
  })

  it('removes confirmed saved cells from later dirty change events', async () => {
    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        students: [
          { exam_student_id: 21, name: '张三', student_no: 'S001', class_id: 1 },
          { exam_student_id: 22, name: '李四', student_no: 'S002', class_id: 1 },
        ],
        subjects: [{ exam_subject_id: 11, course_name: '数学', full_score: '100.00' }],
        scores: [],
        failedItems: [],
        savedItems: [],
      },
      global: {
        stubs: {
          'el-input-number': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-table': { template: '<div />' },
          'el-table-column': { template: '<div />' },
        },
      },
    })

    const view = wrapper.vm as unknown as { updateScore: (examStudentId: number, examSubjectId: number, score: number) => void }
    view.updateScore(21, 11, 88)
    view.updateScore(22, 11, 110)
    await flushPromises()

    await wrapper.setProps({
      savedItems: [{ exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null }],
    })
    await flushPromises()

    const changes = wrapper.emitted('change') || []
    expect(changes[changes.length - 1]?.[0]).toEqual([
      { exam_student_id: 22, exam_subject_id: 11, score: '110', score_status: 'normal', remark: null },
    ])
  })

  it('does not emit score edits while disabled during save', async () => {
    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        disabled: true,
        students: [{ exam_student_id: 21, name: '张三', student_no: 'S001', class_id: 1 }],
        subjects: [{ exam_subject_id: 11, course_name: '数学', full_score: '100.00' }],
        scores: [],
        failedItems: [],
      },
      global: {
        stubs: {
          'el-input-number': { template: '<input />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-select': { template: '<div><slot /></div>' },
          'el-table': { template: '<div />' },
          'el-table-column': { template: '<div />' },
        },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      updateScore: (examStudentId: number, examSubjectId: number, score: number) => void
      updateStatus: (examStudentId: number, examSubjectId: number, status: string) => void
    }
    view.updateScore(21, 11, 88)
    view.updateStatus(21, 11, 'absent')
    await flushPromises()

    const changes = wrapper.emitted('change') || []
    expect(changes[changes.length - 1]?.[0]).toEqual([])
  })

  it('loads row-level import errors after score import', async () => {
    const post = vi.spyOn(http, 'post').mockResolvedValue({
      data: { batch_id: 8, status: 'partial_success', success_count: 3, failed_count: 1, error_summary: '1 行失败' },
    })
    const get = vi.spyOn(http, 'get').mockResolvedValue({
      data: {
        items: [{ id: 1, batch_id: 8, row_number: 5, field: 'score', raw_value: '110', reason: '分数不能超过满分', raw_data: null, created_at: '' }],
        total: 1,
        page: 1,
        page_size: 20,
      },
    })
    const wrapper = mount(ScoreImportDialog, {
      props: { modelValue: true, examId: 7 },
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-dialog': { template: '<div><slot /></div>' },
          'el-table': { props: ['data'], template: '<div><div v-for="row in data" :key="row.id">{{ Object.values(row).join(" ") }}</div></div>' },
          'el-table-column': { template: '<div />' },
          'el-upload': { template: '<div><slot /></div>' },
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    const view = wrapper.vm as unknown as { uploadScoreFile: (options: { file: File }) => Promise<void> }
    await view.uploadScoreFile({ file: new File(['score'], 'scores.xlsx') })
    await flushPromises()

    expect(post).toHaveBeenCalledWith('/exams/7/scores/import', expect.any(FormData), expect.any(Object))
    expect(get).toHaveBeenCalledWith('/imports/8/errors', expect.objectContaining({ params: expect.objectContaining({ page: 1, page_size: 100 }) }))
    expect(wrapper.text()).toContain('分数不能超过满分')
  })

  it('emits imported even when row-level import errors fail to load', async () => {
    vi.spyOn(http, 'post').mockResolvedValue({
      data: { batch_id: 8, status: 'partial_success', success_count: 3, failed_count: 1, error_summary: '1 行失败' },
    })
    vi.spyOn(http, 'get').mockRejectedValue(new Error('errors unavailable'))
    const wrapper = mount(ScoreImportDialog, {
      props: { modelValue: true, examId: 7 },
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-dialog': { template: '<div><slot /></div>' },
          'el-table': { props: ['data'], template: '<div><div v-for="row in data" :key="row.id">{{ Object.values(row).join(" ") }}</div></div>' },
          'el-table-column': { template: '<div />' },
          'el-upload': { template: '<div><slot /></div>' },
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    const view = wrapper.vm as unknown as { uploadScoreFile: (options: { file: File }) => Promise<void> }
    await view.uploadScoreFile({ file: new File(['score'], 'scores.xlsx') })
    await flushPromises()

    expect(wrapper.emitted('imported')?.[0]?.[0]).toMatchObject({ batch_id: 8, success_count: 3, failed_count: 1 })
  })

  it('reloads score sheet when route id changes', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    const get = vi.spyOn(http, 'get').mockImplementation((url: string) => {
      const id = url.includes('/8') ? 8 : 7
      return Promise.resolve({
        data: {
          exam: { id, name: id === 7 ? '期中考试' : '期末考试', exam_type: 'school', term: '2026-2027-1' },
          classes: [{ id: 1, name: '一班' }],
          subjects: [{ exam_subject_id: 11, course_id: 3, course_name: '数学', full_score: '100', pass_score: '60', excellent_score: '90', status: 'active' }],
          students: [],
          scores: [],
        },
      })
    })
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('期中考试')

    routerMocks.route.params.id = '8'
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/exams/8/score-sheet')
    expect(wrapper.text()).toContain('期末考试')
  })

  it('ignores stale score sheet responses after a faster route change', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    const firstLoad = deferred<{ data: ReturnType<typeof scoreSheet> }>()
    const get = vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/exams/7/score-sheet') return firstLoad.promise
      if (url === '/exams/8/score-sheet') return Promise.resolve({ data: scoreSheet(8, '期末考试') })
      return Promise.resolve({ data: {} })
    })
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })

    routerMocks.route.params.id = '8'
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/exams/8/score-sheet')
    expect(wrapper.text()).toContain('期末考试')

    firstLoad.resolve({ data: scoreSheet(7, '期中考试') })
    await flushPromises()

    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).not.toContain('期中考试')
  })

  it('keeps only failed cells dirty after a partial bulk save', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    vi.spyOn(http, 'get').mockResolvedValue({ data: scoreSheet(7, '期中考试') })
    const put = vi
      .spyOn(http, 'put')
      .mockResolvedValueOnce({
        data: {
          success_count: 1,
          failure_count: 1,
          failed_items: [{ index: 1, exam_student_id: 22, exam_subject_id: 11, reason: '分数不能超过满分 100.00' }],
        },
      })
      .mockResolvedValueOnce({
        data: {
          success_count: 1,
          failure_count: 0,
          failed_items: [],
        },
      })
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      bulkSave: () => Promise<void>
      handleTableChange: (items: Array<{ exam_student_id: number; exam_subject_id: number; score: string; score_status: string; remark: null }>) => void
    }
    view.handleTableChange([
      { exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null },
      { exam_student_id: 22, exam_subject_id: 11, score: '110', score_status: 'normal', remark: null },
    ])
    await view.bulkSave()
    await flushPromises()
    await view.bulkSave()
    await flushPromises()

    expect(put).toHaveBeenNthCalledWith(1, '/exams/7/scores', {
      items: [
        { exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null },
        { exam_student_id: 22, exam_subject_id: 11, score: '110', score_status: 'normal', remark: null },
      ],
    })
    expect(put).toHaveBeenNthCalledWith(2, '/exams/7/scores', {
      items: [{ exam_student_id: 22, exam_subject_id: 11, score: '110', score_status: 'normal', remark: null }],
    })
  })

  it('ignores stale save responses after navigating to another exam', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/exams/7/score-sheet') return Promise.resolve({ data: scoreSheet(7, '期中考试') })
      if (url === '/exams/8/score-sheet') return Promise.resolve({ data: scoreSheet(8, '期末考试') })
      return Promise.resolve({ data: {} })
    })
    const firstSave = deferred<{
      data: { success_count: number; failure_count: number; failed_items: Array<{ index: number; exam_student_id: number; exam_subject_id: number; reason: string }> }
    }>()
    const put = vi.spyOn(http, 'put').mockImplementation(() => firstSave.promise)
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      bulkSave: () => Promise<void>
      handleTableChange: (items: Array<{ exam_student_id: number; exam_subject_id: number; score: string; score_status: string; remark: null }>) => void
    }
    view.handleTableChange([{ exam_student_id: 21, exam_subject_id: 11, score: '110', score_status: 'normal', remark: null }])
    const savePromise = view.bulkSave()

    routerMocks.route.params.id = '8'
    await flushPromises()
    expect(wrapper.text()).toContain('期末考试')

    firstSave.resolve({
      data: {
        success_count: 0,
        failure_count: 1,
        failed_items: [{ index: 0, exam_student_id: 21, exam_subject_id: 11, reason: '分数不能超过满分 100.00' }],
      },
    })
    await savePromise
    await flushPromises()

    expect(wrapper.text()).not.toContain('保存中')
    await view.bulkSave()

    expect(put).toHaveBeenCalledTimes(1)
  })

  it('clears save loading after a stale save finishes on another exam', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/exams/7/score-sheet') return Promise.resolve({ data: scoreSheet(7, '期中考试') })
      if (url === '/exams/8/score-sheet') return Promise.resolve({ data: scoreSheet(8, '期末考试') })
      return Promise.resolve({ data: {} })
    })
    const firstSave = deferred<{ data: { success_count: number; failure_count: number; failed_items: [] } }>()
    vi.spyOn(http, 'put').mockImplementation(() => firstSave.promise)
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { props: ['loading'], template: '<button>{{ loading ? "保存中" : "" }}<slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      bulkSave: () => Promise<void>
      handleTableChange: (items: Array<{ exam_student_id: number; exam_subject_id: number; score: string; score_status: string; remark: null }>) => void
    }
    view.handleTableChange([{ exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null }])
    const savePromise = view.bulkSave()
    await flushPromises()
    expect(wrapper.text()).toContain('保存中')

    routerMocks.route.params.id = '8'
    await flushPromises()
    firstSave.resolve({ data: { success_count: 1, failure_count: 0, failed_items: [] } })
    await savePromise
    await flushPromises()

    expect(wrapper.text()).toContain('期末考试')
    expect(wrapper.text()).not.toContain('保存中')
  })

  it('keeps newer save loading when an older save finishes', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    vi.spyOn(http, 'get').mockImplementation((url: string) => {
      if (url === '/exams/7/score-sheet') return Promise.resolve({ data: scoreSheet(7, '期中考试') })
      if (url === '/exams/8/score-sheet') return Promise.resolve({ data: scoreSheet(8, '期末考试') })
      return Promise.resolve({ data: {} })
    })
    const firstSave = deferred<{ data: { success_count: number; failure_count: number; failed_items: [] } }>()
    const secondSave = deferred<{ data: { success_count: number; failure_count: number; failed_items: [] } }>()
    vi.spyOn(http, 'put').mockImplementationOnce(() => firstSave.promise).mockImplementationOnce(() => secondSave.promise)
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { props: ['loading'], template: '<button>{{ loading ? "保存中" : "" }}<slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      bulkSave: () => Promise<void>
      handleTableChange: (items: Array<{ exam_student_id: number; exam_subject_id: number; score: string; score_status: string; remark: null }>) => void
    }
    view.handleTableChange([{ exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null }])
    const firstSavePromise = view.bulkSave()

    routerMocks.route.params.id = '8'
    await flushPromises()
    view.handleTableChange([{ exam_student_id: 21, exam_subject_id: 11, score: '91', score_status: 'normal', remark: null }])
    const secondSavePromise = view.bulkSave()
    await flushPromises()
    expect(wrapper.text()).toContain('保存中')

    firstSave.resolve({ data: { success_count: 1, failure_count: 0, failed_items: [] } })
    await firstSavePromise
    await flushPromises()

    expect(wrapper.text()).toContain('保存中')

    secondSave.resolve({ data: { success_count: 1, failure_count: 0, failed_items: [] } })
    await secondSavePromise
  })

  it('disables score mutations when the exam is inactive', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    vi.spyOn(http, 'get').mockResolvedValue({ data: scoreSheet(7, '期中考试', 'inactive') })
    const put = vi.spyOn(http, 'put').mockResolvedValue({ data: { success_count: 1, failure_count: 0, failed_items: [] } })
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { props: ['disabled'], template: '<button>{{ disabled ? "禁用" : "" }}<slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { props: ['disabled'], template: '<div>{{ disabled ? "成绩表禁用" : "" }}</div>' },
          ScoreImportDialog: { props: ['disabled'], template: '<div>{{ disabled ? "导入禁用" : "" }}</div>' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      bulkSave: () => Promise<void>
      handleTableChange: (items: Array<{ exam_student_id: number; exam_subject_id: number; score: string; score_status: string; remark: null }>) => void
    }
    view.handleTableChange([{ exam_student_id: 21, exam_subject_id: 11, score: '88', score_status: 'normal', remark: null }])
    await view.bulkSave()

    expect(wrapper.text()).toContain('成绩表禁用')
    expect(wrapper.text()).toContain('导入禁用')
    expect(put).not.toHaveBeenCalled()
  })

  it('keeps the selected class and subject after save reloads the sheet', async () => {
    routerMocks.route.params.id = '7'
    routerMocks.route.query = {}
    vi.spyOn(http, 'get').mockResolvedValue({ data: multiScoreSheet(7, '期中考试') })
    vi.spyOn(http, 'put').mockResolvedValue({ data: { success_count: 1, failure_count: 0, failed_items: [] } })
    const wrapper = mount(ScoreEntryView, {
      global: {
        stubs: {
          'el-button': { template: '<button><slot /></button>' },
          'el-empty': { template: '<div />' },
          'el-option': { props: ['label'], template: '<span>{{ label }}</span>' },
          'el-segmented': { template: '<div />' },
          'el-select': { template: '<div><slot /></div>' },
          ScoreEntryTable: { template: '<div />' },
          ScoreImportDialog: { template: '<div />' },
        },
        directives: { loading: {} },
      },
    })
    await flushPromises()

    const view = wrapper.vm as unknown as {
      filters: { class_id?: number; subject_id?: number }
      bulkSave: () => Promise<void>
      handleTableChange: (items: Array<{ exam_student_id: number; exam_subject_id: number; score: string; score_status: string; remark: null }>) => void
    }
    view.filters.class_id = 2
    view.filters.subject_id = 12
    view.handleTableChange([{ exam_student_id: 22, exam_subject_id: 12, score: '88', score_status: 'normal', remark: null }])

    await view.bulkSave()
    await flushPromises()

    expect(view.filters.class_id).toBe(2)
    expect(view.filters.subject_id).toBe(12)
  })

  it('ignores stale score import results after the dialog switches exams', async () => {
    const firstUpload = deferred<{ data: { batch_id: number; status: string; success_count: number; failed_count: number; error_summary: string } }>()
    vi.spyOn(http, 'post').mockImplementation(() => firstUpload.promise)
    vi.spyOn(http, 'get').mockResolvedValue({
      data: {
        items: [{ id: 1, batch_id: 8, row_number: 5, field: 'score', raw_value: '110', reason: '旧考试错误', raw_data: null, created_at: '' }],
        total: 1,
        page: 1,
        page_size: 20,
      },
    })
    const wrapper = mount(ScoreImportDialog, {
      props: { modelValue: true, examId: 7 },
      global: {
        stubs: {
          'el-button': { props: ['loading'], template: '<button>{{ loading ? "上传中" : "" }}<slot /></button>' },
          'el-dialog': { template: '<div><slot /></div>' },
          'el-table': { props: ['data'], template: '<div><div v-for="row in data" :key="row.id">{{ Object.values(row).join(" ") }}</div></div>' },
          'el-table-column': { template: '<div />' },
          'el-upload': { template: '<div><slot /></div>' },
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    const view = wrapper.vm as unknown as { uploadScoreFile: (options: { file: File }) => Promise<void> }
    const uploadPromise = view.uploadScoreFile({ file: new File(['score'], 'scores.xlsx') })
    await wrapper.setProps({ examId: 8 })
    firstUpload.resolve({ data: { batch_id: 8, status: 'partial_success', success_count: 0, failed_count: 1, error_summary: '旧考试失败' } })
    await uploadPromise
    await flushPromises()

    expect(wrapper.text()).not.toContain('旧考试错误')
    expect(wrapper.emitted('imported')).toBeUndefined()
  })

  it('keeps newer upload loading when an older upload finishes', async () => {
    const firstUpload = deferred<{ data: { batch_id: number; status: string; success_count: number; failed_count: number; error_summary: string } }>()
    const secondUpload = deferred<{ data: { batch_id: number; status: string; success_count: number; failed_count: number; error_summary: string } }>()
    vi.spyOn(http, 'post').mockImplementationOnce(() => firstUpload.promise).mockImplementationOnce(() => secondUpload.promise)
    const wrapper = mount(ScoreImportDialog, {
      props: { modelValue: true, examId: 7 },
      global: {
        stubs: {
          'el-button': { props: ['loading'], template: '<button>{{ loading ? "上传中" : "" }}<slot /></button>' },
          'el-dialog': { template: '<div><slot /></div>' },
          'el-table': { props: ['data'], template: '<div><div v-for="row in data" :key="row.id">{{ Object.values(row).join(" ") }}</div></div>' },
          'el-table-column': { template: '<div />' },
          'el-upload': { template: '<div><slot /></div>' },
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    const view = wrapper.vm as unknown as { uploadScoreFile: (options: { file: File }) => Promise<void> }
    const firstUploadPromise = view.uploadScoreFile({ file: new File(['score'], 'scores.xlsx') })
    await wrapper.setProps({ examId: 8 })
    const secondUploadPromise = view.uploadScoreFile({ file: new File(['score'], 'scores-2.xlsx') })
    await flushPromises()
    expect(wrapper.text()).toContain('上传中')

    firstUpload.resolve({ data: { batch_id: 8, status: 'success', success_count: 1, failed_count: 0, error_summary: '' } })
    await firstUploadPromise
    await flushPromises()

    expect(wrapper.text()).toContain('上传中')

    secondUpload.resolve({ data: { batch_id: 9, status: 'success', success_count: 1, failed_count: 0, error_summary: '' } })
    await secondUploadPromise
  })
})
