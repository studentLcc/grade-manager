# Grade Manager Design

## Context

Build a grade management system for teachers. The project is a new front-end/back-end separated application with:

- Backend: Python, FastAPI, MySQL, `uv` for Python dependency and environment management.
- Frontend: Vue 3, Vite, Element Plus.
- Users: multiple teachers. Each teacher manages only their own classes, students, courses, exams, scores, imports, and statistics.

The first version focuses on teacher workflows: class and student management, course management, exam setup, score entry, Excel import, and score statistics.

## Scope

In scope for the first version:

- Teacher registration and login.
- Class management.
- Student management with manual editing and Excel import.
- Course management.
- **Schedule management** — minimal weekly schedule CRUD for dashboard display.
- Exam management, including single-subject quizzes and multi-subject school exams.
- Exams associated with one or more classes.
- Exam subjects with per-subject full score, pass score, excellent score, exam date, and remarks.
- Score entry through an editable table.
- Score import through Excel.
- Import batch tracking and row-level import errors.
- Statistics by exam, class, subject, and student history.
- **Dashboard APIs** — summary metrics, recent exams, score overview, class average trend.
- Soft deletion through inactive/archived status.

Out of scope for the first version:

- School-wide admin role.
- Student login.
- Parent login.
- SSO integration.
- Full student class history table, unless later requirements demand detailed enrollment period tracking outside exam snapshots.
- Advanced schedule features: semester version switching, conflict detection, class adjustments/cancellations/makeups, hard linkage with exams/scores.

## Architecture

The system uses standard front-end/back-end separation.

Backend:

- FastAPI application with `/api/v1` route prefix.
- SQLAlchemy 2.x for ORM.
- Alembic for migrations.
- MySQL as the primary database.
- `uv` with `pyproject.toml` and `uv.lock` for dependency management.
- Pydantic schemas for request and response validation.
- JWT authentication.
- Services contain business logic; routers stay thin.

Frontend:

- Vue 3 with Vite.
- Element Plus for table, form, dialog, upload, pagination, menu, and message components.
- Pinia for auth/session and shared state.
- Vue Router for protected routes.
- Axios with an interceptor for JWT and common error handling.

Recommended backend module boundaries:

- `auth`
- `teachers`
- `classes`
- `students`
- `courses`
- `schedules`
- `exams`
- `scores`
- `imports`
- `statistics`
- `dashboard`

Each business module should keep routes, schemas, models, and services separate enough that rules can be tested without going through the HTTP layer.

## Authentication

Teachers register and log in with username/password. Passwords are stored as hashes.

JWT rules:

- Tokens include the teacher id and an expiration timestamp.
- Default expiration is 30 days.
- Expiration is configurable through environment variables, for example 7, 30, or 90 days.
- Do not implement non-expiring tokens.
- First version does not need refresh tokens.
- When the token expires, the frontend clears local session state and redirects to the login page.

All business APIs require JWT. Every business query is scoped to the current teacher.

## Data Model

### `teachers`

Stores teacher accounts.

Important fields:

- `id`
- `username`
- `password_hash`
- `display_name`
- `email`
- `phone`
- `status`
- `created_at`
- `updated_at`

### `classes`

Stores teacher-owned classes.

Important fields:

- `id`
- `teacher_id`
- `name`
- `grade`
- `academic_year`
- `status`
- `remark`
- `created_at`
- `updated_at`

Best-practice rule: do not overwrite a historical class by renaming it across school years. When a class advances from one grade/year to another, create a new class record and move current students to it. Historical exams remain associated with the old class record.

### `students`

Stores current student information.

Important fields:

- `id`
- `teacher_id`
- `class_id`
- `student_no`
- `name`
- `gender`
- `status`
- `remark`
- `created_at`
- `updated_at`

Constraints:

- Unique: `teacher_id + student_no`.

`students.class_id` means the student's current class. It is not enough for historical exam statistics after a student transfers. Historical exam class membership is captured through `exam_students`.

Ownership rule:

