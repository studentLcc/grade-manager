# Table Work Surface Design

## Context

Management and statistics pages currently place filters, Element Plus tables, and pagination directly inside page cards. This keeps the implementation simple, but it makes dense tables feel awkward:

- Users scroll the page to reach the pagination controls after scanning a table.
- The page can feel like one long list instead of a focused work area.
- Similar tables use the same data styling but do not share the same surrounding layout.

An earlier table design already standardized contained horizontal scrolling and fixed-right operation columns. This design extends that convention to the vertical table experience.

## Decision

Introduce a reusable table work surface pattern made of three regions:

1. A compact table toolbar for filters and primary actions.
2. A contained table viewport that owns table overflow.
3. A bottom pagination bar visually attached to the table surface.

The backend pagination model and existing `el-pagination` controls remain unchanged. The change is layout and visual behavior, not data behavior.

## Scope

In scope:

- Class management table.
- Student management table.
- Course management table.
- Weekly schedule table.
- Exam statistics ranking table.
- Exam statistics score segment table.
- Equivalent list tables that already share the same pagination issue: exam center, statistics exam list, score management, import records, import detail row errors.
- Global CSS and structural tests for the work surface convention.

Out of scope:

- Backend API changes.
- Infinite scroll or virtual scrolling.
- Removing page size selection.
- Changing table columns, filters, routes, row actions, or save behavior.
- Reworking dashboard cards beyond the existing dashboard fixes already in the worktree.

## Frontend Behavior

Each paginated table surface should render as:

```html
<div class="gm-table-surface">
  <div class="gm-table-toolbar">...</div>
  <div class="gm-table-viewport">
    <el-table class="gm-data-table" border />
  </div>
  <div class="gm-pagination">...</div>
</div>
```

For sections that already have a `gm-section-title`, the title remains outside the work surface so page hierarchy stays clear. Filters and action buttons move into `gm-table-toolbar` when they control the table.

The table viewport should:

- Use `min-height` so empty or short result sets still look intentional.
- Use `max-height` based on viewport height so long tables scroll within the surface.
- Keep horizontal overflow contained by the existing `gm-data-table` rules.
- Keep Element Plus fixed-right operation columns visible.

The pagination bar should:

- Stay close to the table viewport instead of floating far down the page.
- Use a subtle top border and compact padding.
- Wrap cleanly on narrow screens.

## Visual Style

The surface should feel utilitarian and quiet:

- No nested card styling inside `gm-page-card`.
- Use a light border and background only to group table tools, rows, and pagination.
- Keep compact spacing consistent with the current app.
- Avoid hero-like or decorative treatment.

## Testing

Structural tests should verify:

- Paginated table pages use `gm-table-surface`.
- Table surfaces include `gm-table-toolbar`, `gm-table-viewport`, and `gm-pagination` where applicable.
- Global CSS defines the table surface, toolbar, viewport, and attached pagination behavior.
- Existing table conventions remain: bordered `gm-data-table` tables, fixed-right operation columns, contained horizontal scrolling, compact action buttons.

Verification should include:

- Focused table layout tests.
- Existing management/statistics tests.
- Full frontend test suite.
- Frontend lint.
- Frontend build.
- Browser checks on dashboard-adjacent routes and the named table pages.
