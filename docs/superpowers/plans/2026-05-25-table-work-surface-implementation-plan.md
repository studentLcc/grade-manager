# Table Work Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all paginated table pages use a unified table work surface with compact controls, contained table scrolling, and attached pagination.

**Architecture:** This is a frontend-only layout change. Vue view templates wrap existing filters, `el-table`, and pagination controls in a shared `gm-table-surface` structure, while global CSS defines the surface, toolbar, viewport, and pagination behavior. Existing API calls, filters, pagination models, columns, routes, and row actions stay unchanged.

**Tech Stack:** Vue 3, TypeScript, Element Plus, Vitest, Vue Test Utils, ESLint, Vite, CSS.

---

## File Structure

- Modify: `frontend/tests/table-layout.spec.ts`
  - Responsibility: enforce table work surface structure and global CSS conventions.
- Modify: `frontend/src/styles/app.css`
  - Responsibility: define shared table surface, toolbar, viewport, pagination, and responsive behavior.
- Modify: `frontend/src/views/ClassesStudentsView.vue`
  - Responsibility: apply the surface to class and student management tables.
- Modify: `frontend/src/views/CoursesScheduleView.vue`
  - Responsibility: apply the surface to course and weekly schedule tables.
- Modify: `frontend/src/views/ExamStatisticsView.vue`
  - Responsibility: apply the surface to ranking, segment, and exception tables.
- Modify: `frontend/src/views/ExamCenterView.vue`
  - Responsibility: apply the surface to the exam list.
- Modify: `frontend/src/views/StatisticsView.vue`
  - Responsibility: apply the surface to the statistics exam list.
- Modify: `frontend/src/views/ScoreManagementView.vue`
  - Responsibility: apply the surface to the score records table.
- Modify: `frontend/src/views/ImportRecordsView.vue`
  - Responsibility: apply the surface to the import records table.
- Modify: `frontend/src/views/ImportDetailView.vue`
  - Responsibility: apply the surface to the row error table and pagination.

---

### Task 1: Add Structural Tests

**Files:**
- Modify: `frontend/tests/table-layout.spec.ts`

- [ ] **Step 1: Add a table-surface convention test**

Add a test that scans paginated table views for the shared classes:

```ts
  it('wraps paginated tables in a consistent table work surface', () => {
    const requiredFiles = [
      'src/views/ClassesStudentsView.vue',
      'src/views/CoursesScheduleView.vue',
      'src/views/ExamStatisticsView.vue',
      'src/views/ExamCenterView.vue',
      'src/views/StatisticsView.vue',
      'src/views/ScoreManagementView.vue',
      'src/views/ImportRecordsView.vue',
      'src/views/ImportDetailView.vue',
    ]

    for (const file of requiredFiles) {
      const source = readProjectFile(file)
      expect(source, file).toContain('gm-table-surface')
      expect(source, file).toContain('gm-table-viewport')
      expect(source, file).toContain('gm-pagination')
    }
  })
```

- [ ] **Step 2: Extend the CSS convention test**

Add expectations for the new classes:

```ts
    expect(css).toContain('.gm-table-surface')
    expect(css).toContain('.gm-table-toolbar')
    expect(css).toContain('.gm-table-viewport')
    expect(css).toMatch(/\.gm-table-viewport\s*{[^}]*overflow:\s*auto/s)
    expect(css).toMatch(/\.gm-table-surface\s+\.gm-pagination\s*{[^}]*border-top:/s)
```

- [ ] **Step 3: Run the focused test and confirm failure**

Run:

```bash
cd frontend
npm run test -- table-layout.spec.ts
```

Expected before implementation: failure because `gm-table-surface` and CSS rules are missing from several files.

### Task 2: Add Shared Table Surface CSS

**Files:**
- Modify: `frontend/src/styles/app.css`

- [ ] **Step 1: Add table surface rules near existing table CSS**

Add:

