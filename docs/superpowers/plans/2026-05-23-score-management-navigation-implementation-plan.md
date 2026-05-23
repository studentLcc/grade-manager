# Score Management Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an independent `成绩管理` navigation entry and score-work entry page while reorganizing the existing class/student page into `班级管理` and `学生管理` tabs.

**Architecture:** This is a frontend-only change. `ClassesStudentsView` keeps its current state, API calls, dialogs, import handling, and save behavior, but moves the existing class and student surfaces into Element Plus tabs. `ScoreManagementView` is a new exam-list-based entry point that reuses `listExams(params)` and routes score actions into the existing exam score, import, statistics, and detail workflows.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, Element Plus, Vitest, Vue Test Utils, ESLint, Vite.

---

## File Structure

- Modify: `frontend/src/views/ClassesStudentsView.vue`
  - Responsibility: render the existing class and student management workflows in separate in-page tabs without changing their data behavior.
- Create: `frontend/src/views/ScoreManagementView.vue`
  - Responsibility: render a score-focused exam list with filters, pagination, and actions into existing score/statistics/detail routes.
- Modify: `frontend/src/router/index.ts`
  - Responsibility: register `/score-management`.
- Modify: `frontend/src/layouts/AppLayout.vue`
  - Responsibility: add sidebar item order and active-path rules for score work routes.
- Modify: `frontend/tests/base-management.spec.ts`
  - Responsibility: verify the class/student tab split and existing controls.
- Create: `frontend/tests/score-management.spec.ts`
  - Responsibility: verify the new score management page, list API usage, filter page reset, and row action routing.
- Create: `frontend/tests/navigation.spec.ts`
  - Responsibility: verify route registration, sidebar ordering, and active navigation mapping.

---

### Task 1: Add Failing Tests For Class/Student Tabs

**Files:**
- Modify: `frontend/tests/base-management.spec.ts`

- [ ] **Step 1: Replace the old one-page class/student render test**

Replace the existing test named `renders class and student controls on one page` with these three tests:

```ts
  it('renders class and student management tabs', () => {
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })

    expect(wrapper.text()).toContain('班级与学生')
    expect(wrapper.text()).toContain('班级管理')
    expect(wrapper.text()).toContain('学生管理')
  })

  it('keeps class controls in the class management tab content', () => {
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })

    expect(wrapper.text()).toContain('班级列表')
    expect(wrapper.text()).toContain('新增班级')
    expect(wrapper.text()).toContain('班级')
    expect(wrapper.text()).toContain('年级')
    expect(wrapper.text()).toContain('学年')
  })

  it('keeps student controls and import in the student management tab content', () => {
    const wrapper = mount(ClassesStudentsView, {
      global: testGlobal(),
    })

    expect(wrapper.text()).toContain('学生列表')
    expect(wrapper.text()).toContain('导入学生')
    expect(wrapper.text()).toContain('新增学生')
    expect(wrapper.text()).toContain('学号')
    expect(wrapper.text()).toContain('姓名')
  })
```

- [ ] **Step 2: Run the focused test and verify it fails**

From `frontend/`, run:

```bash
npm run test -- tests/base-management.spec.ts
```

Expected: FAIL. The first new test fails because `ClassesStudentsView` does not yet render `班级管理` and `学生管理`.

- [ ] **Step 3: Commit the failing test**

```bash
git add frontend/tests/base-management.spec.ts
git commit -m "test: cover class student tab split"
```

---

### Task 2: Split ClassesStudentsView Into Tabs

**Files:**
- Modify: `frontend/src/views/ClassesStudentsView.vue`
- Test: `frontend/tests/base-management.spec.ts`

- [ ] **Step 1: Remove the duplicate page-header actions**

In `frontend/src/views/ClassesStudentsView.vue`, replace the existing `.gm-page-header` block with:

```vue
    <div class="gm-page-header">
      <div>
        <h1>班级与学生</h1>
        <p>维护基础班级、学生档案，并导入批量学生名单。</p>
      </div>
    </div>
```

- [ ] **Step 2: Replace the two-column management grid with Element Plus tabs**

In `frontend/src/views/ClassesStudentsView.vue`, replace the full `<div class="gm-management-grid">...</div>` block with:

