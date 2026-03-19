import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { training, datasets } from '../services/api'

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
  metrics?: { test?: { accuracy?: number }; train?: unknown; validation?: unknown }
  error?: string
}

type ConfigState = {
  data_path: string
  classification_mode: 'binary' | 'multiclass'
  feature_mode: 'payload_only' | 'response_only' | 'hybrid' | 'sqli_37'
  train_ratio: number
  val_ratio: number
  test_ratio: number
  n_estimators: number
  max_depth: number
  min_samples_split: number
  min_samples_leaf: number
  max_features: string
  random_state: number
  hyperparameter_tuning: boolean
}

const PRESETS: { name: string; label: string; config: Partial<ConfigState> }[] = [
  { name: 'minimal', label: 'Minimal (lowest)', config: { n_estimators: 50, max_depth: 8, hyperparameter_tuning: false } },
  { name: 'small', label: 'Small', config: { n_estimators: 100, max_depth: 12, hyperparameter_tuning: false } },
  { name: 'medium', label: 'Medium', config: { n_estimators: 200, max_depth: 20, hyperparameter_tuning: false } },
  { name: 'large', label: 'Large', config: { n_estimators: 350, max_depth: 30, hyperparameter_tuning: false } },
  { name: 'maximum', label: 'Maximum (highest)', config: { n_estimators: 500, max_depth: 40, hyperparameter_tuning: true } },
]