```css
.gm-table-surface {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  min-width: 0;
  min-height: 360px;
  max-height: min(680px, calc(100vh - 190px));
  overflow: hidden;
  border: 1px solid #dbe7ef;
  border-radius: var(--gm-radius);
  background: #fbfdff;
}

.gm-table-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
  border-bottom: 1px solid #e4edf4;
  padding: 10px;
}

.gm-table-toolbar > .gm-filter-row,
.gm-table-toolbar > .gm-toolbar {
  margin-bottom: 0;
}

.gm-table-viewport {
  min-width: 0;
  min-height: 220px;
  overflow: auto;
  background: #fff;
}

.gm-table-viewport .gm-data-table {
  height: 100%;
}

.gm-table-surface .gm-pagination {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid #e4edf4;
  margin-top: 0;
  padding: 8px 10px;
  background: #fbfdff;
}
```

- [ ] **Step 2: Add responsive rules**

Add:

```css
@media (max-width: 720px) {
  .gm-table-surface {
    max-height: none;
  }

  .gm-table-toolbar {
    align-items: stretch;
  }

  .gm-table-toolbar > .gm-filter-row,
  .gm-table-toolbar > .gm-toolbar {
    width: 100%;
  }
}
```

- [ ] **Step 3: Run the focused CSS test**

Run:

```bash
cd frontend
npm run test -- table-layout.spec.ts
```

Expected: still fails until templates are wrapped.

### Task 3: Wrap Management Tables

**Files:**
- Modify: `frontend/src/views/ClassesStudentsView.vue`
- Modify: `frontend/src/views/CoursesScheduleView.vue`

- [ ] **Step 1: Wrap class and student table blocks**

For each tab, keep `gm-section-title` outside and wrap the existing filter/action controls, table, and pagination:

```html
<div class="gm-table-surface">
  <div class="gm-table-toolbar">
    <div class="gm-filter-row">...</div>
    <div class="gm-toolbar">...</div>
  </div>
  <div class="gm-table-viewport">
    <el-table ...>...</el-table>
  </div>
  <div class="gm-pagination">...</div>
</div>
```

For class management, move `新增班级` from the section title into the toolbar. For student management, move import and create actions into the toolbar next to filters.

- [ ] **Step 2: Wrap course and schedule table blocks**

Use the same structure for course management and weekly schedule. Move status/class filters and add buttons into `gm-table-toolbar`.

- [ ] **Step 3: Run base management tests**

Run:

```bash
cd frontend
npm run test -- base-management.spec.ts table-layout.spec.ts
```

Expected: tests pass after wrappers are correct.

### Task 4: Wrap Exam, Statistics, Score, And Import Tables

**Files:**
- Modify: `frontend/src/views/ExamCenterView.vue`
- Modify: `frontend/src/views/StatisticsView.vue`
- Modify: `frontend/src/views/ScoreManagementView.vue`
- Modify: `frontend/src/views/ImportRecordsView.vue`
- Modify: `frontend/src/views/ImportDetailView.vue`
- Modify: `frontend/src/views/ExamStatisticsView.vue`

- [ ] **Step 1: Wrap list pages**

For each list page, wrap the existing filter row, table, and pagination in `gm-table-surface`. Keep page headers unchanged.

- [ ] **Step 2: Wrap statistics detail tables**

For ranking and segment sections, keep the section title outside and place filters, table, and optional pagination area in a table surface. For exception rows, wrap the exception tabs as toolbar content and the exception table as viewport content.

- [ ] **Step 3: Run focused tests**

Run:

```bash
cd frontend
npm run test -- table-layout.spec.ts score-management.spec.ts exam-workflow.spec.ts import-records.spec.ts
```

Expected: tests pass.

### Task 5: Full Verification

**Files:**
- No code changes expected.

- [ ] **Step 1: Run the complete frontend suite**

Run:

```bash
cd frontend
npm run test
npm run lint
npm run build
```

Expected: tests and lint pass; build may keep existing chunk-size or Rollup annotation warnings only.

- [ ] **Step 2: Browser-check key pages**

Use the in-app browser to inspect:

```text
http://localhost:5173/classes-students
http://localhost:5173/courses-schedule
http://localhost:5173/exam-center
http://localhost:5173/statistics
```

For each page, verify:

- Filters, table, and pagination sit in one surface.
- Table body scrolls inside the surface when content is long.
- Operation columns remain fixed on the right.
- Pagination remains close to the table.
- No page-level horizontal overflow appears.
