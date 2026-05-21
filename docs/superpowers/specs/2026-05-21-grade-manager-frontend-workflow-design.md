# Grade Manager Frontend Workflow Design

## Relationship To Existing Design

This document supplements `docs/superpowers/specs/2026-05-20-grade-manager-design.md`.

The existing design remains the system-level source of truth for:

- backend technology choices
- data model
- API scope
- authentication and teacher data isolation
- import behavior
- statistics rules
- business constraints

This document adds frontend-specific detail for:

- page structure
- navigation
- teacher workflow
- key page responsibilities
- frontend data flow
- visual layout constraints

If the two documents appear to conflict, backend data rules, API behavior, and business rules follow the existing system design. Frontend page organization, workflow details, and visual layout follow this document.

## Decisions

The frontend uses an exam-driven workflow with desktop-first layout.

Confirmed decisions:

- Student lists are commonly imported from Excel, while scores may be imported or entered manually.
- Score work starts from an exam.
- Exam creation uses a step-by-step wizard.
- Score entry combines focused entry and whole-exam table views.
- Excel import writes valid rows and reports invalid rows.
- After score entry or import, the main flow leads to the exam statistics overview.
- Desktop and notebook screens are the primary target. Mobile only needs basic accessibility in the first version.

## Overall Page Structure

The frontend uses a light, desktop-oriented management layout:

- narrow left sidebar
- top bar with global search, notification icon, teacher avatar, and teacher name
- main work area close to the sidebar
- white cards on a light gray background
- fresh teal and blue accents
- compact but readable spacing

The app should look like a professional education management dashboard, not a marketing site.

Main navigation uses merged entries to avoid an overly long sidebar:

1. Dashboard
2. Classes And Students
3. Courses And Schedule
4. Exam Center
5. Statistics
6. Import Records
7. Account Settings

Navigation rules:

- Exam Center is the main entry for exam, score entry, score import, and per-exam statistics work.
- Classes And Students and Courses And Schedule are setup and maintenance areas.
- Statistics and Import Records are review and troubleshooting areas.
- Dashboard aggregates important status and quick actions but does not become a complex task system in the first version.

## Core Workflow

The core workflow is an exam-driven loop:

1. Prepare base data.
2. Create an exam.
3. Enter or import scores.
4. Fix import or save errors.
5. View the exam statistics overview.
6. Return later through Dashboard, Exam Center, Statistics, or Import Records.

### Prepare Base Data

Teachers create classes in Classes And Students, then import student lists from Excel or add students manually. The same module supports student search, filtering, pagination, status changes, and edits.

Teachers maintain courses and a simple weekly schedule in Courses And Schedule. The first version uses the schedule mainly for Dashboard display. It does not include conflict detection, class adjustments, cancellations, makeups, or semester schedule versioning.

### Create Exam

Teachers create exams from Exam Center through a wizard:

1. Basic information: exam name, exam type, term, remarks.
2. Participating classes.
3. Exam subjects: course, full score, pass score, excellent score, exam date, remarks.
4. Confirmation: review settings and create the exam.

After creation, the teacher should be able to go directly to score entry. They should not have to search through multiple menus to continue.

### Enter Scores

Score entry is organized around one exam.

The score entry page supports:

- focused entry view: filter by class and subject for daily score entry
- whole-exam table view: students as rows and subjects as columns for full-table review and batch editing
- numeric score input
- abnormal status selection for absent, deferred, cheating, and exempt
- bulk save
- failed-cell highlighting
- near-cell failure details when a save returns item-level errors

### Import Scores

Score import starts from Exam Center or the score entry page.

The teacher can download a template, upload an Excel file, and receive a batch result:

- success count
- failure count
- batch status
- row number
- field
- raw value
- reason

The first version follows the existing backend design: valid rows are written, invalid rows are reported. Failed rows are never silently skipped.

### View Statistics

After manual save or import, the main flow leads to the current exam's statistics overview.

The statistics page shows:

- average score
- highest score
- lowest score
- pass rate
- excellent rate
- abnormal status counts
- missing score count
- class comparison
- subject comparison
- score segments
- ranking entry points
- absent, deferred, cheating, exempt, and missing-score lists

The default included status is normal scores only. Status filters call backend statistics APIs instead of recalculating statistics in the frontend.

## Key Pages

### Dashboard

The Dashboard follows the approved HTML preview direction.

It includes:

- top metric cards: class count, student count, course count, pending score count
- today's schedule
- recent exams
- score overview for the latest relevant exam
- class average trend
- quick actions for creating an exam, importing students, entering scores, and viewing statistics

Dashboard is for scanning and returning to work. It should not contain complex editing flows.

### Classes And Students

This page combines class and student work.

It supports:

- class list or class filter
- class create and edit
- student table
- student create and edit
- student Excel import
- keyword search
- status filter
- pagination

Student import results can be shown immediately and linked to Import Records for later review.

### Courses And Schedule

This page uses two tabs:

- course management
- weekly schedule

Course management maintains course name, status, and remarks.

