# Score Management Navigation Design

## Context

This design updates the existing Grade Manager frontend organization. It builds on:

- `docs/superpowers/specs/2026-05-20-grade-manager-design.md`
- `docs/superpowers/specs/2026-05-21-grade-manager-frontend-workflow-design.md`

The backend already provides the score-sheet, score save, score template, score import, exam list, exam detail, and statistics APIs needed for the requested workflow. This change is therefore frontend-focused unless implementation reveals a contract mismatch.

## Decisions

The approved approach is:

1. Keep one sidebar entry for class and student setup.
2. Split the current combined class/student page into two in-page tabs:
   - `班级管理`
   - `学生管理`
3. Add an independent sidebar entry named `成绩管理`.
4. Reuse existing exam and score APIs. Do not add a separate score data model or new score CRUD backend in this change.

## Navigation

The main sidebar will include a new `成绩管理` item near `考试中心`.

Expected sidebar order:

1. 工作台
2. 班级与学生
3. 课程与课表
4. 考试中心
5. 成绩管理
6. 统计分析
7. 导入记录
8. 账号设置

The new route will be `/score-management`.

Active navigation rules:

- `/score-management` highlights `成绩管理`.
- `/exam-center/:id/scores` highlights `成绩管理`, because it is the score work surface.
- `/exam-center/:id/statistics` may also highlight `成绩管理` when reached as a score follow-up.
- `/exam-center` and `/exam-center/:id` continue to highlight `考试中心`.
- Existing import record pages continue to highlight `导入记录`.

## Class And Student Page

The existing `ClassesStudentsView` remains the route target for `/classes-students`, but its content is reorganized into tabs.

### Class Management Tab

The `班级管理` tab contains:

- page-level class filters: keyword and status
- class table
- class pagination
- create class action
- edit class action and dialog

Class behavior remains unchanged:

- new classes are created as active
- editing can change status
- class list filters reset pagination when changed
- active class options are still fetched independently for selectors

### Student Management Tab

The `学生管理` tab contains:

- student filters: keyword, status, class
- student table
- student pagination
- create student action
- edit student action and dialog
- student import action
- import result panel

Student behavior remains unchanged:

- importing students requires a selected target class
- new students are created as active
- editing can change status
- student list filters reset pagination when changed
- student create/edit class options come from active classes with the existing fallback for edited inactive classes

## Score Management Page

The new `ScoreManagementView` is a score-focused work entry point. It uses the existing exam list API and does not create or configure exams.

It contains:

- page header titled `成绩管理`
- description focused on score entry, score import, and score review
- filters:
  - exam keyword
  - exam type
  - term
  - status
- exam table columns:
  - exam name
  - type
  - term
  - status
  - participating classes
  - subjects
  - actions
- pagination

Row actions:

- `成绩录入` links to `/exam-center/:id/scores`
- `导入成绩` links to `/exam-center/:id/scores?import=1`
- `查看统计` links to `/exam-center/:id/statistics`
- `考试详情` links to `/exam-center/:id`

The page should not show `创建考试`, because exam creation remains the responsibility of `考试中心`.

## Exam Center Boundary

`考试中心` continues to own:

- creating exams through the wizard
- exam list and exam detail
- participating class configuration
- subject configuration
- exam status and metadata review

`成绩管理` owns:

- finding exams for score work
- entering scores
- importing scores
- navigating to score statistics

This keeps teachers from needing to start every score workflow from the exam setup area while avoiding duplicate exam creation behavior.

## Data Flow

`ScoreManagementView` uses the same API client as `ExamCenterView`:

- `listExams(params)` for table data

The score entry and import workflows continue through existing routes and APIs:

- `getScoreSheet(examId)`
- `saveScores(examId, items)`
- `downloadScoreTemplate(examId, classId?)`
- `importScores(examId, file, overwriteExisting?)`

No backend schema, migration, or API contract change is expected.

## Error Handling

The new page follows existing frontend conventions:

- API failures are surfaced by the global HTTP interceptor.
- Local load state is cleared only for the latest request.
- Filter changes reset the page to `1`.
- Empty exam lists use existing Element Plus empty table behavior.

The class/student tab split preserves existing save/import error handling:

- dialogs stay open when save requests fail
- import result panels show backend result fields
- import remains disabled until a class is selected

## Testing

Frontend tests should cover:

- `ClassesStudentsView` renders `班级管理` and `学生管理` tabs.
- Class controls are present in the class tab.
- Student import and student controls are present in the student tab.
- Existing class/student save, filter, import, status, and pagination behaviors still pass.
- `ScoreManagementView` renders the independent score entry page from exam list data.
- `ScoreManagementView` does not render exam creation controls.
- Score management row actions route to score entry, score import, statistics, and exam detail.
- The sidebar includes `成绩管理` and active path mapping highlights score work routes correctly.

Verification should include:

- frontend unit tests
- frontend lint
- frontend build

Backend tests are not required for this UI-only change unless implementation changes backend contracts.