- `students.teacher_id` must match the `teacher_id` of the referenced current class.

### `courses`

Stores teacher-owned subjects.

Important fields:

- `id`
- `teacher_id`
- `course_name`
- `status`
- `remark`
- `created_at`
- `updated_at`

Constraints:

- Unique: `teacher_id + course_name`.

### `schedules`

Stores a teacher's minimal weekly schedule for dashboard display.

Important fields:

- `id`
- `teacher_id`
- `class_id`
- `course_id`
- `weekday`
- `period_no`
- `start_time`
- `end_time`
- `location`
- `status`
- `remark`
- `created_at`
- `updated_at`

Constraints:

- Unique active schedule slot: `teacher_id + class_id + weekday + period_no`.

Rules:

- `weekday` uses 1 through 7, where 1 means Monday and 7 means Sunday.
- `period_no` is a positive integer.
- `start_time` and `end_time` are optional in the first version.
- When both times are present, `start_time` must be earlier than `end_time`.
- A schedule row must reference a class and course owned by the current teacher.
- `schedules.teacher_id` must match both the referenced class owner and the referenced course owner.
- Schedule records are not linked to exams or score statistics in the first version.
- The dashboard's "today" schedule uses the configured application timezone, defaulting to `Asia/Shanghai`.

### `exams`

Stores exam-level information.

Important fields:

- `id`
- `teacher_id`
- `name`
- `exam_type`
- `term`
- `status`
- `remark`
- `created_at`
- `updated_at`

Exam-level data contains the overall name, type, term, and remarks. Per-subject exam date and score thresholds belong to `exam_subjects`.

### `exam_classes`

Associates exams with participating classes.

Important fields:

- `id`
- `exam_id`
- `class_id`
- `status`
- `created_at`

Constraints:

- Unique: `exam_id + class_id`.

Rules:

- An exam must have at least one class.
- A class associated with an exam must belong to the current teacher.
- One exam may include multiple classes.
- `status=active` means the class currently participates in the exam.
- `status=inactive` preserves a historical association after a post-scoring removal that is allowed by business rules.

### `exam_subjects`

Stores subjects within an exam.

Important fields:

- `id`
- `exam_id`
- `course_id`
- `full_score`
- `pass_score`
- `excellent_score`
- `exam_date`
- `status`
- `remark`
- `created_at`
- `updated_at`

Constraints:

- Unique: `exam_id + course_id`.

Rules:

- Scores use decimal thresholds, not floating point.
- Threshold order must be valid: `0 <= pass_score <= excellent_score <= full_score`.
- A subject with existing scores cannot be physically removed from the exam.
- A subject without scores can be removed.
- A subject with scores can still update full score, pass score, excellent score, exam date, remarks, or status, subject to validation.
- Updating `full_score` after scores exist is allowed only if the new full score is greater than or equal to the highest existing normal score for that subject.
- Updating pass or excellent thresholds after scores exist must preserve valid threshold order. Statistics always use the current thresholds, but updates that make existing scores impossible are rejected.
- If a subject needs to be retired after scores exist, mark it inactive.

### `exam_students`

Stores the participating students and their class snapshot for an exam.

Important fields:

- `id`
- `exam_id`
- `student_id`
- `class_id`
- `status`
- `created_at`

Constraints:

- Unique: `exam_id + student_id`.

Purpose:

- Freeze which students participate in an exam.
- Freeze each student's class for that exam. `exam_students.class_id` means the student's class when participating in this exam, not the student's current class.
- Preserve historical statistics even if the student later transfers to another class.

When an exam is created or the score sheet is first generated, the backend populates `exam_students` from the selected `exam_classes` and the current active students in those classes. After any score exists for the exam, the roster is frozen for destructive changes: later refreshes must not delete existing `exam_students` rows, must not change their `class_id`, and must not orphan or invalidate existing `scores`.

Roster refresh policy:

