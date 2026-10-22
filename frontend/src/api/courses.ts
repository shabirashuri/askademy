import type { User } from './auth'
import { request } from './client'

export interface Course {
  id: string
  code: string
  title: string
  description: string | null
  teacher_id: string
  created_at: string
}

export interface CourseInput {
  code: string
  title: string
  description?: string | null
  teacher_id?: string
}

export interface Topic {
  id: string
  course_id: string
  parent_topic_id: string | null
  title: string
  position: number
}

export const listCourses = () => request<Course[]>('/courses')
export const getCourse = (id: string) => request<Course>(`/courses/${id}`)
export const createCourse = (body: CourseInput) =>
  request<Course>('/courses', { method: 'POST', body })
export const updateCourse = (id: string, body: Partial<CourseInput>) =>
  request<Course>(`/courses/${id}`, { method: 'PATCH', body })
export const deleteCourse = (id: string) => request<void>(`/courses/${id}`, { method: 'DELETE' })

export const listTopics = (courseId: string) => request<Topic[]>(`/courses/${courseId}/topics`)
export const createTopic = (courseId: string, title: string, parentTopicId: string | null) =>
  request<Topic>(`/courses/${courseId}/topics`, {
    method: 'POST',
    body: { title, parent_topic_id: parentTopicId },
  })
export const renameTopic = (topicId: string, title: string) =>
  request<Topic>(`/topics/${topicId}`, { method: 'PATCH', body: { title } })
export const deleteTopic = (topicId: string) =>
  request<void>(`/topics/${topicId}`, { method: 'DELETE' })
export const reorderTopics = (courseId: string, items: { id: string; position: number }[]) =>
  request<Topic[]>(`/courses/${courseId}/topics/order`, { method: 'PUT', body: { items } })

export interface Enrollment {
  id: string
  course_id: string
  student_id: string
  enrolled_at: string
  student: User
}

export const listEnrollments = (courseId: string) =>
  request<Enrollment[]>(`/courses/${courseId}/enrollments`)
export const enrollStudent = (courseId: string, studentId: string) =>
  request<Enrollment>(`/courses/${courseId}/enrollments`, {
    method: 'POST',
    body: { student_id: studentId },
  })
export const unenrollStudent = (courseId: string, studentId: string) =>
  request<void>(`/courses/${courseId}/enrollments/${studentId}`, { method: 'DELETE' })
