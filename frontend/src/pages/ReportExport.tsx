import { useState, useEffect } from 'react'
import { reports, training } from '../services/api'

export default function ReportExport() {
  const [jobs, setJobs] = useState<{ job_id: string; phase?: string }[]>([])
  const [jobId, setJobId] = useState('')
  const [format, setFormat] = useState<'html' | 'markdown'>('html')
  const [result, setResult] = useState<{ path?: string; preview_url?: string } | null>(null)

  useEffect(() => {
    training.list().then(({ data }) => setJobs((data.jobs || []).filter((j: { phase?: string }) => j.phase === 'completed'))).catch(() => {})
  }, [])

  const handleExport = async () => {
    if (!jobId) return
    setResult(null)
    try {
      const { data } = await reports.export(jobId, format)
      setResult(data)
    } catch {
      setResult({ path: 'Export failed' })
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Report Export</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Export experiment reports in HTML or Markdown.
      </p>
      <div style={{ maxWidth: 500, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem' }}>Job</label>
          <select
            value={jobId}
            onChange={(e) => setJobId(e.target.value)}
            style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
          >
            <option value="">Select completed job...</option>
            {jobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>{j.job_id}</option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.25rem' }}>Format</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value as 'html' | 'markdown')}
            style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
          >
            <option value="html">HTML</option>
            <option value="markdown">Markdown</option>
          </select>
        </div>
        <button onClick={handleExport} disabled={!jobId} style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600 }}>
          Export
        </button>
        {result?.preview_url && (
          <a href={result.preview_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', marginLeft: '1rem', color: 'var(--accent)' }}>
            Preview HTML
          </a>
        )}
        {result?.path && <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Saved: {result.path}</p>}
      </div>
    </div>
  )
}
