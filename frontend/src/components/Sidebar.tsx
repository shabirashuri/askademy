import {
  BarChart3,
  BookOpen,
  Boxes,
  FileQuestion,
  LayoutDashboard,
  Search,
  Settings2,
} from 'lucide-react'

const navigation = [
  { label: 'Overview', icon: LayoutDashboard, active: true },
  { label: 'Courses & topics', icon: BookOpen },
  { label: 'Question bank', icon: Boxes },
  { label: 'Assessments', icon: FileQuestion },
  { label: 'Student insights', icon: BarChart3 },
]

export function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Smart Item Bank home">
        <span className="brand-mark">S</span>
        <span>
          <strong>smartbank</strong>
          <small>LEARNING PLATFORM</small>
        </span>
      </a>

      <div className="workspace-label">WORKSPACE</div>
      <nav className="navigation" aria-label="Main navigation">
        {navigation.map(({ label, icon: Icon, active }) => (
          <a
            className={`nav-item${active ? ' active' : ''}`}
            href="#"
            key={label}
            aria-current={active ? 'page' : undefined}
          >
            <Icon size={18} strokeWidth={1.8} />
            <span>{label}</span>
            {label === 'Question bank' && <span className="nav-count">—</span>}
          </a>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <a className="nav-item" href="#">
          <Search size={18} strokeWidth={1.8} />
          <span>Search</span>
          <span className="shortcut">⌘ K</span>
        </a>
        <a className="nav-item" href="#">
          <Settings2 size={18} strokeWidth={1.8} />
          <span>Settings</span>
        </a>
        <div className="profile">
          <div className="avatar">JD</div>
          <div className="profile-copy">
            <strong>Jordan Davis</strong>
            <span>Teacher account</span>
          </div>
          <span className="profile-menu">···</span>
        </div>
      </div>
    </aside>
  )
}
