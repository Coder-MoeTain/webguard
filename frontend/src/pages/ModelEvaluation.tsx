import { useState, useEffect } from 'react'
import { training } from '../services/api'

export default function ModelEvaluation() {
  const [jobs, setJobs] = useState<{ job_id: string; phase?: string }[]>([])
  const [jobId, setJobId] = useState('')
  const [metrics, setMetrics] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    training.list().then(({ data }) => setJobs(data.jobs || [])).catch(() => {})
  }, [])

  const fetchStatus = async () => {
    if (!jobId) return
    try {
      const { data } = await training.status(jobId)
      if (data.metrics) setMetrics(data.metrics as Record<string, unknown>)
    } catch {}
  }

  const completedJobs = jobs.filter((j) => j.phase === 'completed')

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Model Evaluation</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        View metrics from completed training jobs.
      </p>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <select
          value={jobId}
          onChange={(e) => setJobId(e.target.value)}
          style={{ padding: '0.6rem', minWidth: 200, background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
        >
          <option value="">Select job...</option>
          {completedJobs.map((j) => (
            <option key={j.job_id} value={j.job_id}>{j.job_id}</option>
          ))}
        </select>
        <button onClick={fetchStatus} disabled={!jobId} style={{ padding: '0.6rem 1rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)' }}>
          Load
        </button>
      </div>
      {metrics && (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3>Test Metrics</h3>
          {metrics.test && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '1rem' }}>
              {Object.entries(metrics.test as Record<string, number>).filter(([k]) => !['confusion_matrix', 'per_class_metrics'].includes(k)).map(([k, v]) => (
                <div key={k} style={{ padding: '1rem', background: 'var(--bg-primary)', borderRadius: 4 }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{k}</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{typeof v === 'number' ? v.toFixed(4) : String(v)}</div>
                </div>
              ))}
            </div>
          )}
          <pre style={{ marginTop: '1rem', fontSize: '0.85rem', overflow: 'auto' }}>{JSON.stringify(metrics, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
