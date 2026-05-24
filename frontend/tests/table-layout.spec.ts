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
  })
})
