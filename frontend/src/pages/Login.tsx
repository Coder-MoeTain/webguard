import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { auth } from '../services/api'

export default function Login() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await auth.login(username, password)
      login(data.access_token)
      navigate('/')
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%)',
    }}>
      <div style={{
        width: 360,
        padding: 2,
        background: 'var(--bg-secondary)',
        borderRadius: 8,
        border: '1px solid var(--bg-card)',
      }}>
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <Shield size={48} style={{ color: 'var(--accent)' }} />
          <h1 style={{ margin: '0.5rem 0', fontSize: '1.5rem' }}>WebGuard RF</h1>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Web Attack Detection Platform
          </p>
        </div>
        <form onSubmit={handleSubmit} style={{ padding: '0 2rem 2rem' }}>
          {error && (
            <div style={{ padding: '0.5rem', background: 'rgba(248,113,113,0.2)', borderRadius: 4, marginBottom: '1rem', color: 'var(--danger)' }}>
              {error}
            </div>
          )}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Username</label>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                width: '100%',
                padding: '0.6rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--bg-card)',
                borderRadius: 4,
                color: 'var(--text)',
              }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Password</label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '0.6rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--bg-card)',
                borderRadius: 4,
                color: 'var(--text)',
              }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.75rem',
              background: 'var(--accent)',
              border: 'none',
              borderRadius: 4,
              color: 'var(--bg-primary)',
              fontWeight: 600,
            }}
          >
            Sign In
          </button>
        </form>
        <p style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Demo: admin / admin123
        </p>
      </div>
    </div>
  )
}