- Before scoring starts, the backend may rebuild `exam_students` from the current active students in active `exam_classes`.
- After scoring starts, refresh is a transactional merge.
- Existing `exam_students` rows are retained.
- Existing `scores` are retained.
- New active students from the exam classes may be appended.
- Students no longer in the current class list are kept in the snapshot and may be marked inactive/withdrawn for that exam, but they are not deleted.
- Removing a class from `exam_classes` before scoring starts may rebuild the snapshot.
- Removing a class after scoring starts is rejected if that class has any `scores` for the exam.
- Removing a class after scoring starts is allowed only when the class has snapshotted students but no scores; in that case the `exam_classes` row is marked inactive and the related `exam_students` rows are marked inactive or withdrawn instead of being deleted.

Future student transfers do not change old exam snapshots automatically.

### `scores`

Stores score details.

Important fields:

- `id`
- `exam_student_id`
- `exam_subject_id`
- `score`
- `score_status`
- `remark`
- `created_at`
- `updated_at`

Constraints:

- Unique: `exam_student_id + exam_subject_id`.

Rules:

- `score` uses `DECIMAL(6,2)`.
- `exam_student_id` references the student's row in the exam snapshot.
- Score writes must verify that `exam_student_id` belongs to the same exam as `exam_subject_id`.
- Student and class information for a score is read through `exam_student_id`; the first version does not duplicate `student_id` or `class_id` in `scores`.
- No `scores` row means not entered.
- `score_status = normal` requires a decimal score.
- `score_status in absent/deferred/cheating/exempt` normally requires `score` to be null.
- Numeric score must be greater than or equal to 0.
- Numeric score must not exceed `exam_subjects.full_score`.

Recommended status values:

- `normal`
- `absent`
- `deferred`
- `cheating`
- `exempt`

### `import_batches`

Tracks student and score imports.

Important fields:

- `id`
- `teacher_id`
- `import_type`
- `target_class_id`
- `target_exam_id`
- `target_exam_subject_id`
- `file_name`
- `status`
- `success_count`
- `failed_count`
- `error_summary`
- `created_at`
- `updated_at`

`import_type` values:

- `students`
- `scores`

Target rules:

- Student imports require `target_class_id`.
- Score imports require `target_exam_id`.
- Score imports may include `target_exam_subject_id` when importing a single subject.
- `target_class_id` may also be set for class-specific score template/import workflows.

### `import_errors`

Stores row-level import errors.

Important fields:

- `id`
- `batch_id`
- `row_number`
- `field`
- `raw_value`
- `reason`
- `raw_data`
- `created_at`

Use this table instead of putting all row errors into one large text field. `raw_data` is optional and may store the original row payload when one field value is not enough to diagnose the import failure.

## Status Rules

Default status values:

- `classes`, `students`, `courses`, `schedules`, `exams`, and `exam_subjects`: `active`, `inactive`, `archived`.
- `exam_classes`: `active`, `inactive`.
- `exam_students`: `active`, `withdrawn`, `inactive`.
- `scores.score_status`: `normal`, `absent`, `deferred`, `cheating`, `exempt`.
- `import_batches.status`: `pending`, `processing`, `success`, `partial_success`, `failed`.

List and detail behavior:

- List APIs return active records by default unless the request passes a `status` filter.
- Detail APIs may return inactive or archived records when the current teacher owns them.
- Historical exams, scores, imports, and statistics may display archived related data so old records remain understandable.
- Restoring an inactive or archived record uses `PATCH` to set `status=active` and must re-check uniqueness constraints and business rules.

## API Design

All API paths use the `/api/v1` prefix.

### Authentication

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Classes

- `GET /api/v1/classes`
- `POST /api/v1/classes`
- `PATCH /api/v1/classes/{id}`
- `DELETE /api/v1/classes/{id}`

`DELETE` means soft delete by setting status to inactive/archived.

### Students

- `GET /api/v1/students`
- `POST /api/v1/students`
- `PATCH /api/v1/students/{id}`
- `DELETE /api/v1/students/{id}`
- `POST /api/v1/students/import`