```vue
    <section class="gm-page-card">
      <div class="gm-tab-label-row" aria-hidden="true">
        <span>班级管理</span>
        <span>学生管理</span>
      </div>
      <el-tabs>
        <el-tab-pane label="班级管理" name="classes">
          <div class="gm-section-title">
            <h2>班级列表</h2>
            <button class="gm-action-button" type="button" @click="openCreateClassDialog">新增班级</button>
          </div>
          <div class="gm-filter-row">
            <el-input v-model="classFilters.keyword" placeholder="搜索班级名称" clearable />
            <el-select v-model="classFilters.status" placeholder="状态">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <el-table v-loading="classLoading" :data="classRows" empty-text="暂无班级">
            <el-table-column prop="name" label="班级" />
            <el-table-column prop="grade" label="年级" width="90" />
            <el-table-column prop="academic_year" label="学年" width="120" />
            <el-table-column prop="status_display" label="状态" width="90" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button text type="primary" @click="openEditClassDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="gm-pagination">
            <el-pagination
              v-model:current-page="classFilters.page"
              v-model:page-size="classFilters.page_size"
              layout="prev, pager, next, sizes"
              :total="classTotal"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="学生管理" name="students">
          <div class="gm-section-title">
            <h2>学生列表</h2>
            <div class="gm-toolbar">
              <el-upload
                v-model:file-list="uploadFiles"
                :disabled="importDisabled"
                :http-request="uploadStudents"
                :show-file-list="false"
                name="file"
              >
                <button class="gm-action-button" :disabled="importDisabled" type="button">导入学生</button>
              </el-upload>
              <button class="gm-action-button is-primary" type="button" @click="openCreateStudentDialog">新增学生</button>
            </div>
          </div>

          <div class="gm-filter-row gm-filter-row-wide">
            <el-input v-model="studentFilters.keyword" placeholder="搜索学号或姓名" clearable />
            <el-select v-model="studentFilters.status" placeholder="状态">
              <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
            <el-select v-model="studentFilters.class_id" placeholder="所属班级" clearable>
              <el-option v-for="item in classOptions" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </div>

          <ImportResultPanel :result="importResult" />

          <el-table v-loading="studentLoading" :data="studentRows" empty-text="暂无学生">
            <el-table-column prop="student_no" label="学号" width="120" />
            <el-table-column prop="name" label="姓名" width="110" />
            <el-table-column prop="class_display" label="班级" />
            <el-table-column prop="status_display" label="状态" width="90" />
            <el-table-column prop="remark" label="备注" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button text type="primary" @click="openEditStudentDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="gm-pagination">
            <el-pagination
              v-model:current-page="studentFilters.page"
              v-model:page-size="studentFilters.page_size"
              layout="prev, pager, next, sizes"
              :total="studentTotal"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </section>
```

- [ ] **Step 3: Run the focused test and verify it passes**

From `frontend/`, run:

```bash
npm run test -- tests/base-management.spec.ts
```

Expected: PASS. Existing class/student save, filter, import, status, and pagination tests still pass.

- [ ] **Step 4: Commit the tab implementation**

```bash
git add frontend/src/views/ClassesStudentsView.vue
git commit -m "feat: split class student management into tabs"
```

---

### Task 3: Add Failing Tests For ScoreManagementView

**Files:**
- Create: `frontend/tests/score-management.spec.ts`

- [ ] **Step 1: Create the score management test file**

Create `frontend/tests/score-management.spec.ts` with:

```ts
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
```

- [ ] **Step 2: Run the focused test and verify it fails**

From `frontend/`, run:

```bash
npm run test -- tests/score-management.spec.ts
```

Expected: FAIL with an import resolution error for `../src/views/ScoreManagementView.vue`.

- [ ] **Step 3: Commit the failing test**

```bash
git add frontend/tests/score-management.spec.ts
git commit -m "test: cover score management page"
```

---

### Task 4: Implement ScoreManagementView

**Files:**
- Create: `frontend/src/views/ScoreManagementView.vue`
- Test: `frontend/tests/score-management.spec.ts`

- [ ] **Step 1: Create the new score management view**

Create `frontend/src/views/ScoreManagementView.vue` with:

```vue
<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listExams, type ExamRecord } from '../api/exams'

const router = useRouter()
const loading = ref(false)
const exams = ref<ExamRecord[]>([])
const total = ref(0)
let requestSeq = 0
let resettingPage = false

const filters = reactive({
  keyword: '',
  exam_type: '',
  term: '',
  status: 'active',
  page: 1,
  page_size: 20,
})

const statusOptions = [
  { label: '启用', value: 'active' },
  { label: '停用', value: 'inactive' },
  { label: '归档', value: 'archived' },
]

const typeOptions = [
  { label: '校级考试', value: 'school' },
  { label: '单元测验', value: 'quiz' },
  { label: '期中考试', value: 'midterm' },
  { label: '期末考试', value: 'final' },
]
const statusLabelMap = new Map(statusOptions.map((item) => [item.value, item.label]))
const typeLabelMap = new Map(typeOptions.map((item) => [item.value, item.label]))

function compactParams(params: Record<string, unknown>) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== '' && value !== undefined && value !== null))
}

async function loadExams() {
  const requestId = ++requestSeq
  loading.value = true
  try {
    const { data } = await listExams(compactParams(filters))
    if (requestId !== requestSeq) return
    exams.value = data.items
    total.value = data.total
  } catch {
    // Global http interceptor shows the user-facing error.
  } finally {
    if (requestId === requestSeq) loading.value = false
  }
}

function classNames(exam: ExamRecord) {
  return exam.classes.map((item) => item.name).join('、') || '-'
}

function subjectNames(exam: ExamRecord) {
  return exam.subjects.map((item) => item.course_name || '未命名科目').join('、') || '-'
}

function examTypeLabel(examType: string | null) {
  return examType ? typeLabelMap.get(examType) || '其他考试' : '未设置'
}

function statusLabel(status: string) {
  return statusLabelMap.get(status) || '未知状态'
}

watch(
  () => [filters.keyword, filters.exam_type, filters.term, filters.status],
  () => {
    if (filters.page !== 1) {
      resettingPage = true
      filters.page = 1
      return
    }
    loadExams()
  },
)

watch(
  () => [filters.page, filters.page_size],
  () => {
    if (resettingPage) resettingPage = false
    loadExams()
  },
)

onMounted(loadExams)
</script>

<template>
  <section class="gm-management-page">
    <div class="gm-page-header">
      <div>
        <h1>成绩管理</h1>
        <p>集中处理成绩录入、成绩导入和成绩复核，快速进入考试统计。</p>
      </div>
    </div>

    <section class="gm-page-card">
      <div class="gm-filter-row gm-filter-row-wide">
        <el-input v-model="filters.keyword" placeholder="搜索考试名称" clearable />
        <el-select v-model="filters.exam_type" placeholder="考试类型" clearable>
          <el-option v-for="item in typeOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input v-model="filters.term" placeholder="学期" clearable />
        <el-select v-model="filters.status" placeholder="状态">
          <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="exams" empty-text="暂无考试">
        <el-table-column prop="name" label="考试名称" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            {{ examTypeLabel(row.exam_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="term" label="学期" width="140" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            {{ statusLabel(row.status) }}
          </template>
        </el-table-column>
        <el-table-column label="参与班级" min-width="160">
          <template #default="{ row }">
            {{ classNames(row) }}
          </template>
        </el-table-column>
        <el-table-column label="科目" min-width="160">
          <template #default="{ row }">
            {{ subjectNames(row) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button text type="primary" @click="router.push(`/exam-center/${row.id}/scores`)">成绩录入</el-button>
            <el-button text @click="router.push(`/exam-center/${row.id}/scores?import=1`)">导入成绩</el-button>
            <el-button text @click="router.push(`/exam-center/${row.id}/statistics`)">查看统计</el-button>
            <el-button text @click="router.push(`/exam-center/${row.id}`)">考试详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="gm-pagination">
        <el-pagination v-model:current-page="filters.page" v-model:page-size="filters.page_size" layout="prev, pager, next, sizes" :total="total" />
      </div>
    </section>
  </section>
</template>
```

- [ ] **Step 2: Run the focused test and verify it passes**

From `frontend/`, run:

```bash
npm run test -- tests/score-management.spec.ts
```

Expected: PASS. The page renders exam list data, has no `创建考试` control, and routes all four row actions correctly.

- [ ] **Step 3: Commit the view implementation**

```bash
git add frontend/src/views/ScoreManagementView.vue
git commit -m "feat: add score management view"
```

---

### Task 5: Add Failing Tests For Route And Sidebar Navigation

**Files:**
- Create: `frontend/tests/navigation.spec.ts`

- [ ] **Step 1: Create the navigation test file**

Create `frontend/tests/navigation.spec.ts` with:

```ts
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
```

- [ ] **Step 2: Run the focused test and verify it fails**

From `frontend/`, run:

```bash
npm run test -- tests/navigation.spec.ts
```

Expected: FAIL. `/score-management` is not registered, `成绩管理` is missing from the sidebar, and score work routes still highlight `考试中心`.

- [ ] **Step 3: Commit the failing navigation test**

```bash
git add frontend/tests/navigation.spec.ts
git commit -m "test: cover score management navigation"
```

---

