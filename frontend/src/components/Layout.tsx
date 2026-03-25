import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Shield, Database, Cpu, BarChart3, TestTube, FileText, LogOut, FlaskConical, ShieldAlert } from 'lucide-react'
import { APP_NAME_SHORT, LOGO_ALT } from '../researchBranding'

const navItems = [
  { path: '/', label: 'Overview', icon: Shield },
  { path: '/datasets/generate', label: 'Synthetic dataset', icon: Database },
  { path: '/datasets/upload', label: 'Import dataset', icon: Database },
  { path: '/datasets/browse', label: 'Dataset browser', icon: Database },
  { path: '/features/extract', label: 'Feature extraction', icon: Cpu },
  { path: '/training/config', label: 'Train models', icon: Cpu },
  { path: '/evaluation', label: 'Metrics & confusion', icon: BarChart3 },
  { path: '/feature-importance', label: 'Feature importance', icon: BarChart3 },
  { path: '/robustness', label: 'Robustness & ablation', icon: TestTube },
  { path: '/inference', label: 'Scoring lab', icon: TestTube },
  { path: '/test-lab', label: 'Payload experiments', icon: FlaskConical },
  { path: '/ids', label: 'IDS demo (stream)', icon: ShieldAlert },
  { path: '/models', label: 'Saved models', icon: FileText },
  { path: '/reports', label: 'Report export', icon: FileText },
]

export default function Layout() {
  const location = useLocation()
  const { logout } = useAuth()

  const handleLogout = () => {
    logout()
    window.location.href = '/login'
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{
        width: 240,
        background: 'var(--bg-secondary)',
        padding: '1rem 0',
        borderRight: '1px solid var(--bg-card)',
      }}>
        <Link to="/" style={{ display: 'block', padding: '0 1rem 1rem', borderBottom: '1px solid var(--bg-card)', textDecoration: 'none', color: 'inherit' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <img src="/shield.svg" alt={LOGO_ALT} style={{ width: 36, height: 36 }} />
            <div>
              <h2 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--accent)' }}>{APP_NAME_SHORT}</h2>
            </div>
          </div>
        </Link>
        <nav style={{ padding: '1rem 0' }}>
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.6rem 1rem',
                color: location.pathname === path ? 'var(--accent)' : 'var(--text-muted)',
                background: location.pathname === path ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                borderLeft: location.pathname === path ? '3px solid var(--accent)' : '3px solid transparent',
                textDecoration: 'none',
              }}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div style={{ padding: '1rem', borderTop: '1px solid var(--bg-card)' }}>
          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              background: 'transparent',
              border: '1px solid var(--bg-card)',
              color: 'var(--text-muted)',
              borderRadius: 4,
            }}
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: '1.5rem', overflow: 'auto' }}>
        <Outlet />
      </main>
    </div>
  )
}
