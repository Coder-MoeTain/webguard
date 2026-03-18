import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { features, datasets } from '../services/api'

export default function FeatureExtraction() {
  const [datasetList, setDatasetList] = useState<{ path: string; name: string }[]>([])
  const [inputPath, setInputPath] = useState('data/sample_dataset.parquet')
  const [featureMode, setFeatureMode] = useState<'payload_only' | 'response_only' | 'hybrid' | 'sqli_37'>('payload_only')
  const [result, setResult] = useState<{ job_id?: string; output_path?: string } | null>(null)

  useEffect(() => {
    datasets.list().then(({ data }) => setDatasetList(data.datasets || [])).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    try {
      const { data } = await features.extract({ input_path: inputPath, feature_mode: featureMode })
      setResult(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setResult({ output_path: msg || 'Extraction failed' })
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Feature Extraction</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Extract lexical, structural, behavioral, and contextual features.
      </p>
      <div style={{ maxWidth: 500, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        {!datasetList.length && (
          <p style={{ padding: '0.75rem', background: 'rgba(251,191,36,0.2)', borderRadius: 4, marginBottom: '1rem', color: 'var(--warning)', fontSize: '0.9rem' }}>
            No datasets yet. <Link to="/datasets/browse" style={{ color: 'var(--accent)' }}>Generate or upload</Link> a dataset first.
          </p>
        )}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Input Dataset</label>
            <select
              value={inputPath}
              onChange={(e) => setInputPath(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              {datasetList.length ? datasetList.map((d) => (
                <option key={d.path} value={d.path}>{d.name}</option>
              )) : <option value={inputPath}>{inputPath}</option>}
            </select>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Feature Mode</label>
            <select
              value={featureMode}
              onChange={(e) => setFeatureMode(e.target.value as 'payload_only' | 'response_only' | 'hybrid' | 'sqli_37')}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              <option value="payload_only">Payload Only</option>
              <option value="response_only">Response Only</option>
              <option value="hybrid">Hybrid</option>
              <option value="sqli_37">SQLi 37 Features</option>
            </select>
          </div>
          <button type="submit" style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600 }}>
            Extract Features
          </button>
        </form>
        {result && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: result.job_id ? 'var(--bg-primary)' : 'rgba(248,113,113,0.2)', borderRadius: 4, color: result.job_id ? undefined : 'var(--danger)' }}>
            {result.job_id && <p style={{ margin: 0 }}>Job ID: {result.job_id}</p>}
            {result.output_path && <p style={{ margin: '0.25rem 0 0' }}>{result.job_id ? 'Output: ' : ''}{result.output_path}</p>}
          </div>
        )}
      </div>
    </div>
  )
}
