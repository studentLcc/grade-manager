import { describe, expect, it } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const projectRoot = join(dirname(fileURLToPath(import.meta.url)), '..')

function collectVueFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry)
    if (statSync(path).isDirectory()) return collectVueFiles(path)
    return path.endsWith('.vue') ? [path] : []
  })
}

function readProjectFile(path: string) {
  return readFileSync(join(projectRoot, path), 'utf8')
}

describe('table layout conventions', () => {
  it('opts every Element Plus table into the polished bordered data table treatment', () => {
    const offenders: string[] = []

    for (const file of collectVueFiles(join(projectRoot, 'src'))) {
      const source = readFileSync(file, 'utf8')
      for (const match of source.matchAll(/<el-table(?!-)\b[\s\S]*?>/g)) {
        const declaration = match[0].replace(/\s+/g, ' ')
        if (!/\bborder\b/.test(declaration) || !/\bclass="gm-data-table"/.test(declaration)) {
          offenders.push(`${relative(projectRoot, file)}: ${declaration}`)
        }
      }
    }

    expect(offenders).toEqual([])
  })

  it('fixes every operation column to the right side of its table', () => {
    const offenders: string[] = []

    for (const file of collectVueFiles(join(projectRoot, 'src'))) {
      const source = readFileSync(file, 'utf8')
      for (const match of source.matchAll(/<el-table-column\b(?=[^>]*label="操作")[^>]*>/g)) {
        const declaration = match[0].replace(/\s+/g, ' ')
        if (!/\bfixed="right"/.test(declaration)) {
          offenders.push(`${relative(projectRoot, file)}: ${declaration}`)
        }
      }
    }

    expect(offenders).toEqual([])
  })

  it('wraps paginated tables through the shared table surface component', () => {
    const requiredFiles = [
      'src/views/ClassesStudentsView.vue',
      'src/views/CoursesScheduleView.vue',
      'src/views/ExamStatisticsView.vue',
      'src/views/ExamCenterView.vue',
      'src/views/StatisticsView.vue',
      'src/views/ScoreManagementView.vue',
      'src/views/ScoreEntryView.vue',
      'src/views/ExamDetailView.vue',
      'src/views/ImportRecordsView.vue',
      'src/views/ImportDetailView.vue',
    ]
    for (const file of requiredFiles) {
      const source = readProjectFile(file)
      expect(source, file).toContain("TableSurface")
      expect(source, file).toContain("<TableSurface")
      expect(source, file).not.toContain('class="gm-table-surface"')
      expect(source, file).not.toContain('class="gm-table-toolbar"')
      expect(source, file).not.toContain('class="gm-table-viewport"')
      expect(source, file).not.toContain('class="gm-pagination"')
    }

    const surfaceSource = readProjectFile('src/components/common/TableSurface.vue')
    expect(surfaceSource).toContain('class="gm-table-surface"')
    expect(surfaceSource).toContain('class="gm-table-toolbar"')
    expect(surfaceSource).toContain('class="gm-table-viewport"')
    expect(surfaceSource).toContain('class="gm-pagination"')
    expect(surfaceSource).toContain('compact?: boolean')
    expect(surfaceSource).toContain('is-compact')
    expect(readProjectFile('src/views/ExamDetailView.vue')).toContain('<TableSurface compact>')
  })

  it('uses the shared compact pagination component for table surfaces', () => {
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
      expect(source, file).toContain("TablePagination")
      expect(source, file).toContain("<TablePagination")
    }

    const vueOffenders: string[] = []
    for (const file of collectVueFiles(join(projectRoot, 'src'))) {
      const relativeFile = relative(projectRoot, file).replace(/\\/g, '/')
      if (relativeFile === 'src/components/common/TablePagination.vue') continue
      const source = readFileSync(file, 'utf8')
      if (source.includes('<el-pagination')) vueOffenders.push(relativeFile)
    }
    expect(vueOffenders).toEqual([])

    const paginationSource = readProjectFile('src/components/common/TablePagination.vue')
    expect(paginationSource).toContain('<el-pagination')
    expect(paginationSource).toContain(':pager-count="5"')
    expect(paginationSource).toContain('small')
    expect(paginationSource).toContain('layout="prev, pager, next, sizes"')
    expect(paginationSource).toContain(':page-sizes="[10, 20, 50, 100]"')
    expect(paginationSource).toContain("defineModel<number>('currentPage'")
    expect(paginationSource).toContain("defineModel<number>('pageSize'")
  })

  it('does not duplicate tab labels above tabbed management tables', () => {
    const tabbedManagementPages = [
      'src/views/ClassesStudentsView.vue',
      'src/views/CoursesScheduleView.vue',
    ]

    for (const file of tabbedManagementPages) {
      const source = readProjectFile(file)
      expect(source, file).not.toContain('gm-tab-label-row')
    }

    expect(readProjectFile('src/styles/app.css')).not.toContain('gm-tab-label-row')
  })

  it('contains the global CSS needed for contained scrolling and lightweight scan cues', () => {
    const css = readProjectFile('src/styles/app.css')

    expect(css).toMatch(/\.gm-main\s*{[^}]*overflow-x:\s*hidden/s)
    expect(css).toMatch(/\.gm-page-card\s*{[^}]*min-width:\s*0/s)
    expect(css).toContain('.gm-table-surface')
    expect(css).toContain('.gm-table-toolbar')
    expect(css).toContain('.gm-table-viewport')
    expect(css).toMatch(/\.gm-management-page\s*>\s*\.gm-page-card:has\(>\s*\.gm-table-surface\)\s*>\s*\.gm-table-surface\s*{[^}]*height:\s*clamp\(420px,\s*calc\(100vh - 192px\),\s*760px\)/s)
    expect(css).toMatch(/\.gm-management-page\s*>\s*\.gm-page-card:has\(>\s*\.gm-table-surface\)\s*>\s*\.gm-table-surface\s*{[^}]*max-height:\s*none/s)
    expect(css).toMatch(/\.gm-management-page\s*>\s*\.gm-page-card:has\(>\s*\.gm-section-title\s*\+\s*\.gm-table-surface\)\s*>\s*\.gm-table-surface\s*{[^}]*height:\s*clamp\(360px,\s*calc\(100vh - 300px\),\s*620px\)/s)
    expect(css).toMatch(/\.gm-table-toolbar\s+\.gm-filter-row\s*{[^}]*gap:\s*8px/s)
    expect(css).toMatch(/\.gm-table-toolbar\s+\.gm-filter-row\s+\.el-select\s*{[^}]*width:\s*120px/s)
    expect(css).toMatch(/\.gm-table-toolbar\s+\.gm-filter-row-wide\s+\.el-input\s*{[^}]*width:\s*170px/s)
    expect(css).toMatch(/\.gm-table-surface\s+\.gm-pagination\s+\.el-select\s*{[^}]*width:\s*92px/s)
    expect(css).toMatch(/\.gm-table-surface\s+\.gm-pagination\s+\.el-pagination\s*{[^}]*max-width:\s*100%/s)
    expect(css).toMatch(/\.gm-table-surface\s+\.gm-pagination\s+\.el-pager\s+li\s*{[^}]*min-width:\s*26px/s)
    expect(css).toMatch(/\.gm-table-surface\s+\.gm-pagination\s+\.el-pagination\s+button\s*{[^}]*min-width:\s*26px/s)
    expect(css).toMatch(/\.gm-table-surface\.is-compact\s*{[^}]*min-height:\s*0/s)
    expect(css).toMatch(/\.gm-table-surface\.is-compact\s*{[^}]*max-height:\s*none/s)
    expect(css).toMatch(/\.gm-management-page\s*>\s*\.gm-page-card:has\(>\s*\.gm-table-surface\)\s*>\s*\.gm-table-surface\.is-compact\s*{[^}]*height:\s*auto/s)
    expect(css).toMatch(/\.gm-table-surface\.is-compact\s+\.gm-table-viewport\s*{[^}]*min-height:\s*0/s)
    expect(css).toMatch(/\.gm-stats-control-card\s*{[^}]*display:\s*flex/s)
    expect(css).toMatch(/\.gm-stats-control-card\s*{[^}]*align-items:\s*center/s)
    expect(css).toMatch(/\.gm-stats-control-card\s*{[^}]*flex-wrap:\s*nowrap/s)
    expect(css).toMatch(/\.gm-table-viewport\s*{[^}]*overflow:\s*auto/s)
    expect(css).toMatch(/\.gm-table-surface\s+\.gm-pagination\s*{[^}]*border-top:/s)
    expect(css).toMatch(/\.gm-management-page:has\(>\s*\.gm-page-header\s*\+\s*\.gm-page-card\s*>\s*\.el-tabs\)\s*{[^}]*height:\s*calc\(100vh - 84px\)/s)
    expect(css).toMatch(/\.gm-management-page:has\(>\s*\.gm-page-header\s*\+\s*\.gm-page-card\s*>\s*\.el-tabs\)\s*{[^}]*overflow:\s*hidden/s)
    expect(css).toMatch(/\.gm-management-page:has\(>\s*\.gm-page-header\s*\+\s*\.gm-page-card\s*>\s*\.el-tabs\)\s*{[^}]*grid-template-rows:\s*auto minmax\(0,\s*1fr\)/s)
    expect(css).toMatch(/\.gm-management-page\s*>\s*\.gm-page-card:has\(>\s*\.el-tabs\)\s*{[^}]*display:\s*grid/s)
    expect(css).toMatch(/\.gm-page-card\s*>\s*\.el-tabs\s*{[^}]*display:\s*flex/s)
    expect(css).toMatch(/\.gm-page-card\s+\.el-tab-pane\s*>\s*\.gm-table-surface\s*{[^}]*flex:\s*1 1 auto/s)
    expect(css).toMatch(/\.gm-page-card\s+\.el-tab-pane\s*>\s*\.gm-table-surface\s*{[^}]*height:\s*auto/s)
    expect(css).toContain('.gm-data-table')
    expect(css).toContain('.gm-data-table .el-table__header-wrapper th')
    expect(css).toContain('.gm-data-table .el-table__body-wrapper td:first-child')
    expect(css).toContain('.gm-data-table .el-table__row:hover')
    expect(css).toContain('.gm-data-table .el-table-fixed-column--right')
    expect(css).toContain('.gm-table-actions')
    expect(css).toContain('.gm-table-action')
    expect(css).toMatch(/\.gm-table-actions\s+\.el-button\s*\+\s*\.el-button\s*{[^}]*margin-left:\s*0/s)
    expect(css).toMatch(/\.gm-table-action\.el-button\s*{[^}]*width:\s*30px/s)
    expect(css).toMatch(/\.gm-table-action\.el-button\s*{[^}]*height:\s*30px/s)
    expect(css).toMatch(/\.gm-main\s*{[^}]*padding:\s*10px 14px 16px/s)
    expect(css).toMatch(/\.gm-dashboard\s*{[^}]*--gm-gap:\s*8px/s)
    expect(css).toMatch(/\.gm-dashboard\s+\.gm-page-header\s*{[^}]*padding:\s*10px 12px/s)
    expect(css).toMatch(/\.gm-metric-card\s*{[^}]*min-height:\s*60px/s)
    expect(css).toMatch(/\.gm-dashboard-grid\s*{[^}]*align-items:\s*start/s)
    expect(css).toMatch(/\.gm-trend-card\s*{[^}]*max-height:\s*none/s)
    expect(css).toMatch(/\.gm-trend-card\s*{[^}]*overflow:\s*hidden/s)
    expect(css).not.toMatch(/--gm-dashboard-list-height/)
    expect(css).not.toMatch(/--gm-dashboard-analysis-height/)
    expect(css).toMatch(/\.gm-dashboard-list\s*{[^}]*grid-template-rows:\s*auto auto/s)
    expect(css).toMatch(/\.gm-dashboard-list\s*{[^}]*height:\s*auto/s)
    expect(css).toMatch(/\.gm-dashboard-list\s*>\s*\.gm-stack-list\s*{[^}]*overflow:\s*hidden/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*height:\s*auto/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*align-self:\s*start/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*align-content:\s*start/s)
    expect(css).toMatch(/\.gm-score-overview,\s*\.gm-trend-card\s*{[^}]*gap:\s*8px/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*grid-template-rows:\s*30px 45px 55px 190px auto/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\.is-empty\s*{[^}]*grid-template-rows:\s*30px auto/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*>\s*\.gm-section-title\s*{[^}]*height:\s*30px/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*>\s*\.gm-trend-class-strip\s*{[^}]*height:\s*45px/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s+\.gm-trend-class-chip\s*{[^}]*height:\s*28px/s)
    expect(css).toMatch(/\.gm-score-metrics,\s*\.gm-trend-summary\s*{[^}]*height:\s*55px/s)
    expect(css).toMatch(/\.gm-score-class-filter\.gm-trend-class-strip\s*{[^}]*height:\s*45px/s)
    expect(css).toMatch(/\.gm-trend-class-strip\s*{[^}]*width:\s*100%/s)
    expect(css).toMatch(/\.gm-trend-class-strip\s*{[^}]*max-width:\s*100%/s)
    expect(css).toMatch(/\.gm-score-overview\s+\.gm-section-title\s*{[^}]*margin-bottom:\s*0/s)
    expect(css).toMatch(/\.gm-trend-card\s+\.gm-section-title\s*{[^}]*margin-bottom:\s*0/s)
    expect(css).toContain('.gm-score-class-filter')
    expect(css).not.toMatch(/\.gm-score-class-chip\s*{/)
    expect(css).toMatch(/\.gm-score-metrics\s*{[^}]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/s)
    expect(css).toMatch(/\.gm-trend-summary div,\s*\.gm-score-metrics div\s*{[^}]*padding:\s*7px 9px/s)
    expect(css).toMatch(/\.gm-analysis-visual-panel\s*{[^}]*height:\s*190px/s)
    expect(css).toMatch(/\.gm-trend-chart-shell\s*{[^}]*height:\s*190px/s)
    expect(css).toMatch(/\.gm-score-visuals\s*{[^}]*grid-template-columns:\s*150px minmax\(0,\s*1fr\)/s)
    expect(css).toContain('.gm-status-bar-row')
    expect(css).toContain('.gm-status-info-item')
    expect(css).toMatch(/\.gm-abnormal-content\s*{[^}]*grid-template-columns:\s*120px minmax\(0,\s*1fr\)/s)
    expect(css).toMatch(/\.gm-abnormal-grid\s*{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(130px,\s*1fr\)\)/s)
    expect(css).toMatch(/\.gm-abnormal-item\s*{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s*auto/s)
    expect(css).toMatch(/\.gm-abnormal-item\s*{[^}]*padding:\s*6px 7px/s)
    expect(css).toMatch(/\.gm-abnormal-item small\s*{[^}]*grid-column:\s*1 \/ -1/s)
    expect(css).toMatch(/\.gm-donut\s*{[^}]*width:\s*124px/s)
    expect(css).toMatch(/\.gm-donut\s*>\s*div\s*{[^}]*align-content:\s*center/s)
    expect(css).toMatch(/\.gm-donut\s*>\s*div\s*{[^}]*gap:\s*2px/s)
    expect(css).toMatch(/\.gm-status-info-grid\s*{[^}]*align-content:\s*start/s)
    expect(css).toMatch(/\.gm-status-info-grid\s*{[^}]*align-items:\s*start/s)
    expect(css).toMatch(/\.gm-status-info-item\s*{[^}]*padding:\s*5px 7px/s)
    expect(css).toMatch(/\.gm-status-label\s*{[^}]*line-height:\s*1\.2/s)
    expect(css).toMatch(/\.gm-status-info-item strong\s*{[^}]*line-height:\s*1\.15/s)
    expect(css).toContain('.gm-trend-axis-x')
    expect(css).toContain('.gm-trend-area')
    expect(css).toContain('.gm-trend-bar')
    expect(css).toMatch(/\.gm-trend-point-list\s*{[^}]*display:\s*grid/s)
    expect(css).toMatch(/\.gm-trend-point-list\s*{[^}]*align-content:\s*start/s)
    expect(css).toMatch(/\.gm-trend-point-list\s*{[^}]*align-items:\s*start/s)
    expect(css).toMatch(/\.gm-trend-point-list\s*{[^}]*overflow:\s*hidden/s)
    expect(css).not.toMatch(/\.gm-trend-point-list\s*{[^}]*overflow-x:\s*auto/s)
    expect(css).toMatch(/\.gm-trend-point\s*{[^}]*min-width:\s*0/s)
    expect(css).toMatch(/\.gm-trend-point-label\s*{[^}]*line-height:\s*1\.2/s)
    expect(css).toMatch(/\.gm-trend-point-value\s*{[^}]*line-height:\s*1\.15/s)
    expect(css).toMatch(/\.gm-score-cell\s+\.el-input-number,\s*\.gm-score-cell\s+\.el-select\s*{[^}]*width:\s*100%/s)
    expect(css).toMatch(/\.gm-score-cell\s+\.el-input-number,\s*\.gm-score-cell\s+\.el-select\s*{[^}]*min-width:\s*0/s)
    expect(css).toContain('.gm-exam-summary-grid')
    expect(css).toMatch(/\.gm-exam-summary-grid\s*{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(180px,\s*1fr\)\)/s)
    expect(css).toMatch(/\.gm-exam-summary-item\s*{[^}]*border:\s*1px solid #e4edf2/s)
    expect(css).toMatch(/\.gm-exam-classes-card\s*{[^}]*margin-bottom:\s*2px/s)
    expect(css).toMatch(/\.gm-exam-classes-card\s+\.gm-chip-row\s*{[^}]*margin-top:\s*10px/s)
    expect(css).toMatch(/\.gm-exam-subjects-card\s*{[^}]*margin-bottom:\s*8px/s)
    expect(css).toContain('.gm-analysis-legend')
    expect(css).toContain('.gm-recent-exam-row')
    expect(readProjectFile('src/components/dashboard/ScoreOverviewCard.vue')).toContain('gm-dashboard-analysis-card')
    expect(readProjectFile('src/components/dashboard/ClassAverageTrend.vue')).toContain('gm-dashboard-analysis-card')
    expect(readProjectFile('src/components/dashboard/ClassAverageTrend.vue')).toContain("'is-empty': !points.length")
  })
})
