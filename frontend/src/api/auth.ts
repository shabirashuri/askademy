import { request } from './client'

export type UserRole = 'admin' | 'teacher' | 'student'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
    skipAuthRedirect: true,
  })
}

export function getMe(): Promise<User> {
  return request<User>('/auth/me')
}
