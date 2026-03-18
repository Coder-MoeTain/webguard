import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { models } from '../services/api'

const PLACEHOLDER_DATA = [
  { name: 'has_script_tag', value: 0.12 },
  { name: 'has_union', value: 0.09 },
  { name: 'angle_bracket_count', value: 0.08 },
  { name: 'payload_length', value: 0.07 },
  { name: 'has_select', value: 0.06 },
]

export default function FeatureImportance() {
  const [modelList, setModelList] = useState<{ id: string; name: string }[]>([])
  const [modelId, setModelId] = useState('')
  const [data, setData] = useState<{ name: string; value: number }[]>(PLACEHOLDER_DATA)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    models.list().then(({ data: res }) => setModelList(res.models || [])).catch(() => [])
  }, [])

  useEffect(() => {
    if (!modelId) {
      setData(PLACEHOLDER_DATA)
      return
    }
    setLoading(true)
    models.detail(modelId)
      .then(({ data: detail }) => {
        const top = (detail.top_features || []).slice(0, 15).map((f: { name: string; importance: number }) => ({
          name: f.name,
          value: f.importance,
        }))
        setData(top.length ? top : PLACEHOLDER_DATA)
      })
      .catch(() => setData(PLACEHOLDER_DATA))
      .finally(() => setLoading(false))
  }, [modelId])

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Feature Importance</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Top contributing features from Random Forest. Select a model to view its feature importance.
      </p>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <select
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          style={{ padding: '0.6rem', minWidth: 200, background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
        >
          <option value="">Select model (or view example)</option>
          {modelList.map((m) => (
            <option key={m.id} value={m.id}>{m.id}</option>
          ))}
        </select>
        {loading && <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading...</span>}
      </div>
      <div style={{ height: 400, background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" stroke="var(--text-muted)" />
            <YAxis type="category" dataKey="name" width={90} stroke="var(--text-muted)" tick={{ fill: 'var(--text)' }} />
            <Tooltip contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)' }} />
            <Bar dataKey="value" fill="var(--accent)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
