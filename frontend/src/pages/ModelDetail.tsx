import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { models } from '../services/api'

type ModelDetailData = {
  id: string
  classification_mode: string
  feature_mode: string
  algorithm_label?: string | null
  feature_count: number
  feature_importance: Record<string, number>
  top_features: { name: string; importance: number }[]
  label_map: Record<string, number>
  n_estimators?: number
  max_depth?: number
}

export default function ModelDetail() {
  const { modelId } = useParams<{ modelId: string }>()
  const navigate = useNavigate()
  const [detail, setDetail] = useState<ModelDetailData | null>(null)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (!modelId) return
    models.detail(modelId)
      .then(({ data }) => setDetail(data))
      .catch(() => setError('Model not found'))
  }, [modelId])

  if (error) return <div><p style={{ color: 'var(--danger)' }}>{error}</p><Link to="/models" style={{ color: 'var(--accent)' }}>← Back</Link></div>
  if (!detail) return <div>Loading...</div>

  const maxImp = Math.max(...Object.values(detail.feature_importance), 0.001)

  const handleDelete = async () => {
    if (!detail) return
    const label = detail.algorithm_label || detail.id
    const ok = window.confirm(`Delete model "${label}"?\n\n${detail.id}`)
    if (!ok) return
    try {
      setDeleting(true)
      await models.delete(detail.id)
      navigate('/models')
    } catch {
      setError('Delete failed')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Model Detail</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
        {detail.algorithm_label ? `Algorithm: ${detail.algorithm_label} ` : null}
        Model ID: {detail.id}
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Classification Mode</div>
          <div style={{ fontWeight: 600 }}>{detail.classification_mode}</div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Feature Mode</div>
          <div style={{ fontWeight: 600 }}>{detail.feature_mode}</div>
        </div>
        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Feature Count</div>
          <div style={{ fontWeight: 600 }}>{detail.feature_count}</div>
        </div>
        {detail.n_estimators != null && (
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>n_estimators</div>
            <div style={{ fontWeight: 600 }}>{detail.n_estimators}</div>
          </div>
        )}
        {detail.max_depth != null && (
          <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>max_depth</div>
            <div style={{ fontWeight: 600 }}>{detail.max_depth}</div>
          </div>
        )}
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem' }}>Label Map</h3>
        <pre style={{ margin: 0, padding: '1rem', background: 'var(--bg-secondary)', borderRadius: 6, border: '1px solid var(--bg-card)', overflow: 'auto' }}>
          {JSON.stringify(detail.label_map, null, 2)}
        </pre>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem' }}>Feature Importance</h3>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          {detail.top_features.map(({ name, importance }) => (
            <div key={name} style={{ marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                <span>{name}</span>
                <span style={{ color: 'var(--text-muted)' }}>{(importance * 100).toFixed(2)}%</span>
              </div>
              <div style={{ height: 6, background: 'var(--bg-primary)', borderRadius: 3, overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${(importance / maxImp) * 100}%`,
                    height: '100%',
                    background: 'var(--accent)',
                    transition: 'width 0.3s',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem' }}>
        <Link to="/models" style={{ color: 'var(--accent)' }}>← Back to Models</Link>
        <a href={`/api/models/${detail.id}/download`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
          Download Model
        </a>
        <button
          type="button"
          onClick={handleDelete}
          disabled={deleting}
          style={{
            padding: '0.5rem 1rem',
            background: deleting ? 'var(--bg-card)' : 'var(--danger)',
            border: 'none',
            borderRadius: 4,
            color: 'white',
            cursor: deleting ? 'not-allowed' : 'pointer',
            fontWeight: 600,
            marginLeft: 'auto',
          }}
        >
          {deleting ? 'Deleting...' : 'Delete Model'}
        </button>
      </div>
    </div>
  )
}
