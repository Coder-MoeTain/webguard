import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { models } from '../services/api'
import { BarChart3, Cpu, ChevronDown, ChevronRight } from 'lucide-react'

type ModelWithMetrics = {
  id: string
  name: string
  path?: string
  algorithm?: string | null
  algorithm_label?: string | null
  test_accuracy?: number | null
  test_f1_macro?: number | null
  test_precision_macro?: number | null
  test_recall_macro?: number | null
  train_time_seconds?: number | null
  metrics?: {
    train?: Record<string, number | unknown>
    validation?: Record<string, number | unknown>
    test?: Record<string, number | unknown>
    train_time_seconds?: number
  } | null
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

function fmt(v: number | null | undefined): string {
  if (v == null) return '—'
  return (v * 100).toFixed(2) + '%'
}

function ModelDetailPanel({ metrics }: { metrics?: ModelWithMetrics['metrics'] }) {
  if (!metrics) {
    return <div style={{ padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>No metrics available for this model.</div>
  }
  const splits = [
    { key: 'train', label: 'Train' },
    { key: 'validation', label: 'Validation' },
    { key: 'test', label: 'Test' },
  ] as const
  const metricKeys = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro', 'f1_weighted', 'roc_auc', 'false_positive_rate', 'false_negative_rate'].filter(
    (k) => !['confusion_matrix', 'per_class_metrics'].includes(k)
  )
  return (
    <div style={{ padding: '1.5rem', background: 'var(--bg-primary)', margin: 0 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {splits.map(({ key, label }) => {
          const split = metrics[key as keyof typeof metrics] as Record<string, number> | undefined
          if (!split) return null
          return (
            <div key={key} style={{ ...cardStyle, padding: '1rem' }}>
              <h4 style={{ margin: '0 0 1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>{label}</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem 1rem', fontSize: '0.85rem' }}>
                {metricKeys.map((mk) => {
                  const v = split[mk]
                  if (v == null) return null
                  return (
                    <div key={mk}>
                      <div style={metricLabelStyle}>{mk.replace(/_/g, ' ')}</div>
                      <div style={{ fontWeight: 600 }}>{typeof v === 'number' ? (v <= 1 ? (v * 100).toFixed(2) + '%' : v.toFixed(0)) : String(v)}</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
      {metrics.train_time_seconds != null && (
        <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Total train time: {metrics.train_time_seconds.toFixed(1)}s
        </div>
      )}
    </div>
  )
}

export default function ModelEvaluation() {
  const [modelList, setModelList] = useState<ModelWithMetrics[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    setLoading(true)
    models
      .list({ include_metrics: true })
      .then(({ data }) => setModelList(data.models || []))
      .catch(() => setModelList([]))
      .finally(() => setLoading(false))
  }, [])

  const selected = modelList.find((m) => m.id === selectedId)
  const toggleCompare = (id: string) => {
    setCompareIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }
  const compareModels = modelList.filter((m) => compareIds.has(m.id))
  const compareChartData = compareModels.map((m) => ({
    name: `${m.algorithm_label || m.id} (${m.id.slice(-6)})`,
    accuracy: (m.test_accuracy ?? 0) * 100,
    f1: (m.test_f1_macro ?? 0) * 100,
    precision: (m.test_precision_macro ?? 0) * 100,
    recall: (m.test_recall_macro ?? 0) * 100,
  }))

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ margin: '0 0 0.25rem', fontSize: '1.75rem' }}>Model Evaluation</h1>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>
          View metrics for trained models. Compare accuracy, F1, precision, and recall across models.
        </p>
      </div>

      {/* Empty state */}
      {!loading && !modelList.length && (
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
          Loading models...
        </div>
      )}

      {/* Models table */}
      {!loading && modelList.length > 0 && (
        <div style={cardStyle}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BarChart3 size={18} /> Models
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--bg-card)' }}>
                  <th style={{ textAlign: 'left', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Model</th>
                  <th style={{ textAlign: 'left', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Algorithm</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Test Accuracy</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>F1 Macro</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Precision</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Recall</th>
                  <th style={{ textAlign: 'right', padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Train Time</th>
                  <th style={{ width: 80, padding: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>Compare</th>
                  <th style={{ width: 40, padding: '0.75rem' }} />
                </tr>
              </thead>
              <tbody>
                {modelList.map((m) => (
                  <React.Fragment key={m.id}>
                    <tr
                      key={m.id}
                      onClick={() => setSelectedId(selectedId === m.id ? null : m.id)}
                      style={{
                        borderBottom: '1px solid var(--bg-card)',
                        cursor: 'pointer',
                        background: selectedId === m.id ? 'rgba(var(--accent-rgb, 59, 130, 246), 0.08)' : undefined,
                      }}
                    >
                      <td style={{ padding: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{m.id}</td>
                      <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>{m.algorithm_label || m.algorithm || '—'}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>{fmt(m.test_accuracy)}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>{fmt(m.test_f1_macro)}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>{fmt(m.test_precision_macro)}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right' }}>{fmt(m.test_recall_macro)}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--text-muted)' }}>
                        {m.train_time_seconds != null ? `${m.train_time_seconds.toFixed(1)}s` : '—'}
                      </td>
                      <td style={{ padding: '0.75rem' }} onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => toggleCompare(m.id)}
                          style={{
                            padding: '0.25rem 0.5rem',
                            fontSize: '0.75rem',
                            background: compareIds.has(m.id) ? 'var(--accent)' : 'var(--bg-primary)',
                            color: compareIds.has(m.id) ? 'var(--bg-primary)' : 'var(--text)',
                            border: '1px solid var(--bg-card)',
                            borderRadius: 4,
                            cursor: 'pointer',
                          }}
                        >
                          {compareIds.has(m.id) ? '✓ Compare' : 'Compare'}
                        </button>
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        {selectedId === m.id ? <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} /> : <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />}
                      </td>
                    </tr>
                    {selectedId === m.id && selected && (
                      <tr key={`${m.id}-detail`}>
                        <td colSpan={9} style={{ padding: 0, borderBottom: '1px solid var(--bg-card)', verticalAlign: 'top' }}>
                          <ModelDetailPanel metrics={selected.metrics} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Compare models chart */}
      {!loading && compareModels.length > 0 && (
        <div style={{ ...cardStyle, marginTop: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Model Comparison</h3>
          <div style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={compareChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="name" stroke="var(--text-muted)" tick={{ fill: 'var(--text)', fontSize: 11 }} />
                <YAxis stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
                <Tooltip formatter={(v: number) => `${v.toFixed(2)}%`} contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 8 }} />
                <Legend />
                <Bar dataKey="accuracy" fill="var(--accent)" name="Accuracy" radius={[4, 4, 0, 0]} />
                <Bar dataKey="f1" fill="#22c55e" name="F1 Macro" radius={[4, 4, 0, 0]} />
                <Bar dataKey="precision" fill="#f59e0b" name="Precision" radius={[4, 4, 0, 0]} />
                <Bar dataKey="recall" fill="#8b5cf6" name="Recall" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
