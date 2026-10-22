import { request } from './client'
import type { User, UserRole } from './auth'

export interface UserInput {
  email: string
  full_name: string
  password: string
  role: UserRole
}

export const listUsers = (role?: UserRole) =>
  request<User[]>(`/users${role ? `?role=${role}` : ''}`)
export const createUser = (body: UserInput) => request<User>('/users', { method: 'POST', body })
export const updateUser = (
  id: string,
  body: { full_name?: string; password?: string; is_active?: boolean },
) => request<User>(`/users/${id}`, { method: 'PATCH', body })
