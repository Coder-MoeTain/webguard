import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Shield, Database, Cpu, BarChart3, TestTube, FileText, LogOut, FlaskConical, ShieldAlert } from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: Shield },
  { path: '/datasets/generate', label: 'Dataset Generation', icon: Database },
  { path: '/datasets/upload', label: 'Dataset Upload', icon: Database },
  { path: '/datasets/browse', label: 'Dataset Browser', icon: Database },
  { path: '/features/extract', label: 'Feature Extraction', icon: Cpu },
  { path: '/training/config', label: 'Training Config', icon: Cpu },
  { path: '/evaluation', label: 'Model Evaluation', icon: BarChart3 },
  { path: '/feature-importance', label: 'Feature Importance', icon: BarChart3 },
  { path: '/robustness', label: 'Robustness Analysis', icon: TestTube },
  { path: '/inference', label: 'Inference Testing', icon: TestTube },
  { path: '/test-lab', label: 'Vulnerability Test Lab', icon: FlaskConical },
  { path: '/ids', label: 'Real-time IDS', icon: ShieldAlert },
  { path: '/models', label: 'Model Management', icon: FileText },
  { path: '/reports', label: 'Report Export', icon: FileText },
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
        <div style={{ padding: '0 1rem 1rem', borderBottom: '1px solid var(--bg-card)' }}>
          <h2 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--accent)' }}>WebGuard RF</h2>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Attack Detection
          </p>
        </div>
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
