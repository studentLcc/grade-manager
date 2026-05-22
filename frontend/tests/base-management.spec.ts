import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ClassesStudentsView from '../src/views/ClassesStudentsView.vue'
import CoursesScheduleView from '../src/views/CoursesScheduleView.vue'
import ImportResultPanel from '../src/components/imports/ImportResultPanel.vue'
import { http } from '../src/api/http'

const mocks = vi.hoisted(() => ({
  emptyPage: { items: [], total: 0, page: 1, page_size: 20 },
}))

const tableSlotStub = { template: '<div><slot /></div>' }
const tableColumnStub = {
  props: ['label'],
  template: '<div class="table-column">{{ label }}<slot /></div>',
}
const dataTableStub = {
  props: ['data'],
  template: `
    <div>
      <slot />
      <div v-for="row in data" :key="row.id || row.student_no" class="table-row">
        {{ Object.entries(row).filter(([key]) => key !== 'status').map(([, value]) => value).join(' ') }}
      </div>
    </div>
  `,
}
const inputStub = { template: '<input />' }
const buttonStub = { template: '<button><slot /></button>' }
const paginationStub = { template: '<nav />' }
const selectStub = {
  props: { clearable: Boolean },
  template: '<div class="select-stub" :data-clearable="String(Boolean(clearable))"><slot /></div>',
}
const optionStub = {
  props: ['label'],
  template: '<span>{{ label }}</span>',
}
const routerLinkStub = {
  props: ['to'],
  template: '<a><slot /></a>',
}
const elementStubs = {
  'el-button': buttonStub,
  'el-dialog': tableSlotStub,
  'el-form': tableSlotStub,
  'el-form-item': tableSlotStub,
  'el-input': inputStub,
  'el-input-number': inputStub,
  'el-option': optionStub,
  'el-pagination': paginationStub,
  'el-select': tableSlotStub,
  'el-table': tableSlotStub,
  'el-table-column': tableColumnStub,
  'el-tabs': tableSlotStub,
  'el-tab-pane': tableSlotStub,
  'el-time-select': inputStub,
  'el-upload': tableSlotStub,
  RouterLink: routerLinkStub,
}

function testGlobal(stubs = {}) {
  return {
    plugins: [createPinia()],
    stubs: { ...elementStubs, ...stubs },
    directives: { loading: {} },
  }
}

