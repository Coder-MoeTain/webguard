import { useState, useEffect } from 'react'
import { datasets } from '../services/api'

export default function DatasetGeneration() {
  const [total, setTotal] = useState(5_000_000)
  const [attackRatio, setAttackRatio] = useState(0.8)
  const [format, setFormat] = useState('parquet')
  const [seed, setSeed] = useState(42)
  const [labelNoise, setLabelNoise] = useState(0.04)
  const [result, setResult] = useState<{ job_id?: string; message?: string } | null>(null)
  const [status, setStatus] = useState<{ phase: string; progress: number; written?: number; total?: number; output_path?: string; error?: string } | null>(null)

  const jobId = result?.job_id
  const isRunning = status?.phase === 'running' || status?.phase === 'starting'

  useEffect(() => {
    if (!jobId) return
    let cancelled = false
    const poll = async () => {
      if (cancelled) return true
      try {
        const { data } = await datasets.generationStatus(jobId)
        if (cancelled) return true
        setStatus(data)
        return data.phase === 'completed' || data.phase === 'failed'
      } catch {
        return true
      }
    }
    poll()
    const interval = setInterval(async () => {
      const done = await poll()
      if (done) clearInterval(interval)
    }, 1500)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [jobId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    setStatus(null)
    try {
      const { data } = await datasets.generate({
        total_samples: total,
        attack_ratio: attackRatio,
        output_format: format,
        random_seed: seed,
        label_noise_ratio: labelNoise,
      })
      setResult(data)
      setStatus({ phase: 'starting', progress: 0 })
    } catch (err) {
      setResult({ message: 'Failed to start generation' })
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Dataset Generation</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Generate up to 5 million samples with 80% attack and 20% benign traffic.
      </p>
      <div style={{ maxWidth: 500, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Total Samples</label>
            <input
              type="number"
              value={total}
              onChange={(e) => setTotal(Number(e.target.value))}
              min={1000}
              max={10_000_000}
              step={100000}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Attack Ratio (0-1)</label>
            <input
              type="number"
              value={attackRatio}
              onChange={(e) => setAttackRatio(Number(e.target.value))}
              min={0}
              max={1}
              step={0.1}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Output Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              <option value="parquet">Parquet</option>
              <option value="csv">CSV</option>
            </select>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Random Seed</label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Label Noise Ratio (0–1)</label>
            <input
              type="number"
              value={labelNoise}
              onChange={(e) => setLabelNoise(Number(e.target.value))}
              min={0}
              max={0.2}
              step={0.01}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            />
          </div>
          <button type="submit" disabled={isRunning} style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600, cursor: isRunning ? 'not-allowed' : 'pointer' }}>
            {isRunning ? 'Generating...' : 'Start Generation'}
          </button>
        </form>
        {result && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-primary)', borderRadius: 4 }}>
            {result.job_id && <p style={{ margin: 0 }}>Job ID: {result.job_id}</p>}
            {result.message && <p style={{ margin: '0.25rem 0 0', color: 'var(--text-muted)' }}>{result.message}</p>}
            {status && (
              <div style={{ marginTop: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  <span>{status.phase === 'completed' ? 'Completed' : status.phase === 'failed' ? 'Failed' : 'Generating'}</span>
                  {status.written != null && status.total != null && (
                    <span>{status.written.toLocaleString()} / {status.total.toLocaleString()} samples</span>
                  )}
                </div>
                <div style={{ height: 8, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${status.progress ?? 0}%`,
                      background: status.phase === 'completed' ? 'var(--success)' : status.phase === 'failed' ? 'var(--danger)' : 'var(--accent)',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
                {status.phase === 'failed' && status.error && (
                  <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--danger)' }}>{status.error}</p>
                )}
                {status.phase === 'completed' && status.output_path && (
                  <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--success)' }}>Output: {status.output_path}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
