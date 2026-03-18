import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { inference, models } from '../services/api'

export default function InferenceTesting() {
  const [modelList, setModelList] = useState<{ id: string }[]>([])
  const [modelId, setModelId] = useState<string | null>(null)
  const [payload, setPayload] = useState("' OR 1=1--")
  const [result, setResult] = useState<{ prediction?: string; confidence?: number; top_features?: { name: string; importance: number }[]; risk_explanation?: string } | null>(null)

  useEffect(() => {
    models.list().then(({ data }) => {
      const list = data.models || []
      setModelList(list)
      if (list.length) setModelId((prev) => prev || list[0].id)
    }).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setResult(null)
    try {
      const { data } = await inference.predict({
        body: payload,
        query_params: payload,
        request_method: 'GET',
        model_id: modelId || undefined,
      })
      setResult(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setResult({ prediction: 'Error', risk_explanation: msg || 'Inference failed' })
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Inference Testing</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Test live payloads and get prediction with confidence.
      </p>
      <div style={{ maxWidth: 600, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        {!modelList.length && (
          <p style={{ padding: '0.75rem', background: 'rgba(251,191,36,0.2)', borderRadius: 4, marginBottom: '1rem', color: 'var(--warning)', fontSize: '0.9rem' }}>
            No trained models yet. <Link to="/training/config" style={{ color: 'var(--accent)' }}>Train a model</Link> first.
          </p>
        )}
        <form onSubmit={handleSubmit}>
          {modelList.length > 1 && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.25rem' }}>Model</label>
              <select
                value={modelId || ''}
                onChange={(e) => setModelId(e.target.value)}
                style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
              >
                {modelList.map((m) => (
                  <option key={m.id} value={m.id}>{m.id}</option>
                ))}
              </select>
            </div>
          )}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.25rem' }}>Payload / Request Body</label>
            <textarea
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              rows={4}
              placeholder="Enter payload to test..."
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)', fontFamily: 'var(--font-mono)' }}
            />
          </div>
          <button type="submit" style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600 }}>
            Predict
          </button>
        </form>
        {result && (
          <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--bg-primary)', borderRadius: 4 }}>
            <div style={{ marginBottom: '0.5rem' }}>
              <strong>Prediction:</strong> <span style={{ color: result.prediction === 'benign' ? 'var(--success)' : 'var(--danger)' }}>{result.prediction}</span>
            </div>
            {result.confidence !== undefined && (
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Confidence:</strong> {(result.confidence * 100).toFixed(1)}%
              </div>
            )}
            {result.risk_explanation && (
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Explanation:</strong> {result.risk_explanation}
              </div>
            )}
            {result.top_features && result.top_features.length > 0 && (
              <div>
                <strong>Top features:</strong>
                <ul style={{ margin: '0.25rem 0 0', paddingLeft: '1.25rem' }}>
                  {result.top_features.map((f, i) => (
                    <li key={i}>{f.name}: {(f.importance * 100).toFixed(2)}%</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