describe('base management views', () => {
  beforeEach(() => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: mocks.emptyPage })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllEnvs()
  })

  it('renders class and student controls on one page', () => {
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    expect(wrapper.text()).toContain('班级与学生')
    expect(wrapper.text()).toContain('导入学生')
    expect(wrapper.text()).toContain('新增学生')
  })

  it('renders course and weekly schedule tabs', () => {
    const wrapper = mount(CoursesScheduleView, {
      global: testGlobal(),
    })
    expect(wrapper.text()).toContain('课程管理')
    expect(wrapper.text()).toContain('周课表')
    expect(wrapper.text()).not.toContain('课程编码')
  })

  it('renders schedule class context and clearable class filter', () => {
    const wrapper = mount(CoursesScheduleView, {
      global: {
        ...testGlobal({
          'el-select': selectStub,
        }),
      },
    })

    expect(wrapper.text()).toContain('班级')
    expect(wrapper.find('[data-clearable="true"]').exists()).toBe(true)
  })

  it('resets student page when list filters change', async () => {
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    const view = wrapper.vm as unknown as { studentFilters: { keyword: string; page: number } }

    view.studentFilters.page = 3
    view.studentFilters.keyword = '张三'
    await wrapper.vm.$nextTick()

    expect(view.studentFilters.page).toBe(1)
  })

  it('passes status filters to course and schedule lists', async () => {
    const get = vi.mocked(http.get)

    mount(CoursesScheduleView, {
      global: testGlobal(),
    })
    await flushPromises()

    expect(get).toHaveBeenCalledWith(
      '/courses',
      expect.objectContaining({ params: expect.objectContaining({ status: 'active' }) }),
    )
    expect(get).toHaveBeenCalledWith(
      '/schedules',
      expect.objectContaining({ params: expect.objectContaining({ status: 'active' }) }),
    )
  })

  it('loads active class and course options independently from table filters', async () => {
    const get = vi.mocked(http.get)
    const classesWrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    await flushPromises()
    get.mockClear()

    const classesView = classesWrapper.vm as unknown as {
      classFilters: { status: string }
      loadClassOptions: () => Promise<void>
    }
    classesView.classFilters.status = 'archived'
    await flushPromises()
    await classesView.loadClassOptions()

    expect(get).toHaveBeenCalledWith(
      '/classes',
      expect.objectContaining({ params: expect.objectContaining({ status: 'archived' }) }),
    )
    expect(get).toHaveBeenCalledWith(
      '/classes',
      expect.objectContaining({ params: expect.objectContaining({ status: 'active' }) }),
    )

    const coursesWrapper = mount(CoursesScheduleView, {
      global: testGlobal(),
    })
    await flushPromises()
    get.mockClear()

    const coursesView = coursesWrapper.vm as unknown as {
      courseFilters: { status: string }
      loadCourseOptions: () => Promise<void>
    }
    coursesView.courseFilters.status = 'inactive'
    await flushPromises()
    await coursesView.loadCourseOptions()

    expect(get).toHaveBeenCalledWith(
      '/courses',
      expect.objectContaining({ params: expect.objectContaining({ status: 'inactive' }) }),
    )
    expect(get).toHaveBeenCalledWith(
      '/courses',
      expect.objectContaining({ params: expect.objectContaining({ status: 'active' }) }),
    )
  })

  it('renders backend import failed_count field', () => {
    const wrapper = mount(ImportResultPanel, {
      props: {
        result: {
          batch_id: 7,
          status: 'partial_success',
          success_count: 8,
          failed_count: 2,
        },
      },
      global: { stubs: { RouterLink: routerLinkStub } },
    })

    expect(wrapper.text()).toContain('部分成功')
    expect(wrapper.text()).not.toContain('partial_success')
    expect(wrapper.text()).toContain('8')
    expect(wrapper.text()).toContain('2')
  })

  it('renders teacher-facing status values in Chinese', async () => {
    vi.mocked(http.get).mockImplementation((url: string) => {
      if (url === '/students') {
        return Promise.resolve({
          data: {
            items: [{ id: 2, student_no: 'S001', name: '张三', class_id: 1, gender: null, status: 'archived', remark: null }],
            total: 1,
            page: 1,
            page_size: 20,
          },
        })
      }
      if (url === '/classes') {
        return Promise.resolve({
          data: {
            items: [{ id: 1, name: '一班', grade: '七年级', academic_year: '2026-2027', status: 'active', remark: null }],
            total: 1,
            page: 1,
            page_size: 20,
          },
        })
      }
      if (url === '/courses') {
        return Promise.resolve({
          data: { items: [{ id: 3, course_name: '数学', status: 'inactive', remark: null }], total: 1, page: 1, page_size: 20 },
        })
      }
      if (url === '/schedules') {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 4,
                class_id: 1,
                course_id: 3,
                weekday: 1,
                period_no: 2,
                start_time: null,
                end_time: null,
                location: null,
                status: 'active',
                remark: null,
              },
            ],
            total: 1,
            page: 1,
            page_size: 20,
          },
        })
      }
      return Promise.resolve({ data: mocks.emptyPage })
    })

    const classStudentWrapper = mount(ClassesStudentsView, {
      global: testGlobal({ 'el-table': dataTableStub }),
    })
    const coursesScheduleWrapper = mount(CoursesScheduleView, {
      global: testGlobal({ 'el-table': dataTableStub }),
    })

    await flushPromises()

    expect(classStudentWrapper.text()).toContain('启用')
    expect(classStudentWrapper.text()).toContain('归档')
    expect(classStudentWrapper.text()).not.toContain(' active ')
    expect(classStudentWrapper.text()).not.toContain(' archived ')
    expect(coursesScheduleWrapper.text()).toContain('停用')
    expect(coursesScheduleWrapper.text()).toContain('启用')
    expect(coursesScheduleWrapper.text()).not.toContain(' inactive ')
  })

  it('renders import status in Chinese instead of raw enum values', () => {
    const wrapper = mount(ImportResultPanel, {
      props: {
        result: {
          batch_id: 7,
          status: 'partial_success',
          success_count: 8,
          failed_count: 2,
        },
      },
      global: { stubs: { RouterLink: routerLinkStub } },
    })

    expect(wrapper.text()).toContain('部分成功')
    expect(wrapper.text()).not.toContain('partial_success')
  })

  it('uploads student imports through configured http client', async () => {
    const { http } = await import('../src/api/http')
    const post = vi.spyOn(http, 'post').mockResolvedValue({
      data: { batch_id: 1, status: 'success', success_count: 1, failed_count: 0 },
    })
    const { importStudents } = await import('../src/api/students')
    const file = new File(['student_no,name\nS001,张三'], 'students.csv', { type: 'text/csv' })

    await importStudents(3, file)

    expect(post).toHaveBeenCalledWith(
      '/students/import',
      expect.any(FormData),
      expect.objectContaining({
        params: { target_class_id: 3 },
      }),
    )
    post.mockRestore()
  })

  it('keeps table list requests bounded to the current backend page', async () => {
    const get = vi.mocked(http.get)
    get.mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      const params = config?.params || {}
      const page = Number(params.page || 1)
      const pageSize = Number(params.page_size || 20)
      if (url === '/classes') {
        return Promise.resolve({
          data: { items: page === 1 ? [{ id: pageSize, name: '一班', grade: null, academic_year: null, status: 'active', remark: null }] : [], total: 250, page, page_size: pageSize },
        })
      }
      if (url === '/courses') {
        return Promise.resolve({
          data: { items: page === 1 ? [{ id: pageSize, course_name: '数学', status: 'active', remark: null }] : [], total: 250, page, page_size: pageSize },
        })
      }
      if (url === '/schedules') {
        return Promise.resolve({
          data: {
            items:
              page === 1
                ? [
                    {
                      id: pageSize,
                      class_id: 1,
                      course_id: 1,
                      weekday: 1,
                      period_no: 1,
                      start_time: null,
                      end_time: null,
                      location: null,
                      status: 'active',
                      remark: null,
                    },
                  ]
                : [],
            total: 250,
            page,
            page_size: pageSize,
          },
        })
      }
      return Promise.resolve({ data: mocks.emptyPage })
    })

    mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    mount(CoursesScheduleView, {
      global: testGlobal(),
    })
    await flushPromises()

    expect(get).toHaveBeenCalledWith('/classes', expect.objectContaining({ params: expect.objectContaining({ page: 1, page_size: 20 }) }))
    expect(get).not.toHaveBeenCalledWith('/classes', expect.objectContaining({ params: expect.objectContaining({ page: 2, page_size: 20 }) }))
    expect(get).toHaveBeenCalledWith('/courses', expect.objectContaining({ params: expect.objectContaining({ page: 1, page_size: 20 }) }))
    expect(get).not.toHaveBeenCalledWith('/courses', expect.objectContaining({ params: expect.objectContaining({ page: 2, page_size: 20 }) }))
    expect(get).toHaveBeenCalledWith('/schedules', expect.objectContaining({ params: expect.objectContaining({ page: 1, page_size: 20 }) }))
    expect(get).not.toHaveBeenCalledWith('/schedules', expect.objectContaining({ params: expect.objectContaining({ page: 2, page_size: 20 }) }))
  })

  it('contains rejected save and import requests locally', async () => {
    vi.spyOn(http, 'post').mockRejectedValue(new Error('network failed'))
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    const file = new File(['student_no,name\nS001,张三'], 'students.csv', { type: 'text/csv' })
    const view = wrapper.vm as unknown as {
      classDialogVisible: boolean
      classForm: { name: string }
      classFormRef: { validate: () => Promise<boolean> }
      openCreateClassDialog: () => void
      saveClass: () => Promise<void>
      studentFilters: { class_id: number | undefined }
      uploadStudents: (options: { file: File }) => Promise<void>
    }

    view.openCreateClassDialog()
    view.classForm.name = '一班'
    view.classFormRef = { validate: () => Promise.resolve(true) }

    await expect(view.saveClass()).resolves.toBeUndefined()
    expect(view.classDialogVisible).toBe(true)

    view.studentFilters.class_id = 1
    await expect(view.uploadStudents({ file })).resolves.toBeUndefined()
  })

  it('sends status in update payloads for course and schedule edits', async () => {
    const { http } = await import('../src/api/http')
    const patch = vi.spyOn(http, 'patch').mockResolvedValue({ data: {} })
    const { updateCourse } = await import('../src/api/courses')
    const { updateSchedule } = await import('../src/api/schedules')

    await updateCourse(2, { course_name: '数学', status: 'inactive' })
    await updateSchedule(3, { class_id: 1, course_id: 2, weekday: 1, period_no: 2, status: 'archived' })

    expect(patch).toHaveBeenCalledWith('/courses/2', expect.objectContaining({ status: 'inactive' }))
    expect(patch).toHaveBeenCalledWith('/schedules/3', expect.objectContaining({ status: 'archived' }))
    patch.mockRestore()
  })

  it('sends status when editing classes and students', async () => {
    const patch = vi.spyOn(http, 'patch').mockResolvedValue({ data: {} })
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    const view = wrapper.vm as unknown as {
      classForm: { status: string }
      classFormRef: { validate: () => Promise<boolean> }
      openEditClassDialog: (record: {
        id: number
        name: string
        grade: string | null
        academic_year: string | null
        status: string
        remark: string | null
      }) => void
      saveClass: () => Promise<void>
      studentForm: { status: string }
      studentFormRef: { validate: () => Promise<boolean> }
      openEditStudentDialog: (record: {
        id: number
        student_no: string
        name: string
        gender: string | null
        class_id: number | null
        status: string
        remark: string | null
      }) => void
      saveStudent: () => Promise<void>
    }

    view.classFormRef = { validate: () => Promise.resolve(true) }
    view.openEditClassDialog({
      id: 1,
      name: '一年级一班',
      grade: '一年级',
      academic_year: '2025-2026',
      status: 'active',
      remark: null,
    })
    view.classForm.status = 'inactive'
    await view.saveClass()

    view.studentFormRef = { validate: () => Promise.resolve(true) }
    view.openEditStudentDialog({
      id: 2,
      student_no: 'S001',
      name: '张三',
      gender: null,
      class_id: 1,
      status: 'active',
      remark: null,
    })
    view.studentForm.status = 'archived'
    await view.saveStudent()

    expect(patch).toHaveBeenCalledWith('/classes/1', expect.objectContaining({ status: 'inactive' }))
    expect(patch).toHaveBeenCalledWith('/students/2', expect.objectContaining({ status: 'archived' }))
  })

  it('switches status filters to active after creates', async () => {
    vi.spyOn(http, 'post').mockResolvedValue({ data: { id: 1 } })
    const classesWrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })
    const classesView = classesWrapper.vm as unknown as {
      classFilters: { status: string }
      classForm: { name: string }
      classFormRef: { validate: () => Promise<boolean> }
      saveClass: () => Promise<void>
      studentFilters: { status: string }
      studentForm: { student_no: string; name: string; class_id: number }
      studentFormRef: { validate: () => Promise<boolean> }
      saveStudent: () => Promise<void>
    }

    classesView.classFormRef = { validate: () => Promise.resolve(true) }
    classesView.classFilters.status = 'inactive'
    classesView.classForm.name = '二年级一班'
    await classesView.saveClass()

    classesView.studentFormRef = { validate: () => Promise.resolve(true) }
    classesView.studentFilters.status = 'archived'
    Object.assign(classesView.studentForm, { student_no: 'S002', name: '李四', class_id: 1 })
    await classesView.saveStudent()

    expect(classesView.classFilters.status).toBe('active')
    expect(classesView.studentFilters.status).toBe('active')

    const coursesWrapper = mount(CoursesScheduleView, {
      global: testGlobal(),
    })
    const coursesView = coursesWrapper.vm as unknown as {
      courseFilters: { status: string }
      courseForm: { course_name: string }
      courseFormRef: { validate: () => Promise<boolean> }
      saveCourse: () => Promise<void>
      scheduleFilters: { status: string }
      scheduleForm: { class_id: number; course_id: number; weekday: number; period_no: number }
      scheduleFormRef: { validate: () => Promise<boolean> }
      saveSchedule: () => Promise<void>
    }

    coursesView.courseFormRef = { validate: () => Promise.resolve(true) }
    coursesView.courseFilters.status = 'inactive'
    coursesView.courseForm.course_name = '化学'
    await coursesView.saveCourse()

    coursesView.scheduleFormRef = { validate: () => Promise.resolve(true) }
    coursesView.scheduleFilters.status = 'archived'
    Object.assign(coursesView.scheduleForm, { class_id: 1, course_id: 1, weekday: 1, period_no: 1 })
    await coursesView.saveSchedule()

    expect(coursesView.courseFilters.status).toBe('active')
    expect(coursesView.scheduleFilters.status).toBe('active')
  })

  it('keeps course and schedule create status active-only', async () => {
    const post = vi.spyOn(http, 'post').mockImplementation((url: string) => {
      if (url === '/courses') {
        return Promise.resolve({ data: { id: 11, course_name: '物理', status: 'active', remark: null } })
      }
      if (url === '/schedules') {
        return Promise.resolve({
          data: {
            id: 22,
            class_id: 1,
            course_id: 11,
            weekday: 1,
            period_no: 2,
            start_time: null,
            end_time: null,
            location: null,
            status: 'active',
            remark: null,
          },
        })
      }
      return Promise.resolve({ data: {} })
    })
    const patch = vi.spyOn(http, 'patch').mockResolvedValue({ data: {} })
    const wrapper = mount(CoursesScheduleView, {
      global: testGlobal(),
    })
    const view = wrapper.vm as unknown as {
      courseForm: { course_name: string; status: string }
      courseFormRef: { validate: () => Promise<boolean> }
      saveCourse: () => Promise<void>
      scheduleForm: { class_id: number; course_id: number; weekday: number; period_no: number; status: string }
      scheduleFormRef: { validate: () => Promise<boolean> }
      saveSchedule: () => Promise<void>
    }

    view.courseFormRef = { validate: () => Promise.resolve(true) }
    view.courseForm.course_name = '物理'
    view.courseForm.status = 'inactive'
    await view.saveCourse()

    view.scheduleFormRef = { validate: () => Promise.resolve(true) }
    Object.assign(view.scheduleForm, {
      class_id: 1,
      course_id: 11,
      weekday: 1,
      period_no: 2,
      status: 'archived',
    })
    await view.saveSchedule()

    expect(post).toHaveBeenCalledWith('/courses', expect.not.objectContaining({ status: expect.anything() }))
    expect(post).toHaveBeenCalledWith('/schedules', expect.not.objectContaining({ status: expect.anything() }))
    expect(patch).not.toHaveBeenCalled()
  })
})
