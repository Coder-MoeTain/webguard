import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { robustness, models, datasets } from '../services/api'

type ZeroOutResult = {
  model_id: string
  test_type: 'zero_out'
  baseline_accuracy: number
  accuracy_drops: Record<string, number>
  sorted_by_sensitivity: { feature: string; accuracy_drop: number }[]
}

type AblationResult = {
  model_id: string
  test_type: 'ablation'
  baseline_accuracy: number
  group_accuracies: Record<string, number>
  accuracy_drops: Record<string, number>
}

type RobustnessResult = ZeroOutResult | AblationResult

export default function RobustnessAnalysis() {
  const [modelList, setModelList] = useState<{ id: string; algorithm_label?: string }[]>([])
  const [datasetList, setDatasetList] = useState<{ path: string; name: string }[]>([])
  const [modelId, setModelId] = useState('')
  const [dataPath, setDataPath] = useState('data/sample_sqli_37_features.parquet')
  const [testType, setTestType] = useState<'zero_out' | 'ablation'>('zero_out')
  const [topN, setTopN] = useState(10)
  const [result, setResult] = useState<RobustnessResult | null>(null)
  const [compareModelIds, setCompareModelIds] = useState<string[]>([])
  const [compareResults, setCompareResults] = useState<RobustnessResult[]>([])
  const [compareLoading, setCompareLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    models.list({ include_metrics: true }).then(({ data }) => setModelList(data.models || [])).catch(() => [])
    datasets.list().then(({ data }) => setDatasetList(data.datasets || [])).catch(() => [])
  }, [])

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const { data } = await robustness.analyze({
        model_id: modelId || undefined,
        data_path: dataPath,
        test_type: testType,
        top_n: topN,
      })
      setResult(data)
    } catch (err: unknown) {
      let msg = ''
      if (err && typeof err === 'object' && 'response' in err) {
        const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
        msg = Array.isArray(detail) ? detail.map((m: { msg?: string }) => m?.msg).filter(Boolean).join('; ') : String(detail ?? 'Request failed')
      } else {
        msg = err instanceof Error ? err.message : String(err)
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const chartDataZeroOut = result && result.test_type === 'zero_out'
    ? result.sorted_by_sensitivity.map(({ feature, accuracy_drop }) => ({ name: feature, value: accuracy_drop, fill: accuracy_drop > 0.05 ? 'var(--danger)' : accuracy_drop > 0.02 ? 'var(--accent)' : 'var(--text-muted)' }))
    : []

  const chartDataAblation = result && result.test_type === 'ablation'
    ? Object.entries(result.accuracy_drops).map(([name, value]) => ({ name, value, fill: value > 0.1 ? 'var(--danger)' : value > 0.05 ? 'var(--accent)' : 'var(--text-muted)' }))
    : []

  const chartData = testType === 'zero_out' ? chartDataZeroOut : chartDataAblation

  const runCompare = async (e: React.FormEvent) => {
    e.preventDefault()
    if (compareModelIds.length < 2) return
    setCompareLoading(true)
    setCompareResults([])
    try {
      const results = await Promise.all(
        compareModelIds.map((mid) =>
          robustness.analyze({ model_id: mid, data_path: dataPath, test_type: testType, top_n: topN }).then((r) => r.data)
        )
      )
      setCompareResults(results)
    } catch {
      setCompareResults([])
    } finally {
      setCompareLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem' }}>Robustness Analysis</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Feature ablation, zero-out sensitivity, and group-based accuracy impact.
      </p>

      <form onSubmit={handleAnalyze} style={{ maxWidth: 600, marginBottom: '2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Model</label>
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              <option value="">Latest model</option>
              {modelList.map((m) => (
                <option key={m.id} value={m.id}>{m.algorithm_label ? `${m.algorithm_label} — ${m.id}` : m.id}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Test Dataset</label>
            <select
              value={dataPath}
              onChange={(e) => setDataPath(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              {datasetList.length ? datasetList.map((d) => (
                <option key={d.path} value={d.path}>{d.name}</option>
              )) : <option value={dataPath}>{dataPath}</option>}
            </select>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Test Type</label>
            <select
              value={testType}
              onChange={(e) => setTestType(e.target.value as 'zero_out' | 'ablation')}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              <option value="zero_out">Zero-out sensitivity (top N features)</option>
              <option value="ablation">Feature group ablation</option>
            </select>
          </div>
          {testType === 'zero_out' && (
            <div>
              <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.9rem' }}>Top N features</label>
              <input
                type="number"
                value={topN}
                onChange={(e) => setTopN(Number(e.target.value) || 10)}
                min={1}
                max={50}
                style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
              />
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <button type="submit" disabled={loading} style={{ padding: '0.75rem 1.5rem', background: 'var(--accent)', border: 'none', borderRadius: 4, color: 'var(--bg-primary)', fontWeight: 600 }}>
            {loading ? 'Analyzing...' : 'Run Analysis'}
          </button>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
            <div>
              <span style={{ display: 'block', fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Compare models (select 2+):</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', maxWidth: 400 }}>
                {modelList.map((m) => (
                  <label key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={compareModelIds.includes(m.id)}
                      onChange={(e) => setCompareModelIds((prev) => (e.target.checked ? [...prev, m.id] : prev.filter((id) => id !== m.id)))}
                    />
                    {m.algorithm_label ? `${m.algorithm_label} (${m.id.slice(-6)})` : m.id}
                  </label>
                ))}
              </div>
            </div>
            <button type="button" onClick={runCompare} disabled={compareModelIds.length < 2 || compareLoading} style={{ padding: '0.5rem 1rem', background: 'var(--bg-card)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)', cursor: compareModelIds.length < 2 || compareLoading ? 'not-allowed' : 'pointer', alignSelf: 'flex-end' }}>
              {compareLoading ? 'Running...' : 'Compare'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(248,113,113,0.2)', borderRadius: 4, color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3 style={{ margin: '0 0 1rem' }}>Results — {result.model_id}</h3>
          {(() => {
            const m = modelList.find((x) => x.id === result.model_id)
            return m?.algorithm_label ? <p style={{ margin: '0 0 1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Algorithm: {m.algorithm_label}</p> : null
          })()}
          <div style={{ marginBottom: '1rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Baseline accuracy</span>
              <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{(result.baseline_accuracy * 100).toFixed(2)}%</div>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Test type</span>
              <div style={{ fontSize: '1rem' }}>{result.test_type === 'zero_out' ? 'Zero-out sensitivity' : 'Feature group ablation'}</div>
            </div>
          </div>

          {chartData.length > 0 && (
            <div style={{ height: 400, marginTop: '1rem' }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                {result.test_type === 'zero_out' ? 'Accuracy drop when zeroing each feature (higher = more sensitive)' : 'Accuracy drop when ablating each feature group'}
              </div>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 100 }}>
                  <XAxis type="number" stroke="var(--text-muted)" />
                  <YAxis type="category" dataKey="name" width={90} stroke="var(--text-muted)" tick={{ fill: 'var(--text)', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)' }} formatter={(v: number) => [`${(v * 100).toFixed(2)}%`, 'Accuracy drop']} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {result.test_type === 'ablation' && result.group_accuracies && (
            <div style={{ marginTop: '1.5rem' }}>
              <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem' }}>Group accuracies</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '0.5rem' }}>
                {Object.entries(result.group_accuracies).map(([name, acc]) => (
                  <div key={name} style={{ padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: 4 }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{name}</div>
                    <div style={{ fontWeight: 600 }}>{(acc * 100).toFixed(2)}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {compareResults.length > 0 && (
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)', marginTop: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem' }}>Model Comparison</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--bg-card)' }}>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Model (Algorithm)</th>
                  <th style={{ textAlign: 'right', padding: '0.5rem' }}>Baseline Accuracy</th>
                  {compareResults[0]?.test_type === 'ablation' && Object.keys((compareResults[0] as AblationResult).group_accuracies || {}).map((g) => (
                    <th key={g} style={{ textAlign: 'right', padding: '0.5rem' }}>{g}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {compareResults.map((r) => {
                  const m = modelList.find((x) => x.id === r.model_id)
                  return (
                    <tr key={r.model_id} style={{ borderBottom: '1px solid var(--bg-card)' }}>
                      <td style={{ padding: '0.5rem' }}>{m?.algorithm_label ? `${m.algorithm_label} (${r.model_id})` : r.model_id}</td>
                      <td style={{ padding: '0.5rem', textAlign: 'right', fontWeight: 600 }}>{(r.baseline_accuracy * 100).toFixed(2)}%</td>
                      {r.test_type === 'ablation' && Object.values((r as AblationResult).group_accuracies || {}).map((acc, j) => (
                        <td key={j} style={{ padding: '0.5rem', textAlign: 'right' }}>{(acc * 100).toFixed(2)}%</td>
                      ))}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