### Task 6: Register Route And Sidebar Item

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/layouts/AppLayout.vue`
- Test: `frontend/tests/navigation.spec.ts`

- [ ] **Step 1: Register the new route**

In `frontend/src/router/index.ts`, add this import:

```ts
import ScoreManagementView from '../views/ScoreManagementView.vue'
```

Then add the child route immediately after `exam-center`:

```ts
        { path: 'exam-center', component: ExamCenterView },
        { path: 'score-management', component: ScoreManagementView },
        { path: 'exam-center/:id', component: ExamDetailView },
```

- [ ] **Step 2: Add the sidebar item and score active-path rules**

In `frontend/src/layouts/AppLayout.vue`, add `Notebook` to the icon import list:

```ts
  Notebook,
```

Replace the current `activePath` computed block with:

```ts
const scoreWorkRoutePattern = /^\/exam-center\/[^/]+\/(scores|statistics)$/

const activePath = computed(() => {
  if (route.path.startsWith('/score-management')) return '/score-management'
  if (scoreWorkRoutePattern.test(route.path)) return '/score-management'
  if (route.path.startsWith('/exam-center')) return '/exam-center'
  if (route.path.startsWith('/imports')) return '/imports'
  return route.path
})
```

Replace the `navItems` array with:

```ts
const navItems = [
  { path: '/dashboard', label: '工作台', icon: House },
  { path: '/classes-students', label: '班级与学生', icon: User },
  { path: '/courses-schedule', label: '课程与课表', icon: Calendar },
  { path: '/exam-center', label: '考试中心', icon: Files },
  { path: '/score-management', label: '成绩管理', icon: Notebook },
  { path: '/statistics', label: '统计分析', icon: DataAnalysis },
  { path: '/imports', label: '导入记录', icon: UploadFilled },
  { path: '/account', label: '账号设置', icon: Setting },
]
```

- [ ] **Step 3: Run the navigation test and verify it passes**

From `frontend/`, run:

```bash
npm run test -- tests/navigation.spec.ts
```

Expected: PASS. The sidebar order matches the design, `/score-management` highlights `成绩管理`, `/exam-center/:id/scores` highlights `成绩管理`, `/exam-center/:id/statistics` highlights `成绩管理`, `/exam-center/:id` highlights `考试中心`, and import pages still highlight `导入记录`.

- [ ] **Step 4: Commit the routing and navigation implementation**

```bash
git add frontend/src/router/index.ts frontend/src/layouts/AppLayout.vue
git commit -m "feat: add score management navigation"
```

---

### Task 7: Final Frontend Verification

**Files:**
- Verify: `frontend/tests/base-management.spec.ts`
- Verify: `frontend/tests/score-management.spec.ts`
- Verify: `frontend/tests/navigation.spec.ts`
- Verify: `frontend/src/views/ClassesStudentsView.vue`
- Verify: `frontend/src/views/ScoreManagementView.vue`
- Verify: `frontend/src/layouts/AppLayout.vue`
- Verify: `frontend/src/router/index.ts`

- [ ] **Step 1: Run all frontend unit tests**

From `frontend/`, run:

```bash
npm run test
```

Expected: PASS.

- [ ] **Step 2: Run frontend lint**

From `frontend/`, run:

```bash
npm run lint
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

From `frontend/`, run:

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 4: Commit any verification fixes**

If verification required small fixes, commit only the files changed for those fixes:

```bash
git add frontend
git commit -m "fix: stabilize score management navigation"
```

Expected: no commit is needed when tests, lint, and build pass without additional edits.

---

## Coverage Check

- Sidebar includes `成绩管理` in the required order: Task 5 and Task 6.
- `/score-management` route exists: Task 5 and Task 6.
- `/exam-center/:id/scores` and `/exam-center/:id/statistics` highlight `成绩管理`: Task 5 and Task 6.
- `/exam-center` and `/exam-center/:id` continue to highlight `考试中心`: Task 5 and Task 6.
- Import pages continue to highlight `导入记录`: Task 5 and Task 6.
- `ClassesStudentsView` renders `班级管理` and `学生管理` tabs: Task 1 and Task 2.
- Class filters, table, pagination, create, edit, status behavior remain in place: Task 1, Task 2, and existing `base-management.spec.ts` tests.
- Student filters, table, pagination, create, edit, import, import result behavior remain in place: Task 1, Task 2, and existing `base-management.spec.ts` tests.
- `ScoreManagementView` uses `listExams(params)`: Task 3 and Task 4.
- `ScoreManagementView` has no `创建考试` control: Task 3 and Task 4.
- Score row actions route to score entry, score import, statistics, and exam detail: Task 3 and Task 4.
- Backend changes are excluded because the design says existing APIs are sufficient.