Weekly schedule maintains class, course, weekday, period number, optional start and end time, location, status, and remarks. The first version keeps this as basic CRUD for dashboard display.

### Exam Center

Exam Center is the core work area.

It includes:

- exam list
- keyword, type, term, and status filters
- create exam wizard
- exam detail page
- score entry entry point
- score import entry point
- exam statistics entry point

The exam detail page shows basic information, participating classes, subjects, score entry status, and primary actions.

### Score Entry

The score entry page starts from one exam.

The top area keeps exam information and filters visible:

- class
- subject
- view mode

The table supports score editing, abnormal status selection, bulk save, failed-cell highlighting, and error detail display.

### Exam Statistics

The exam statistics page starts from Exam Center or after score save/import.

It shows the current exam's core indicators, class comparison, subject comparison, score segments, rankings, abnormal status lists, and missing score lists. It does not edit scores.

### Import Records

Import Records shows both student imports and score imports.

The list includes:

- import type
- target object
- file name
- status
- success count
- failure count
- import time

The detail page shows row-level errors and lets teachers locate data problems before re-importing a corrected file.

## Frontend Data Flow

The backend is the final source of truth. The frontend stores only necessary page state and authentication state.

Authentication:

- Login stores JWT and teacher information.
- Axios adds the token through an interceptor.
- `401` clears the session and redirects to login.
- Pinia stores auth state, current teacher, and minimal cross-page state.

Exam creation:

- The wizard stores step data locally.
- The final step submits to `POST /api/v1/exams`.
- Success navigates to exam detail or score entry.
- The score sheet loads through `GET /api/v1/exams/{id}/score-sheet`.

Score entry:

- The score sheet is loaded by exam.
- Class, subject, and view filters are frontend presentation state.
- Cell edits stay local until bulk save.
- Bulk save calls `PUT /api/v1/exams/{id}/scores`.
- Item-level failures highlight the affected cells.

Import:

- Student import starts from Classes And Students.
- Score import starts from Exam Center or Score Entry.
- Results show batch status, success count, failure count, and error details.
- Import detail is linked to Import Records.

Statistics:

- Statistics pages call backend statistics APIs.
- Changing included statuses reloads statistics from the backend.
- The frontend does not duplicate backend statistics rules.

## Error Handling

Frontend handling follows the existing error format.

Expected behavior:

- `401`: session expired or invalid; clear auth state and redirect to login.
- `403`: show no-permission message.
- `404`: show not-found or no-access message.
- `409`: show duplicate conflict near the relevant field.
- `422`: show validation details, including row, field, raw value, and reason where available.
- `400`: show business-rule failure, such as an exam class that cannot be removed after scoring.
- `500`: show a generic system error without exposing technical details.

Score save failures should be shown near the affected table cell when possible. Import failures should be shown as row-level details.

## Visual And Layout Constraints

The visual baseline is the fifth preview:

`.superpowers/brainstorm/32672-1779371349/content/frontend-workflow-preview-compact-v5.html`

This preview is a discussion artifact, not production frontend code.

### Density

The interface should be compact in the distance between areas:

- sidebar to content
- card to card
- panel to panel
- dashboard sections

Compact does not mean squeezing content inside each card. Card interiors must keep readable spacing for labels, values, tables, charts, and error messages.

### Sidebar

Sidebar rules:

- width around `200-220px`
- merged navigation entries
- light teal or light blue background
- no heavy dark sidebar
- low-saturation functional color accents
- each navigation group may use a subtle colored marker or icon background
- active item should be clear without becoming visually heavy

### Main Area

Main area rules:

- content starts close to the sidebar
- card gaps around `8-12px`
- card radius around `8px`
- light shadow only
- white cards on light gray background
- low-saturation statistic icons
- no large high-saturation gradient blocks for dashboard metrics

### Dashboard Score Overview

The Dashboard score overview card must include:

- average score
- highest score
- lowest score
- abnormal status count
- abnormal status distribution title
- donut chart with total count in the center
- low-score warning count and percentage
- failing count and percentage
- absent count and percentage
- cheating count and percentage

The card should use a two-part vertical layout:

- upper metric block
- lower abnormal distribution block

The two blocks should fill the card naturally. The lower distribution block should not look cramped or leave obvious empty space.

### Color

Use:

- fresh teal and blue as the main accent direction
- low-saturation blue, indigo, amber, purple, and green for function differentiation
- light gray page background
- dark gray body text

Avoid:

- dominant dark blue sidebars
- high-saturation metric gradients
- large purple-blue gradients
- heavy shadows
- one-note single-color palette

## Testing And Verification

Frontend verification should cover:

- login and token-expiration redirect
- dashboard layout at common desktop widths
- no overlap or excessive empty spacing in the dashboard
- sidebar width and sidebar-to-content distance
- dashboard metric icon saturation
- score overview card completeness and proportion
- create exam wizard
- student import result display
- score entry focused view and whole-exam table view
- score save failure highlighting
- score import partial success and row-level error display
- statistics status filter refresh

During implementation, visual review is required in addition to functional checks.