`DELETE` means soft delete by setting status to inactive/archived.

### Courses

- `GET /api/v1/courses`
- `POST /api/v1/courses`
- `PATCH /api/v1/courses/{id}`
- `DELETE /api/v1/courses/{id}`

`DELETE` means soft delete by setting status to inactive/archived. Courses with historical scores should not be physically deleted.

### Schedules

- `GET /api/v1/schedules`
- `POST /api/v1/schedules`
- `PATCH /api/v1/schedules/{id}`
- `DELETE /api/v1/schedules/{id}`

`DELETE` means soft delete by setting status to inactive/archived. Schedule APIs do not implement term switching, conflict detection, cancellations, or makeups in the first version.

### Exams

- `GET /api/v1/exams`
- `POST /api/v1/exams`
- `GET /api/v1/exams/{id}`
- `PATCH /api/v1/exams/{id}`
- `DELETE /api/v1/exams/{id}`
- `PUT /api/v1/exams/{id}/classes`
- `PUT /api/v1/exams/{id}/subjects`

`POST /api/v1/exams` should accept the exam basic information, class ids, and subject definitions in one request.

`PUT /api/v1/exams/{id}/classes` can change participating classes before scoring starts and may rebuild `exam_students`. After scoring starts, it must preserve existing exam rosters and scores. Removing a class is rejected when that class already has scores for the exam. If the class has snapshotted students but no scores after scoring starts, the API may mark `exam_classes` inactive and mark related `exam_students` inactive or withdrawn instead of deleting them. Adding a class appends active students through the transactional roster merge.

`PUT /api/v1/exams/{id}/subjects` must preserve subjects with existing scores. It may remove only subjects without scores. Subjects with existing scores can be updated or marked inactive.

`PUT /api/v1/exams/{id}/subjects` must reject invalid threshold updates, including `pass_score > excellent_score`, `excellent_score > full_score`, negative thresholds, or a new `full_score` below any existing normal score.

### Scores

- `GET /api/v1/exams/{id}/score-sheet`
- `PUT /api/v1/exams/{id}/scores`
- `GET /api/v1/exams/{id}/score-template`
- `POST /api/v1/exams/{id}/scores/import`

Rules:

- `GET /api/v1/exams/{id}/score-sheet` returns students from `exam_students`, not directly from current `students.class_id`.
- `GET /api/v1/exams/{id}/score-sheet` may create the initial roster or append missing active students, but it must not delete or rewrite existing snapshotted students after scoring starts.
- `PUT /api/v1/exams/{id}/scores` bulk-saves scores and returns item-level success/failure details.
- `GET /api/v1/exams/{id}/score-template` supports optional `class_id` for multi-class exams.
- `POST /api/v1/exams/{id}/scores/import` writes valid rows and records invalid rows in `import_errors`.
- `POST /api/v1/exams/{id}/scores/import` may later support `dry_run=true` for validation-only import.
- Score writes identify rows by `exam_student_id` and `exam_subject_id`.
- Score writes reject mismatched exams or teacher ownership. Student and class ownership are resolved through the referenced `exam_students` row.

Bulk score save response should include:

- success count
- failure count
- failed items with `exam_student_id`, `exam_subject_id`, and reason

### Imports

- `GET /api/v1/imports`
- `GET /api/v1/imports/{id}`
- `GET /api/v1/imports/{id}/errors`

### Statistics

- `GET /api/v1/statistics/exams/{id}/summary`
- `GET /api/v1/statistics/exams/{id}/rankings`
- `GET /api/v1/statistics/exams/{id}/segments`
- `GET /api/v1/statistics/students/{id}/history`
- `GET /api/v1/statistics/classes/{id}/overview`

Ranking parameters:

- `rank_type=total|subject`
- `exam_subject_id`
- `class_id`
- `included_statuses=normal`

Segment parameters:

- `type=total|subject`
- `exam_subject_id`
- `class_id`
- `step=10`
- `included_statuses=normal`

Statistics status rules:

