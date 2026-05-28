import { afterEach, describe, expect, it, vi } from 'vitest'
import { downloadBlob } from '../src/utils/download'

describe('downloadBlob', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('downloads a blob with the requested filename and releases the URL', () => {
    const click = vi.fn()
    const anchor = {
      href: '',
      download: '',
      click,
    } as unknown as HTMLAnchorElement
    const createObjectURL = vi.fn(() => 'blob:template')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })
    const createElement = vi.spyOn(document, 'createElement').mockReturnValue(anchor)

    const blob = new Blob(['template'])
    downloadBlob(blob, 'student-import-template.xlsx')

    expect(createObjectURL).toHaveBeenCalledWith(blob)
    expect(createElement).toHaveBeenCalledWith('a')
    expect(anchor.href).toBe('blob:template')
    expect(anchor.download).toBe('student-import-template.xlsx')
    expect(click).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:template')
  })
})
