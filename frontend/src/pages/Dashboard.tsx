import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Database, Cpu, BarChart3, TestTube, Activity, TrendingUp, FlaskConical, ShieldAlert, Trash2 } from 'lucide-react'
import { training, datasets, models } from '../services/api'

const cards = [
  { title: 'Dataset Generation', desc: 'Generate 5M samples', to: '/datasets/generate', icon: Database },
  { title: 'Feature Extraction', desc: 'Extract security features', to: '/features/extract', icon: Cpu },
  { title: 'Training', desc: 'Train Random Forest', to: '/training/config', icon: Cpu },
  { title: 'Evaluation', desc: 'View metrics & confusion matrix', to: '/evaluation', icon: BarChart3 },
  { title: 'Inference', desc: 'Test live payloads', to: '/inference', icon: TestTube },
  { title: 'Vulnerability Test Lab', desc: 'Test SQLi, XSS, CSRF detection', to: '/test-lab', icon: FlaskConical },
  { title: 'Real-time IDS', desc: 'Live intrusion detection dashboard', to: '/ids', icon: ShieldAlert },
]

interface Job {
  job_id: string
  phase?: string
  progress?: number
  metrics?: { test?: { accuracy?: number }; model_id?: string }
}

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [resetting, setResetting] = useState(false)
  const [resetSuccess, setResetSuccess] = useState<string | null>(null)

  const handleReset = async () => {
    if (!window.confirm('Delete all datasets and models? This cannot be undone.')) return
    setResetting(true)
    setResetSuccess(null)
    try {
      const [dsRes, mdRes] = await Promise.all([datasets.reset(), models.reset()])
      const dsCount = dsRes.data?.count ?? 0
      const mdCount = mdRes.data?.count ?? 0
      setResetSuccess(`Deleted ${dsCount} dataset(s) and ${mdCount} model(s).`)
      setJobs([])
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : String(err)
      setResetSuccess(`Error: ${msg}`)
    } finally {
      setResetting(false)
    }
  }

  useEffect(() => {
    const fetch = () => {
      training.list()
        .then(({ data }) => setJobs(data.jobs || []))
        .catch(() => setJobs([]))
    }
    fetch()
    const interval = setInterval(fetch, 5000)
    return () => clearInterval(interval)
  }, [])

  const runningJobs = jobs.filter((j) => j.phase === 'running' || j.phase === 'starting' || j.phase === 'queued')
  const completedJobs = jobs.filter((j) => j.phase === 'completed')
  const accuracies = completedJobs.map((j) => j.metrics?.test?.accuracy).filter((a): a is number => a != null)
  const bestAccuracy = accuracies.length ? Math.max(...accuracies) : undefined
  const latestAccuracy = completedJobs.length > 0 ? completedJobs[0].metrics?.test?.accuracy : undefined
  const displayAccuracy = latestAccuracy ?? bestAccuracy

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <img src="/shield.svg" alt="WebGuard RF" style={{ width: 56, height: 56 }} />
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)', margin: '0.25rem 0 0' }}>
            Machine Learning driven detection of SQLi, XSS, and CSRF
          </p>
        </div>
      </div>

      {/* Training Status & Model Accuracy Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Activity size={24} style={{ color: 'var(--accent)' }} />
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Training Status</h3>
          </div>
          {runningJobs.length > 0 ? (
            <div>
              <p style={{ margin: '0 0 0.5rem', fontSize: '0.9rem' }}>{runningJobs.length} job(s) running</p>
              {runningJobs.slice(0, 3).map((j) => (
                <Link key={j.job_id} to={`/training/monitor/${j.job_id}`} style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--accent)', fontSize: '0.85rem' }}>
                  {j.job_id} — {j.progress ?? 0}%
                </Link>
              ))}
            </div>
          ) : (
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>No active training</p>
          )}
          <Link to="/training/config" style={{ fontSize: '0.85rem', color: 'var(--accent)', marginTop: '0.5rem', display: 'inline-block' }}>Start training →</Link>
        </div>

        <div style={{ padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <TrendingUp size={24} style={{ color: 'var(--accent)' }} />
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Model Accuracy</h3>
          </div>
          {displayAccuracy !== undefined ? (
            <p style={{ margin: 0, fontSize: '2rem', fontWeight: 700, color: 'var(--success)' }}>
              {(displayAccuracy * 100).toFixed(2)}%
            </p>
          ) : (
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>No trained model yet</p>
          )}
          <Link to="/evaluation" style={{ fontSize: '0.85rem', color: 'var(--accent)', marginTop: '0.5rem', display: 'inline-block' }}>View metrics →</Link>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
        {cards.map(({ title, desc, to, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            style={{
              padding: '1.5rem',
              background: 'var(--bg-secondary)',
              borderRadius: 8,
              border: '1px solid var(--bg-card)',
              textDecoration: 'none',
              color: 'inherit',
              transition: 'border-color 0.2s',
            }}
          >
            <Icon size={32} style={{ color: 'var(--accent)', marginBottom: '0.5rem' }} />
            <h3 style={{ margin: '0 0 0.25rem', fontSize: '1rem' }}>{title}</h3>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>{desc}</p>
          </Link>
        ))}
      </div>

      {/* Recent Jobs Table */}
      {jobs.length > 0 && (
        <div style={{ marginTop: '2rem', padding: '1.5rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3 style={{ margin: '0 0 1rem' }}>Recent Training Jobs</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--bg-card)' }}>
                  <th style={{ textAlign: 'left', padding: '0.5rem', fontSize: '0.85rem' }}>Job ID</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem', fontSize: '0.85rem' }}>Status</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem', fontSize: '0.85rem' }}>Accuracy</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem', fontSize: '0.85rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {jobs.slice(0, 5).map((j) => (
                  <tr key={j.job_id} style={{ borderBottom: '1px solid var(--bg-card)' }}>
                    <td style={{ padding: '0.5rem', fontSize: '0.9rem' }}>{j.job_id}</td>
                    <td style={{ padding: '0.5rem', fontSize: '0.9rem' }}>
                      <span style={{
                        color: j.phase === 'completed' ? 'var(--success)' : j.phase === 'failed' ? 'var(--danger)' : 'var(--accent)',
                      }}>
                        {j.phase || '-'}
                      </span>
                      {j.progress !== undefined && j.phase !== 'completed' && j.phase !== 'failed' && (
                        <span style={{ marginLeft: '0.5rem', color: 'var(--text-muted)' }}>({j.progress}%)</span>
                      )}
                    </td>
                    <td style={{ padding: '0.5rem', fontSize: '0.9rem' }}>
                      {j.metrics?.test?.accuracy != null ? `${(j.metrics.test.accuracy * 100).toFixed(2)}%` : '-'}
                    </td>
                    <td style={{ padding: '0.5rem' }}>
                      <Link to={`/training/monitor/${j.job_id}`} style={{ fontSize: '0.85rem', color: 'var(--accent)' }}>View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        <h3 style={{ margin: '0 0 0.5rem' }}>Quick Start</h3>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-muted)' }}>
          <li>Generate or upload a dataset (5M samples recommended)</li>
          <li>Extract features (payload-only or hybrid)</li>
          <li>Configure and start training</li>
          <li>Evaluate metrics and test live payloads</li>
        </ol>
        <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={handleReset}
            disabled={resetting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              background: 'rgba(248,113,113,0.2)',
              border: '1px solid var(--danger)',
              color: 'var(--danger)',
              borderRadius: 4,
              cursor: resetting ? 'not-allowed' : 'pointer',
            }}
          >
            <Trash2 size={18} />
            {resetting ? 'Resetting...' : 'Reset All (datasets & models)'}
          </button>
          {resetSuccess && (
            <span style={{ fontSize: '0.9rem', color: resetSuccess.startsWith('Error') ? 'var(--danger)' : 'var(--success)' }}>
              {resetSuccess}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
