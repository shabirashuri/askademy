import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { LoginPage } from './LoginPage'

const login = vi.fn()

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ user: null, loading: false, login, logout: vi.fn() }),
}))

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <LoginPage />
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  it('keeps the submit button disabled until both fields are filled', async () => {
    renderPage()
    const button = screen.getByRole('button', { name: /log in/i })
    expect(button).toBeDisabled()
    await userEvent.type(screen.getByLabelText(/email/i), 'a@example.com')
    expect(button).toBeDisabled()
    await userEvent.type(screen.getByLabelText(/password/i), 'secret')
    expect(button).toBeEnabled()
  })

  it('submits the trimmed email and password', async () => {
    login.mockResolvedValue({ id: '1', role: 'teacher' })
    renderPage()
    await userEvent.type(screen.getByLabelText(/email/i), '  a@example.com ')
    await userEvent.type(screen.getByLabelText(/password/i), 'secret')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    await waitFor(() => expect(login).toHaveBeenCalledWith('a@example.com', 'secret'))
  })

  it('shows the server message when credentials are wrong', async () => {
    login.mockImplementation(() =>
      Promise.reject(new ApiError(401, 'Invalid email or password.', 'unauthorized')),
    )
    renderPage()
    await userEvent.type(screen.getByLabelText(/email/i), 'a@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'nope')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  })
})
