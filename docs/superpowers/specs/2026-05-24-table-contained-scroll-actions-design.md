# Table Contained Scroll And Sticky Actions Design

## Context

The score management table has enough columns that the row action can be pushed outside the visible area. The current experience makes teachers drag horizontally to the far right before saving a score.

The same risk exists on other Element Plus tables when they grow wider, especially pages with a final `操作` column:

- `ScoreManagementView`
- `ExamCenterView`
- `StatisticsView`
- `ImportRecordsView`
- `ClassesStudentsView`
- `CoursesScheduleView`

Tables without row actions still benefit from contained horizontal scrolling because the page layout should remain stable.

## Decision

Use contained table scrolling and sticky row actions.

1. Horizontal overflow should stay inside the table body/header area.
2. The overall page and card layout should not become horizontally scrollable because of a wide table.
3. Wide tables with row actions should keep the `操作` column fixed to the right side of the table.
4. Score management keeps its direct `保存` button visible; it should not be hidden inside a menu.
5. Other pages with `操作` columns should follow the same fixed-right behavior for consistency.
6. Data tables should gain light cell borders so wide rows are easier to scan without looking visually heavy.

## Scope

In scope:

- Add a reusable frontend convention for wide Element Plus tables.
- Apply the convention to score management and other existing row-action tables.
- Preserve current table columns, button labels, routes, save behavior, filters, and pagination.
- Keep horizontal scrolling on the table itself when content exceeds available width.

Out of scope:

- Removing or merging existing columns.
- Converting row actions to dropdown menus.
- Changing backend APIs or pagination behavior.
- Redesigning score entry's subject-grid editing workflow beyond ensuring it does not widen the page.

## Frontend Behavior

For wide action tables:

- Wrap or configure tables so Element Plus owns the horizontal scroll area.
- Set `fixed="right"` on the final `操作` column.
- Keep explicit widths on action columns so the fixed area is predictable.
- Use `min-width` for content columns that may grow, letting the table create an internal scrollbar when needed.

For wide non-action tables:

- Keep overflow contained within the table region.
- Do not add sticky action behavior when no row actions exist.

For page layout:

- Page cards should allow internal children to shrink with `min-width: 0`.
- The app main content should not expose a document-level horizontal scrollbar due to tables.

## Visual Polish

Tables should use a restrained grid treatment:

- Add light one-pixel cell dividers to data tables.
- Use low-contrast border colors that sit near the existing page border palette.
- Keep row height and existing density stable.
- Avoid heavy dark grid lines or a spreadsheet-like visual weight.
- Keep the fixed operation column visually separated with a subtle left border or shadow so it reads as pinned while the table scrolls under it.

This polish should apply consistently to the existing management and list tables. It should not change form controls inside cells beyond the surrounding table borders.

## Affected Tables

Action columns should become fixed-right in:

- Score management score records
- Exam center exam list
- Statistics exam list
- Import records list
- Class list
- Student list
- Course list
- Schedule list

The score entry table already represents a matrix rather than row actions. It should keep internal table scrolling without adding a row action column.

## Testing

Tests should cover the behavior structurally:

- Score management marks its operation column as fixed-right.
- Other row-action tables mark their operation columns as fixed-right.
- No page-level horizontal scrollbar is introduced when tables are wider than the viewport.
- Wide data tables opt into the light bordered table treatment.

Verification should include:

- focused frontend tests for table column configuration or rendered behavior
- frontend lint
- frontend build
