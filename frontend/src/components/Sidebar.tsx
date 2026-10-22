import { BookOpen, GraduationCap, LayoutDashboard, Users, LogOut, type LucideIcon } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import type { UserRole } from '../api/auth'
import { useAuth } from '../auth/AuthContext'

interface NavItem {
  label: string
  to: string
  icon: LucideIcon
  roles: UserRole[]
}

const navigation: NavItem[] = [
  { label: 'Overview', to: '/', icon: LayoutDashboard, roles: ['admin', 'teacher', 'student'] },
  { label: 'Courses', to: '/courses', icon: BookOpen, roles: ['admin', 'teacher', 'student'] },
  { label: 'Students', to: '/students', icon: GraduationCap, roles: ['teacher'] },
  { label: 'Users', to: '/admin/users', icon: Users, roles: ['admin'] },
]

const roleLabel: Record<UserRole, string> = {
  admin: 'Administrator',
  teacher: 'Teacher account',
  student: 'Student account',
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

export function Sidebar() {
  const { user, logout } = useAuth()
  if (!user) return null

  return (
    <aside className="sidebar">
      <NavLink className="brand" to="/" aria-label="Smart Item Bank home">
        <span className="brand-mark">S</span>
        <span>
          <strong>smartbank</strong>
          <small>LEARNING PLATFORM</small>
        </span>
      </NavLink>

      <div className="workspace-label">WORKSPACE</div>
      <nav className="navigation" aria-label="Main navigation">
        {navigation
          .filter((item) => item.roles.includes(user.role))
          .map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="profile">
          <div className="avatar">{initials(user.full_name)}</div>
          <div className="profile-copy">
            <strong>{user.full_name}</strong>
            <span>{roleLabel[user.role]}</span>
          </div>
          <button className="icon-button" onClick={logout} aria-label="Log out" title="Log out">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  )
}
