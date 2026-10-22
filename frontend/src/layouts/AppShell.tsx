import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { getApiHealth } from '../api/client'
import { Sidebar } from '../components/Sidebar'

type ApiState = 'checking' | 'online' | 'offline'

const statusText: Record<ApiState, string> = {
  checking: 'Connecting to API',
  online: 'System operational',
  offline: 'API unavailable',
}

export function AppShell() {
  const [apiState, setApiState] = useState<ApiState>('checking')

  useEffect(() => {
    let active = true
    getApiHealth()
      .then(() => active && setApiState('online'))
      .catch(() => active && setApiState('offline'))
    return () => {
      active = false
    }
  }, [])

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Workspace</span>
          </div>
          <div className="topbar-right">
            <div className={`api-status ${apiState}`} role="status">
              <span className="status-dot" />
              {statusText[apiState]}
            </div>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  )
}
