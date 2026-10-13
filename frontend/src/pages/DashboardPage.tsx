import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  CircleHelp,
  FileText,
  Layers3,
  Plus,
  Sparkles,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { getApiHealth } from '../api/client'
import { Sidebar } from '../components/Sidebar'

type ApiState = 'checking' | 'online' | 'offline'

const milestones = [
  {
    number: '01',
    title: 'Set up your course structure',
    detail: 'Create a course and organize it into topics.',
    icon: BookOpen,
    state: 'Start here',
  },
  {
    number: '02',
    title: 'Add your first learning material',
    detail: 'Upload a PDF, presentation, or document.',
    icon: FileText,
    state: 'Next step',
  },
  {
    number: '03',
    title: 'Build your question bank',
    detail: 'Generate with AI or write questions yourself.',
    icon: Layers3,
    state: 'Coming up',
  },
]

export function DashboardPage() {
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
            <span className="breadcrumb-divider">/</span>
            <strong>Overview</strong>
          </div>
          <div className="topbar-right">
            <div className={`api-status ${apiState}`} role="status">
              <span className="status-dot" />
              {apiState === 'checking'
                ? 'Connecting to API'
                : apiState === 'online'
                  ? 'System operational'
                  : 'API unavailable'}
            </div>
            <button className="help-button" aria-label="Help">
              <CircleHelp size={19} />
            </button>
          </div>
        </header>

        <div className="page-wrap">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">TUESDAY, OCTOBER 13</p>
              <h1>Good afternoon, Jordan <span>✳</span></h1>
              <p className="welcome-subtitle">
                Your teaching workspace is ready. Let’s build something useful.
              </p>
            </div>
            <button className="primary-button">
              <Plus size={17} />
              Create a course
            </button>
          </section>

          <section className="hero-card">
            <div className="hero-copy">
              <div className="hero-kicker">
                <Sparkles size={14} />
                YOUR TEACHING WORKSPACE
              </div>
              <h2>Turn what you teach<br />into better assessments.</h2>
              <p>
                Start with a course. Add your materials. Build a question bank
                that works as hard as you do.
              </p>
              <button className="hero-button">
                Set up your first course <ArrowRight size={16} />
              </button>
            </div>
            <div className="hero-art" aria-hidden="true">
              <div className="art-orbit orbit-one" />
              <div className="art-orbit orbit-two" />
              <div className="art-card art-card-back">
                <div className="art-lines"><i /><i /><i /></div>
              </div>
              <div className="art-card art-card-front">
                <span className="art-check"><Check size={17} /></span>
                <small>QUESTION 01</small>
                <div className="art-lines"><i /><i /></div>
                <span className="art-option"><b>A</b><i /></span>
                <span className="art-option selected"><b>B</b><i /></span>
                <span className="art-option"><b>C</b><i /></span>
              </div>
              <div className="art-sparkle">✳</div>
              <div className="art-orb" />
            </div>
          </section>

          <section className="stats-grid" aria-label="Workspace summary">
            <div className="stat-card">
              <div className="stat-icon sage"><BookOpen size={18} /></div>
              <div className="stat-copy"><span>COURSES</span><strong>—</strong><small>Get started by creating one</small></div>
              <ArrowUpRight className="stat-arrow" size={16} />
            </div>
            <div className="stat-card">
              <div className="stat-icon lavender"><Layers3 size={18} /></div>
              <div className="stat-copy"><span>BANK QUESTIONS</span><strong>—</strong><small>Build your reusable bank</small></div>
              <ArrowUpRight className="stat-arrow" size={16} />
            </div>
            <div className="stat-card">
              <div className="stat-icon peach"><FileText size={18} /></div>
              <div className="stat-copy"><span>ASSESSMENTS</span><strong>—</strong><small>Create your first quiz</small></div>
              <ArrowUpRight className="stat-arrow" size={16} />
            </div>
          </section>

          <section className="lower-grid">
            <div className="setup-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">YOUR FIRST STEPS</p>
                  <h3>Let’s get you set up</h3>
                </div>
                <span className="step-count">0 of 3 complete</span>
              </div>
              <div className="progress-track"><span /></div>
              <div className="milestone-list">
                {milestones.map(({ number, title, detail, icon: Icon, state }) => (
                  <article className="milestone" key={number}>
                    <div className="milestone-icon"><Icon size={17} /></div>
                    <div className="milestone-copy">
                      <div className="milestone-title-row"><h4>{title}</h4><span>{number}</span></div>
                      <p>{detail}</p>
                    </div>
                    <button className={number === '01' ? 'text-action' : 'icon-action'} aria-label={state}>
                      {number === '01' ? <>{state}<ArrowRight size={14} /></> : <ArrowRight size={16} />}
                    </button>
                  </article>
                ))}
              </div>
            </div>

            <aside className="side-panel">
              <div className="side-panel-header">
                <div>
                  <p className="eyebrow">A BETTER WAY TO PREP</p>
                  <h3>From material<br />to meaningful.</h3>
                </div>
                <span className="side-sparkle">✳</span>
              </div>
              <p className="side-description">
                Upload a lesson, let AI help draft questions, then shape them
                into an assessment that fits your class.
              </p>
              <div className="side-flow">
                <span>Course material</span><i /><span>Question bank</span><i /><span>Assessment</span>
              </div>
              <a className="learn-link" href="#">
                Explore how it works <ArrowRight size={15} />
              </a>
            </aside>
          </section>

          <footer className="page-footer">
            <span>Made for better learning.</span>
            <span>Smart Item Bank <span className="footer-dot">·</span> Prototype workspace</span>
          </footer>
        </div>
      </main>
    </div>
  )
}
