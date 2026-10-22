import { describe, expect, it } from 'vitest'
import { MAX_UPLOAD_MB, validateFile } from '../api/materials'

const file = (name: string, size = 100) => {
  const f = new File(['x'], name)
  Object.defineProperty(f, 'size', { value: size })
  return f
}

describe('validateFile', () => {
  it('accepts PDF, PPTX and DOCX regardless of case', () => {
    expect(validateFile(file('lecture.pdf'))).toBeNull()
    expect(validateFile(file('deck.PPTX'))).toBeNull()
    expect(validateFile(file('notes.docx'))).toBeNull()
  })

  it('rejects other extensions and files without one', () => {
    expect(validateFile(file('virus.exe'))).toMatch(/only pdf, pptx and docx/i)
    expect(validateFile(file('noext'))).toMatch(/only pdf, pptx and docx/i)
  })

  it('rejects empty and oversize files', () => {
    expect(validateFile(file('a.pdf', 0))).toMatch(/empty/i)
    expect(validateFile(file('a.pdf', MAX_UPLOAD_MB * 1024 * 1024 + 1))).toMatch(/larger than/i)
  })
})
