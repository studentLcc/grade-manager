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

  it('contains the global CSS needed for contained scrolling and lightweight scan cues', () => {
    const css = readProjectFile('src/styles/app.css')

    expect(css).toMatch(/\.gm-main\s*{[^}]*overflow-x:\s*hidden/s)
    expect(css).toMatch(/\.gm-page-card\s*{[^}]*min-width:\s*0/s)
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
    expect(css).toMatch(/\.gm-trend-card\s*{[^}]*max-height:/s)
    expect(css).toMatch(/\.gm-trend-card\s*{[^}]*overflow:\s*hidden/s)
    expect(css).toMatch(/--gm-dashboard-list-height:\s*280px/)
    expect(css).toMatch(/--gm-dashboard-analysis-height:\s*460px/)
    expect(css).toMatch(/\.gm-dashboard-list\s*{[^}]*height:\s*var\(--gm-dashboard-list-height\)/s)
    expect(css).toMatch(/\.gm-dashboard-list\s*>\s*\.gm-stack-list\s*{[^}]*overflow:\s*hidden/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*height:\s*var\(--gm-dashboard-analysis-height\)/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*align-self:\s*start/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*{[^}]*align-content:\s*start/s)
    expect(css).toMatch(/\.gm-score-overview,\s*\.gm-trend-card\s*{[^}]*gap:\s*8px/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*>\s*\.gm-section-title\s*{[^}]*min-height:\s*26px/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s*>\s*\.gm-trend-class-strip\s*{[^}]*min-height:\s*30px/s)
    expect(css).toMatch(/\.gm-dashboard-analysis-card\s+\.gm-trend-class-chip\s*{[^}]*height:\s*28px/s)
    expect(css).toMatch(/\.gm-score-class-filter\.gm-trend-class-strip\s*{[^}]*min-height:\s*44px/s)
    expect(css).toMatch(/\.gm-score-class-filter\.gm-trend-class-strip\s*{[^}]*padding-bottom:\s*10px/s)
    expect(css).toMatch(/\.gm-trend-class-strip\s*{[^}]*width:\s*100%/s)
    expect(css).toMatch(/\.gm-trend-class-strip\s*{[^}]*max-width:\s*100%/s)
    expect(css).toMatch(/\.gm-score-overview\s+\.gm-section-title\s*{[^}]*margin-bottom:\s*0/s)
    expect(css).toMatch(/\.gm-trend-card\s+\.gm-section-title\s*{[^}]*margin-bottom:\s*0/s)
    expect(css).toContain('.gm-score-class-filter')
    expect(css).not.toMatch(/\.gm-score-class-chip\s*{/)
    expect(css).toMatch(/\.gm-score-metrics\s*{[^}]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\)/s)
    expect(css).toMatch(/\.gm-trend-summary div,\s*\.gm-score-metrics div\s*{[^}]*padding:\s*7px 9px/s)
    expect(css).toMatch(/\.gm-analysis-visual-panel\s*{[^}]*height:\s*190px/s)
    expect(css).toMatch(/\.gm-trend-chart-shell\s*{[^}]*height:\s*230px/s)
    expect(css).toMatch(/\.gm-score-visuals\s*{[^}]*grid-template-columns:\s*150px minmax\(0,\s*1fr\)/s)
    expect(css).toContain('.gm-status-bar-row')
    expect(css).toContain('.gm-status-info-item')
    expect(css).toMatch(/\.gm-abnormal-content\s*{[^}]*grid-template-columns:\s*120px minmax\(0,\s*1fr\)/s)
    expect(css).toMatch(/\.gm-abnormal-grid\s*{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(130px,\s*1fr\)\)/s)
    expect(css).toMatch(/\.gm-abnormal-item\s*{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s*auto/s)
    expect(css).toMatch(/\.gm-abnormal-item\s*{[^}]*padding:\s*6px 7px/s)
    expect(css).toMatch(/\.gm-abnormal-item small\s*{[^}]*grid-column:\s*1 \/ -1/s)
    expect(css).toMatch(/\.gm-donut\s*{[^}]*width:\s*124px/s)
    expect(css).toContain('.gm-trend-axis-x')
    expect(css).toContain('.gm-trend-area')
    expect(css).toContain('.gm-trend-bar')
    expect(css).toMatch(/\.gm-trend-point-list\s*{[^}]*display:\s*grid/s)
    expect(css).toMatch(/\.gm-trend-point-list\s*{[^}]*overflow:\s*hidden/s)
    expect(css).not.toMatch(/\.gm-trend-point-list\s*{[^}]*overflow-x:\s*auto/s)
    expect(css).toMatch(/\.gm-trend-point\s*{[^}]*min-width:\s*0/s)
    expect(css).toMatch(/\.gm-score-cell\s+\.el-input-number,\s*\.gm-score-cell\s+\.el-select\s*{[^}]*width:\s*100%/s)
    expect(css).toMatch(/\.gm-score-cell\s+\.el-input-number,\s*\.gm-score-cell\s+\.el-select\s*{[^}]*min-width:\s*0/s)
    expect(css).toContain('.gm-analysis-legend')
    expect(css).toContain('.gm-recent-exam-row')
    expect(readProjectFile('src/components/dashboard/ScoreOverviewCard.vue')).toContain('gm-dashboard-analysis-card')
    expect(readProjectFile('src/components/dashboard/ClassAverageTrend.vue')).toContain('gm-dashboard-analysis-card')
  })
})
