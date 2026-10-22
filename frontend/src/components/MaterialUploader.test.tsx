import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import * as materials from '../api/materials'
import { MaterialUploader } from './MaterialUploader'

describe('MaterialUploader', () => {
  it('rejects an unsupported file before any request is made', async () => {
    const upload = vi.spyOn(materials, 'uploadMaterial')
    const onUploaded = vi.fn()
    render(<MaterialUploader courseId="c" topicId="t" onUploaded={onUploaded} />)

    const input = screen.getByLabelText(/upload material/i)
    await userEvent.upload(input, new File(['MZ'], 'virus.exe'), { applyAccept: false })

    expect(await screen.findByRole('alert')).toHaveTextContent(/only pdf, pptx and docx/i)
    expect(upload).not.toHaveBeenCalled()
    expect(onUploaded).not.toHaveBeenCalled()
    upload.mockRestore()
  })

  it('uploads a valid file and reports success', async () => {
    const upload = vi
      .spyOn(materials, 'uploadMaterial')
      .mockResolvedValue({ id: 'm1' } as materials.Material)
    const onUploaded = vi.fn()
    render(<MaterialUploader courseId="c" topicId="t" onUploaded={onUploaded} />)

    await userEvent.upload(
      screen.getByLabelText(/upload material/i),
      new File(['%PDF-1.4'], 'lecture.pdf', { type: 'application/pdf' }),
    )

    expect(await screen.findByRole('status')).toHaveTextContent('Uploaded lecture.pdf.')
    expect(upload).toHaveBeenCalledWith('c', 't', expect.any(File), expect.any(Function))
    expect(onUploaded).toHaveBeenCalledOnce()
    upload.mockRestore()
  })
})