export default function TrainingConfig() {
  const [datasetList, setDatasetList] = useState<{ path: string; name: string }[]>([])
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [config, setConfig] = useState<ConfigState>({
    data_path: 'data/sample_features.parquet',
    classification_mode: 'multiclass' as 'binary' | 'multiclass',
    feature_mode: 'payload_only' as 'payload_only' | 'response_only' | 'hybrid' | 'sqli_37',
    train_ratio: 0.7,
    val_ratio: 0.15,
    test_ratio: 0.15,
    n_estimators: 200,
    max_depth: 20,
    min_samples_split: 2,
    min_samples_leaf: 1,
    max_features: 'sqrt',
    random_state: 42,
    hyperparameter_tuning: false,
  })
  const [activePreset, setActivePreset] = useState<string | null>('medium')
  const [error, setError] = useState('')

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setConfig((c) => ({ ...c, ...preset.config }))
    setActivePreset(preset.name)
  }

  useEffect(() => {
    datasets.list().then(({ data }) => setDatasetList(data.datasets || [])).catch(() => {})
  }, [])

  const isRunning = status?.phase === 'running' || status?.phase === 'starting' || status?.phase === 'queued'

  useEffect(() => {
    if (!activeJobId) return
    const poll = async () => {
      try {
        const { data } = await training.status(activeJobId)
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
    }, 2000)
    return () => clearInterval(interval)
  }, [activeJobId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setActiveJobId(null)
    setStatus(null)
    try {
      const { data } = await training.start(config)
      setActiveJobId(data.job_id)
      setStatus({ phase: 'starting', progress: 0 })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Failed to start training')
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Training Configuration</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Configure Random Forest parameters and start training.
      </p>
      <div style={{ maxWidth: 600, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        {error && <div style={{ padding: '0.5rem', background: 'rgba(248,113,113,0.2)', borderRadius: 4, marginBottom: '1rem', color: 'var(--danger)' }}>{error}</div>}
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Resource presets (low → high)</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {PRESETS.map((p) => (
              <button
                key={p.name}
                type="button"
                onClick={() => applyPreset(p)}
                style={{
                  padding: '0.5rem 0.75rem',
                  background: activePreset === p.name ? 'var(--accent)' : 'var(--bg-primary)',
                  color: activePreset === p.name ? 'var(--bg-primary)' : 'var(--text)',
                  border: '1px solid var(--bg-card)',
                  borderRadius: 4,
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Dataset</label>
              <select
                value={config.data_path}
                onChange={(e) => setConfig({ ...config, data_path: e.target.value })}
                style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
              >
                {datasetList.length ? datasetList.map((d) => (
                  <option key={d.path} value={d.path}>{d.name}</option>
                )) : <option value={config.data_path}>{config.data_path}</option>}
              </select>
              {!datasetList.length && (
                <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  No datasets yet. <Link to="/datasets/browse" style={{ color: 'var(--accent)' }}>Generate or upload</Link> a dataset first.
                </p>
              )}
              <p style={{ margin: '0.25rem 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Use a feature-extracted dataset for best results. <Link to="/features/extract" style={{ color: 'var(--accent)' }}>Extract features</Link> from raw data first.
              </p>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Classification Mode</label>
              <select
                value={config.classification_mode}
                onChange={(e) => setConfig({ ...config, classification_mode: e.target.value as 'binary' | 'multiclass' })}
                style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
              >
                <option value="multiclass">Multi-class (SQLi, XSS, CSRF, Benign)</option>
                <option value="binary">Binary (Attack vs Benign)</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Feature Mode</label>
              <select
                value={config.feature_mode}
                onChange={(e) => setConfig({ ...config, feature_mode: e.target.value as 'payload_only' | 'response_only' | 'hybrid' | 'sqli_37' })}
                style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
              >
                <option value="payload_only">Payload Only</option>
                <option value="response_only">Response Only</option>
                <option value="hybrid">Hybrid</option>
                <option value="sqli_37">SQLi 37 Features</option>
              </select>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Train Ratio</label>
              <input type="number" value={config.train_ratio} onChange={(e) => setConfig({ ...config, train_ratio: Number(e.target.value) })} min={0.5} max={0.9} step={0.05} style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Val Ratio</label>
              <input type="number" value={config.val_ratio} onChange={(e) => setConfig({ ...config, val_ratio: Number(e.target.value) })} min={0.05} max={0.3} step={0.05} style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Test Ratio</label>
              <input type="number" value={config.test_ratio} onChange={(e) => setConfig({ ...config, test_ratio: Number(e.target.value) })} min={0.05} max={0.3} step={0.05} style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }} />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>n_estimators</label>
              <input type="number" value={config.n_estimators} onChange={(e) => { setConfig({ ...config, n_estimators: Number(e.target.value) }); setActivePreset(null) }} min={10} max={500} style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>max_depth</label>
              <input type="number" value={config.max_depth} onChange={(e) => { setConfig({ ...config, max_depth: Number(e.target.value) || undefined }); setActivePreset(null) }} min={5} max={100} placeholder="None" style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }} />
            </div>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input type="checkbox" checked={config.hyperparameter_tuning} onChange={(e) => { setConfig({ ...config, hyperparameter_tuning: e.target.checked }); setActivePreset(null) }} />
              Hyperparameter Tuning (RandomizedSearchCV)
            </label>
          </div>
          <button type="submit" disabled={isRunning} style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600, cursor: isRunning ? 'not-allowed' : 'pointer' }}>
            {isRunning ? 'Training...' : 'Start Training'}
          </button>
        </form>

        {activeJobId && status && (
          <div style={{ marginTop: '1.5rem', padding: '1.5rem', background: 'var(--bg-primary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Training Progress</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{status.step || status.phase || 'Running'}</span>
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{status.progress ?? 0}%</span>
            </div>
            <div style={{ height: 10, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden', marginBottom: '1rem' }}>
              <div
                style={{
                  height: '100%',
                  width: `${status.progress ?? 0}%`,
                  background: status.phase === 'completed' ? 'var(--success)' : status.phase === 'failed' ? 'var(--danger)' : 'var(--accent)',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
            {(status.samples_loaded != null || status.train_size != null || status.feature_count != null) && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '0.75rem', marginBottom: '1rem' }}>
                {status.samples_loaded != null && (
                  <div style={{ padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: 4, fontSize: '0.85rem' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Samples</div>
                    <div style={{ fontWeight: 600 }}>{status.samples_loaded.toLocaleString()}</div>
                  </div>
                )}
                {status.train_size != null && (
                  <div style={{ padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: 4, fontSize: '0.85rem' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Train</div>
                    <div style={{ fontWeight: 600 }}>{status.train_size.toLocaleString()}</div>
                  </div>
                )}
                {status.val_size != null && (
                  <div style={{ padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: 4, fontSize: '0.85rem' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Val</div>
                    <div style={{ fontWeight: 600 }}>{status.val_size.toLocaleString()}</div>
                  </div>
                )}
                {status.test_size != null && (
                  <div style={{ padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: 4, fontSize: '0.85rem' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Test</div>
                    <div style={{ fontWeight: 600 }}>{status.test_size.toLocaleString()}</div>
                  </div>
                )}
                {status.feature_count != null && (
                  <div style={{ padding: '0.5rem', background: 'var(--bg-secondary)', borderRadius: 4, fontSize: '0.85rem' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Features</div>
                    <div style={{ fontWeight: 600 }}>{status.feature_count}</div>
                  </div>
                )}
              </div>
            )}
            {status.error && (
              <div style={{ padding: '0.75rem', background: 'rgba(248,113,113,0.2)', borderRadius: 4, color: 'var(--danger)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                {status.error}
              </div>
            )}
            {status.phase === 'completed' && status.metrics?.test?.accuracy != null && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: 'var(--success)' }}>
                Training complete. Test accuracy: {(status.metrics.test.accuracy * 100).toFixed(2)}%
              </div>
            )}
            <Link to={`/training/monitor/${activeJobId}`} style={{ display: 'inline-block', marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--accent)' }}>
              View full monitor →
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
