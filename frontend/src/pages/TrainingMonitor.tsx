import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { training } from '../services/api'

type JobStatus = {
  phase?: string
  progress?: number
  step?: string
  samples_loaded?: number
  train_size?: number
  val_size?: number
  test_size?: number
  feature_count?: number
  config?: Record<string, unknown>
  metrics?: Record<string, unknown>
  error?: string
}

export default function TrainingMonitor() {
  const { jobId } = useParams<{ jobId: string }>()
  const [status, setStatus] = useState<JobStatus | null>(null)

  useEffect(() => {
    if (!jobId) return
    const interval = setInterval(async () => {
      try {
        const { data } = await training.status(jobId)
        setStatus(data)
        if (data.phase === 'completed' || data.phase === 'failed') clearInterval(interval)
      } catch {
        clearInterval(interval)
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [jobId])

  if (!status) return <div>Loading...</div>

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Training Monitor</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>Job ID: {jobId}</p>
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
          <span>{status.phase || 'Running'}</span>
          <span>{status.progress ?? 0}%</span>
        </div>
        <div style={{ height: 8, background: 'var(--bg-primary)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ width: `${status.progress ?? 0}%`, height: '100%', background: 'var(--accent)', transition: 'width 0.3s' }} />
        </div>
      </div>
      {(status.samples_loaded != null || status.train_size != null || status.feature_count != null) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
          {status.samples_loaded != null && (
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Samples Loaded</div>
              <div style={{ fontWeight: 600 }}>{status.samples_loaded.toLocaleString()}</div>
            </div>
          )}
          {status.train_size != null && (
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Train Size</div>
              <div style={{ fontWeight: 600 }}>{status.train_size.toLocaleString()}</div>
            </div>
          )}
          {status.val_size != null && (
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Val Size</div>
              <div style={{ fontWeight: 600 }}>{status.val_size.toLocaleString()}</div>
            </div>
          )}
          {status.test_size != null && (
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Test Size</div>
              <div style={{ fontWeight: 600 }}>{status.test_size.toLocaleString()}</div>
            </div>
          )}
          {status.feature_count != null && (
            <div style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Features</div>
              <div style={{ fontWeight: 600 }}>{status.feature_count}</div>
            </div>
          )}
        </div>
      )}
      {status.config && Object.keys(status.config).length > 0 && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)' }}>
          <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem' }}>Config</h4>
          <pre style={{ margin: 0, fontSize: '0.8rem', overflow: 'auto' }}>{JSON.stringify(status.config, null, 2)}</pre>
        </div>
      )}
      {status.error && (
        <div style={{ padding: '1rem', background: 'rgba(248,113,113,0.2)', borderRadius: 4, color: 'var(--danger)', marginBottom: '1rem' }}>
          {status.error}
        </div>
      )}
      {status.metrics && (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3 style={{ margin: '0 0 1rem' }}>Results</h3>
          <pre style={{ margin: 0, fontSize: '0.85rem', overflow: 'auto' }}>
            {JSON.stringify(status.metrics, null, 2)}
          </pre>
        </div>
      )}
      <Link to="/training/config" style={{ display: 'inline-block', marginTop: '1rem', color: 'var(--accent)' }}>← Back to Config</Link>
    </div>
  )
}