- `included_statuses` is a comma-separated set selected from `normal`, `absent`, `deferred`, `cheating`, `exempt`, and `missing`.
- Default `included_statuses` is `normal`.
- `normal` uses the entered numeric score.
- `absent`, `deferred`, `cheating`, and `exempt` count as 0 only when explicitly included.
- `missing` means there is no `scores` row and counts as 0 only when explicitly included.
- Statuses not included are excluded from average, total, ranking, segment, pass-rate, and excellent-rate denominators.
- Abnormal status counts and missing-score counts are always returned separately for visibility, regardless of `included_statuses`.

### Dashboard

- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/today-schedule`
- `GET /api/v1/dashboard/recent-exams`
- `GET /api/v1/dashboard/score-overview`
- `GET /api/v1/dashboard/class-average-trend`

Dashboard APIs aggregate existing teacher-scoped modules. They do not introduce complex alerts, comparison analytics, or workflow task queues in the first version.

Dashboard response scope:

- Summary: class count, student count, course count, recent exam count, and pending score count.
- Today's schedule: active `schedules` for the current weekday.
- Recent exams: recently created exams or exams with recent subject dates.
- Score overview: average, highest score, lowest score, and abnormal count for the latest relevant exam.
- Class average trend: recent exam average scores grouped by class.

### List Query Conventions

List APIs should reserve common pagination and filter parameters:

- `page`
- `page_size`
- `keyword`
- `status`
- `class_id`

The exact filters may vary by resource, but `GET /api/v1/students`, `GET /api/v1/exams`, `GET /api/v1/courses`, and `GET /api/v1/imports` must support pagination from the first version.

## Error Handling

Response format:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "成绩保存失败",
  "details": [
    {
      "field": "score",
      "row": 12,
      "value": "108",
      "reason": "分数不能超过满分 100"
    }
  ]
}
```

`details` item fields:

- `field`: field or logical column name.
- `row`: Excel row number or table row number when applicable.
- `value`: invalid raw value when available.
- `reason`: human-readable failure reason.

Normal form validation and Excel row errors should use the same detail structure. Non-row errors can omit `row`.

HTTP status and business code mapping:

- `401 UNAUTHORIZED`: missing, expired, or invalid token.
- `403 FORBIDDEN`: authenticated teacher is not allowed to access the resource.
- `404 NOT_FOUND`: resource does not exist or is not visible to the current teacher.
- `409 DUPLICATE_RESOURCE`: uniqueness conflict.
- `422 VALIDATION_ERROR`: field validation failure.
- `400 BUSINESS_RULE_VIOLATION`: valid request shape, but business rule rejects the action.
- `500 INTERNAL_ERROR`: unexpected server error.

## Import Behavior

Student import:

- Teacher selects target class.
- The import batch stores `target_class_id`.
- Import validates student number, name, duplicate student number, class ownership, and required fields.
- Existing `student_no` values are failed rows by default.
- If the teacher explicitly sets `update_existing=true`, existing students may update name, gender, current class, status, and remark.
- If the same Excel file contains the same `student_no` more than once, later rows fail instead of overriding earlier rows.
- Valid rows are written.
- Invalid rows are recorded in `import_errors`.
- The response includes `batch_id`, `success_count`, `failed_count`, and a short summary.

Score import:

- Teacher selects an exam and uploads an Excel file.
- The template may include all classes or a single class through `class_id`.
- Import validates exam ownership, exam student snapshot, course columns, score status, numeric score range, and duplicate rows.
- Existing scores are failed rows by default.
- If the teacher explicitly sets `overwrite_existing=true`, existing score, status, and remark values may be overwritten.
- If the same Excel file contains the same `exam_student + exam_subject` more than once, later rows fail instead of overriding earlier rows.
- Imported rows must resolve to `exam_students` snapshots, not directly to current `students.class_id`.
- Valid rows are written.
- Invalid rows are recorded in `import_errors`.
- Failed rows are never silently skipped.

