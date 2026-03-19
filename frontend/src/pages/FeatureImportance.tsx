import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts'
import { BarChart3, PieChart as PieIcon, Table2, Download, Cpu, ChevronRight } from 'lucide-react'
import { models } from '../services/api'

type ModelDetail = {
  id: string
  classification_mode: string
  feature_mode: string
  feature_count: number
  feature_importance: Record<string, number>
  top_features: { name: string; importance: number }[]
  n_estimators?: number
  max_depth?: number
}

const cardStyle = {
  background: 'var(--bg-secondary)',
  borderRadius: 12,
  border: '1px solid var(--bg-card)',
  padding: '1.25rem',
}

const metricLabelStyle = {
  fontSize: '0.75rem',
  color: 'var(--text-muted)',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.05em',
  marginBottom: 4,
}

const TOP_N_OPTIONS = [10, 20, 30, 50, 100, 0] // 0 = all

export default function FeatureImportance() {
  const [modelList, setModelList] = useState<{ id: string; name?: string }[]>([])
  const [modelId, setModelId] = useState('')
  const [detail, setDetail] = useState<ModelDetail | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [viewMode, setViewMode] = useState<'bar' | 'pie' | 'table'>('bar')
  const [topN, setTopN] = useState(20)
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    if (!detail) return
    setDownloading(true)
    try {
      const { data } = await models.download(detail.id)
      const url = URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `${detail.id}.joblib`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      setError('Download failed')
    } finally {
      setDownloading(false)
    }
  }

  useEffect(() => {
    models.list().then(({ data: res }) => setModelList(res.models || [])).catch(() => [])
  }, [])

  useEffect(() => {
    if (!modelId) {
      setDetail(null)
      setError('')
      return
    }
    setLoading(true)
    setError('')
    models
      .detail(modelId)
      .then(({ data }) => setDetail(data))
      .catch(() => {
        setError('Failed to load model')
        setDetail(null)
      })
      .finally(() => setLoading(false))
  }, [modelId])

  const chartData =
    detail?.top_features.map((f) => ({
      name: f.name,
      value: f.importance * 100,
      importance: f.importance,
    })) ?? []

  const displayData = topN > 0 ? chartData.slice(0, topN) : chartData
  const maxVal = Math.max(...displayData.map((d) => d.value), 0.001)

  const pieData = displayData.slice(0, 10).map((d, i) => ({
    name: d.name.length > 20 ? d.name.slice(0, 18) + '…' : d.name,
    value: d.value,
    fill: `hsl(${210 - i * 15}, 70%, 55%)`,
  }))

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ margin: '0 0 0.25rem', fontSize: '1.75rem' }}>Feature Importance</h1>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>
          Top contributing features from Random Forest. Features with higher importance have stronger predictive power for attack detection.
        </p>
      </div>

      {/* Model selector */}
      <div style={{ ...cardStyle, marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center' }}>
          <div style={{ flex: '1 1 200px' }}>
            <label style={metricLabelStyle}>Model</label>
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              style={{
                width: '100%',
                padding: '0.6rem 1rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--bg-card)',
                borderRadius: 8,
                color: 'var(--text)',
                fontSize: '0.9rem',
              }}
            >
              <option value="">Select a model...</option>
              {modelList.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name ?? m.id}
                </option>
              ))}
            </select>
          </div>
          <div style={{ flex: '0 1 120px' }}>
            <label style={metricLabelStyle}>Show top</label>
            <select
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '0.6rem 1rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--bg-card)',
                borderRadius: 8,
                color: 'var(--text)',
                fontSize: '0.9rem',
              }}
            >
              {TOP_N_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n === 0 ? 'All' : n}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
            {(['bar', 'pie', 'table'] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setViewMode(mode)}
                style={{
                  padding: '0.5rem 0.75rem',
                  background: viewMode === mode ? 'var(--accent)' : 'var(--bg-primary)',
                  color: viewMode === mode ? 'var(--bg-primary)' : 'var(--text)',
                  border: '1px solid var(--bg-card)',
                  borderRadius: 8,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontSize: '0.85rem',
                }}
              >
                {mode === 'bar' && <BarChart3 size={16} />}
                {mode === 'pie' && <PieIcon size={16} />}
                {mode === 'table' && <Table2 size={16} />}
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Empty state */}
      {!modelList.length && (
        <div style={{ ...cardStyle, textAlign: 'center', padding: '3rem' }}>
          <Cpu size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem', opacity: 0.6 }} />
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>No trained models yet.</p>
          <Link to="/training/config" style={{ fontSize: '0.9rem', color: 'var(--accent)' }}>
            Train a model →
          </Link>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ ...cardStyle, textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading model...
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ ...cardStyle, padding: '1rem', background: 'rgba(248,113,113,0.15)', borderColor: 'var(--danger)', color: 'var(--danger)' }}>
          {error}
        </div>
      )}

      {/* Model metadata */}
      {detail && !loading && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Classification</div>
              <div style={{ fontWeight: 600 }}>{detail.classification_mode}</div>
            </div>
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Feature Mode</div>
              <div style={{ fontWeight: 600 }}>{detail.feature_mode.replace(/_/g, ' ')}</div>
            </div>
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Features</div>
              <div style={{ fontWeight: 600 }}>{detail.feature_count}</div>
            </div>
            {detail.n_estimators != null && (
              <div style={cardStyle}>
                <div style={metricLabelStyle}>n_estimators</div>
                <div style={{ fontWeight: 600 }}>{detail.n_estimators}</div>
              </div>
            )}
            {detail.max_depth != null && (
              <div style={cardStyle}>
                <div style={metricLabelStyle}>max_depth</div>
                <div style={{ fontWeight: 600 }}>{detail.max_depth}</div>
              </div>
            )}
            <div style={{ ...cardStyle, display: 'flex', alignItems: 'center' }}>
              <button
                type="button"
                onClick={handleDownload}
                disabled={downloading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  color: 'var(--accent)',
                  background: 'none',
                  border: 'none',
                  cursor: downloading ? 'not-allowed' : 'pointer',
                  fontSize: '0.9rem',
                  opacity: downloading ? 0.6 : 1,
                }}
              >
                <Download size={18} /> {downloading ? 'Downloading...' : 'Download'}
              </button>
            </div>
          </div>

          {/* Charts */}
          <div style={cardStyle}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BarChart3 size={18} /> Feature Importance
            </h3>

            {viewMode === 'bar' && (
              <div style={{ height: Math.min(400, Math.max(200, displayData.length * 28)) }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={displayData} layout="vertical" margin={{ left: 120, right: 20 }}>
                    <XAxis type="number" stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
                    <YAxis type="category" dataKey="name" width={115} stroke="var(--text-muted)" tick={{ fill: 'var(--text)', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 8 }}
                      formatter={(value: number) => [`${value.toFixed(3)}%`, 'Importance']}
                      labelFormatter={(label) => label}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {displayData.map((entry, i) => (
                        <Cell key={i} fill={`hsl(210, 70%, ${55 - (entry.value / maxVal) * 25}%)`} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {viewMode === 'pie' && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', alignItems: 'flex-start' }}>
                <div style={{ flex: '1 1 320px', minHeight: 320 }}>
                  <ResponsiveContainer width="100%" height={320}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                      >
                        {pieData.map((entry, i) => (
                          <Cell key={i} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 8 }} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ flex: '1 1 200px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  <p style={{ margin: 0 }}>Top 10 features by importance. Pie chart shows relative contribution to total importance.</p>
                </div>
              </div>
            )}

            {viewMode === 'table' && (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--bg-card)' }}>
                      <th style={{ textAlign: 'left', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>#</th>
                      <th style={{ textAlign: 'left', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Feature</th>
                      <th style={{ textAlign: 'right', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Importance</th>
                      <th style={{ width: 120, padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Relative</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayData.map((d, i) => (
                      <tr key={d.name} style={{ borderBottom: '1px solid var(--bg-card)' }}>
                        <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{i + 1}</td>
                        <td style={{ padding: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{d.name}</td>
                        <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>{d.value.toFixed(3)}%</td>
                        <td style={{ padding: '0.75rem' }}>
                          <div style={{ height: 8, background: 'var(--bg-primary)', borderRadius: 4, overflow: 'hidden' }}>
                            <div
                              style={{
                                width: `${(d.value / maxVal) * 100}%`,
                                height: '100%',
                                background: 'var(--accent)',
                                borderRadius: 4,
                              }}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <Link to={`/models/${detail.id}`} style={{ color: 'var(--accent)', display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              View full model details <ChevronRight size={14} />
            </Link>
          </p>
        </>
      )}
    </div>
  )
}