First-version import uses "write valid rows and report invalid rows". A future version can add `dry_run=true` for validation-only import preview before write.

Import batch status rules:

- `success`: all validatable rows were written or updated.
- `partial_success`: at least one row succeeded and at least one row failed.
- `failed`: no data rows were written.
- `processing` is used only while a batch is being parsed and written.
- `pending` may be used before asynchronous processing begins if imports become asynchronous later.

## Frontend Design

The UI follows a clean education-management dashboard style:

- Narrow, light-colored sidebar.
- Main work area close to the sidebar, without a large visual gap.
- Fresh teal/blue accent palette, avoiding a heavy full-blue sidebar.
- Compact cards and panels.
- Rounded corners around 8px.
- Dashboard designed for scanning, not as a marketing page.

Main pages:

- Login/register.
- Dashboard.
- Class management.
- Student management.
- Course management.
- Schedule management.
- Exam management.
- Score entry.
- Score import/result.
- Statistics.
- Import records.
- Account settings.

Dashboard:

- Summary metrics.
- Today's schedule.
- Recent exams.
- Quick actions.
- Score overview.
- Class average score trend.

Score entry:

- Student rows and exam subject columns.
- Numeric score input.
- Status selector for absent, deferred, cheating, and exempt.
- Bulk save.
- Failed cells are highlighted.
- Failure details are shown near the affected cell.

Statistics:

- Exam summary.
- Total and subject rankings.
- Score segments.
- Absent/deferred/cheating/exempt lists.
- Missing score count.
- Status multi-select for included statistics statuses, defaulting to normal scores only.
- Student history trend.

## Business Rules

- A teacher can access only their own data.
- Teacher-owned foreign keys must be internally consistent. For example, `students.teacher_id` must match the referenced class owner, and `schedules.teacher_id` must match the referenced class and course owners.
- An exam must include at least one class and one subject.
- An exam's student list is frozen into `exam_students` for historical correctness.
- Score-sheet refresh must use a merge/retention policy after scoring starts, not a destructive rebuild.
- A score can be entered only for a student in the exam snapshot.
- Scores reference `exam_students` directly through `exam_student_id`.
- Score student and class data are resolved from `exam_students`; `scores` does not duplicate `student_id` or `class_id` in the first version.
- Exam threshold updates must preserve `0 <= pass_score <= excellent_score <= full_score` and may not make existing normal scores exceed the full score.
- Soft deletion is preferred for classes, students, courses, exams, and subjects with historical data.
- Missing score row means not entered.
- Abnormal score status is distinct from missing score.
- Statistics default to normal scores only and can include abnormal or missing statuses through `included_statuses`.

## Testing

Backend tests:

- Register and login.
- JWT expiration and unauthorized access.
- Teacher data isolation.
- Student ownership consistency with the referenced class.
- Unique constraints for students, courses, exam subjects, and scores.
- Schedule CRUD and class/course ownership consistency.
- Creating exams with classes and subjects.
- Generating exam student snapshots.
- Preventing score entry for students not in an exam snapshot.
- Preventing score entry when `exam_student_id` and `exam_subject_id` belong to different exams.
- Rejecting score payloads that try to set `student_id` or `class_id` directly.
- Score status and numeric score validation.
- Preventing deletion/removal of subjects with scores.
- Class removal before scoring, class append after scoring, and class removal rejection when scores exist.
- Bulk score save with item-level failure results.
- Student import success and error rows.
- Student import duplicate handling and `update_existing=true`.
- Score import success and error rows.
- Score import duplicate handling and `overwrite_existing=true`.
- Statistics for average, rankings, segments, abnormal statuses, missing scores, and `included_statuses`.
- Dashboard summary, today schedule, recent exams, score overview, and class average trend.

Frontend verification:

- Login flow and token expiration redirect.
- Pagination and filters.
- Score entry table editing.
- Failed score cells display correctly.
- Import result and error detail pages.
- Statistics status filters update charts and tables.
- Dashboard layout remains compact and does not overlap at common desktop widths.
