import { useState, useEffect, useRef } from 'react'
import { Shield, AlertTriangle, Activity, BarChart3, Play, Square, Trash2 } from 'lucide-react'
import { ids, models } from '../services/api'

interface Alert {
  id: string
  timestamp: number
  prediction: string
  confidence: number
  method: string
  url: string
  payload_preview: string
  source_ip: string
  severity: string
  top_indicators: string[]
  second_best?: string | null
  second_confidence?: number | null
  confidence_margin?: number | null
  uncertain?: boolean
}

interface Stats {
  total_analyzed: number
  attacks_detected: number
  benign: number
  alerts_count: number
  attack_rate?: number
}

type TrafficSample = {
  type: string
  payload: string
  method?: string
  url?: string
  /** Send payload in body (e.g. POST) */
  useBody?: boolean
  /** Align HTTP context with CSRF-labeled training rows */
  request_context_profile?: 'csrf_attack'
}

const TRAFFIC_SAMPLES: TrafficSample[] = [
  { type: 'sqli', payload: "' OR 1=1--" },
  { type: 'sqli', payload: "admin'--" },
  { type: 'xss', payload: '<script>alert(1)</script>' },
  { type: 'xss', payload: '<img onerror=alert(1)>' },
  {
    type: 'csrf',
    payload: 'amount=1000&to=attacker',
    method: 'POST',
    url: '/api/transfer',
    useBody: true,
    request_context_profile: 'csrf_attack',
  },
  { type: 'benign', payload: 'laptop' },
  { type: 'benign', payload: 'user@email.com' },
]

function buildAnalyzePayload(sample: TrafficSample, modelId: string | undefined) {
  const body: {
    model_id?: string
    method?: string
    url?: string
    body?: string
    query_params?: string
    request_context_profile?: 'csrf_attack'
  } = {
    model_id: modelId || undefined,
    method: sample.method ?? 'GET',
    url: sample.url ?? '/search',
  }
  if (sample.useBody) {
    body.body = sample.payload
  } else {
    body.query_params = sample.payload
  }
  if (sample.request_context_profile) {
    body.request_context_profile = sample.request_context_profile
  }
  return body
}

export default function IDSDashboard() {
  const [modelList, setModelList] = useState<{ id: string; algorithm_label?: string }[]>([])
  const [modelId, setModelId] = useState('')
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [testPayload, setTestPayload] = useState("' OR 1=1--")
  const [testCsrfContext, setTestCsrfContext] = useState(false)
  const [lastResult, setLastResult] = useState<{
    prediction: string
    confidence: number
    alert_raised: boolean
    second_best?: string | null
    second_confidence?: number | null
    confidence_margin?: number
    uncertain?: boolean
  } | null>(null)
  const [simulatorRunning, setSimulatorRunning] = useState(false)
  const simulatorRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    models.list({ include_metrics: true }).then(({ data }) => setModelList(data.models || [])).catch(() => [])
  }, [])

  const fetchData = async () => {
    try {
      const [alertsRes, statsRes] = await Promise.all([
        ids.alerts({ limit: 50 }),
        ids.stats(),
      ])
      setAlerts(alertsRes.data.alerts || [])
      setStats(statsRes.data)
    } catch {
      setStats({ total_analyzed: 0, attacks_detected: 0, benign: 0, alerts_count: 0 })
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  const runTest = async () => {
    setLastResult(null)
    try {
      const { data } = await ids.analyze(
        testCsrfContext
          ? {
              method: 'POST',
              url: '/api/transfer',
              body: testPayload,
              model_id: modelId || undefined,
              request_context_profile: 'csrf_attack',
            }
          : {
              method: 'GET',
              url: '/search',
              query_params: testPayload,
              model_id: modelId || undefined,
            },
      )
      setLastResult({
        prediction: data.prediction,
        confidence: data.confidence,
        alert_raised: data.alert_raised,
        second_best: data.second_best,
        second_confidence: data.second_confidence,
        confidence_margin: data.confidence_margin,
        uncertain: data.uncertain,
      })
      fetchData()
    } catch {
      setLastResult({ prediction: 'Error', confidence: 0, alert_raised: false })
    }
  }

  const startSimulator = () => {
    if (simulatorRunning) return
    setSimulatorRunning(true)
    simulatorRef.current = setInterval(async () => {
      const sample = TRAFFIC_SAMPLES[Math.floor(Math.random() * TRAFFIC_SAMPLES.length)]
      try {
        await ids.analyze(buildAnalyzePayload(sample, modelId || undefined))
        fetchData()
      } catch {}
    }, 2500)
  }

  const stopSimulator = () => {
    if (simulatorRef.current) {
      clearInterval(simulatorRef.current)
      simulatorRef.current = null
    }
    setSimulatorRunning(false)
  }

  useEffect(() => () => stopSimulator(), [])

  const severityColor: Record<string, string> = {
    critical: 'var(--danger)',
    high: '#f97316',
    medium: 'var(--warning)',
    low: 'var(--accent)',
    info: 'var(--text-muted)',
  }

  return (
    <div>
      <h1 style={{ margin: '0 0 1rem', fontSize: '1.75rem' }}>IDS stream (research demo)</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>
        Live scoring UI for experiment models — not a substitute for a production WAF. Multiclass labels: benign, SQLi, XSS, CSRF.
      </p>

      {/* Model selector */}
      <div style={{ marginBottom: '1.5rem', maxWidth: 400 }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Detection Model</label>
        <select
          value={modelId}
          onChange={(e) => setModelId(e.target.value)}
          style={{
            width: '100%',
            padding: '0.6rem 1rem',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--bg-card)',
            borderRadius: 8,
            color: 'var(--text)',
            fontSize: '0.9rem',
          }}
        >
          <option value="">Latest model (auto)</option>
          {modelList.map((m) => (
            <option key={m.id} value={m.id}>{m.algorithm_label ? `${m.algorithm_label} — ${m.id}` : m.id}</option>
          ))}
        </select>
      </div>

      {/* Stats cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Activity size={20} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Requests Analyzed</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{stats?.total_analyzed ?? 0}</div>
        </div>
        <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertTriangle size={20} style={{ color: 'var(--danger)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Attacks Detected</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--danger)' }}>{stats?.attacks_detected ?? 0}</div>
        </div>
        <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <Shield size={20} style={{ color: 'var(--success)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Benign</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)' }}>{stats?.benign ?? 0}</div>
        </div>
        <div style={{ padding: '1.25rem', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <BarChart3 size={20} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Attack Rate</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
            {stats?.total_analyzed ? ((stats.attacks_detected / stats.total_analyzed) * 100).toFixed(1) : 0}%
          </div>
        </div>
      </div>

      {/* Test & Simulator */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Test Request</h3>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <input
              value={testPayload}
              onChange={(e) => setTestPayload(e.target.value)}
              placeholder="Enter payload..."
              style={{
                flex: 1,
                padding: '0.6rem',
                background: 'var(--bg-primary)',
                border: '1px solid var(--bg-card)',
                borderRadius: 4,
                color: 'var(--text)',
                fontFamily: 'var(--font-mono)',
              }}
            />
            <button
              onClick={runTest}
              style={{
                padding: '0.6rem 1rem',
                background: 'var(--accent)',
                border: 'none',
                borderRadius: 4,
                color: 'var(--bg-primary)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Analyze
            </button>
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)', cursor: 'pointer', marginBottom: '0.5rem' }}>
            <input type="checkbox" checked={testCsrfContext} onChange={(e) => setTestCsrfContext(e.target.checked)} />
            CSRF context (POST + session cookie, no CSRF token / referer)
          </label>
          {lastResult && (
            <div style={{
              marginTop: '0.75rem',
              padding: '0.75rem',
              background: lastResult.prediction !== 'benign' ? 'rgba(248,113,113,0.15)' : 'rgba(74,222,128,0.15)',
              borderRadius: 4,
              border: `1px solid ${lastResult.prediction !== 'benign' ? 'var(--danger)' : 'var(--success)'}`,
            }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.5rem' }}>
                <strong>{lastResult.prediction}</strong>
                <span>({(lastResult.confidence * 100).toFixed(1)}%)</span>
                {lastResult.uncertain && (
                  <span style={{ fontSize: '0.75rem', padding: '0.15rem 0.45rem', borderRadius: 999, background: 'var(--warning)', color: 'var(--bg-primary)', fontWeight: 600 }}>
                    Low certainty
                  </span>
                )}
                {lastResult.alert_raised && <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>— Alert raised</span>}
              </div>
              {lastResult.second_best != null && lastResult.second_confidence != null && (
                <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Runner-up: <strong style={{ color: 'var(--text)' }}>{lastResult.second_best}</strong> ({(lastResult.second_confidence * 100).toFixed(1)}%)
                  {lastResult.confidence_margin != null && (
                    <> · Margin Δ{(lastResult.confidence_margin * 100).toFixed(1)}%</>
                  )}
                </p>
              )}
            </div>
          )}
        </div>

        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Traffic Simulator</h3>
          <p style={{ margin: '0 0 1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Random mix of SQLi, XSS, CSRF-style POST (missing CSRF token context), and benign strings. Alerts show runner-up class and margin when the model is unsure.
          </p>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={startSimulator}
              disabled={simulatorRunning}
              style={{
                padding: '0.6rem 1rem',
                background: simulatorRunning ? 'var(--bg-card)' : 'var(--success)',
                border: 'none',
                borderRadius: 4,
                color: 'var(--text)',
                cursor: simulatorRunning ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <Play size={16} /> {simulatorRunning ? 'Running...' : 'Start'}
            </button>
            <button
              onClick={stopSimulator}
              disabled={!simulatorRunning}
              style={{
                padding: '0.6rem 1rem',
                background: 'var(--danger)',
                border: 'none',
                borderRadius: 4,
                color: 'white',
                cursor: simulatorRunning ? 'pointer' : 'default',
                opacity: simulatorRunning ? 1 : 0.5,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <Square size={16} /> Stop
            </button>
          </div>
        </div>
      </div>

      {/* Live alerts */}
        <div style={{ background: 'var(--bg-secondary)', padding: '1.5rem', borderRadius: 8, border: '1px solid var(--bg-card)' }}>
          <h3 style={{ margin: '0 0 1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <AlertTriangle size={20} style={{ color: 'var(--danger)' }} />
              Live Alerts ({alerts.length})
            </span>
            <button
              onClick={async () => { await ids.clear(); fetchData(); }}
              style={{ padding: '0.35rem 0.75rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text-muted)', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <Trash2 size={14} /> Clear
            </button>
          </h3>
        {alerts.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', margin: 0 }}>No alerts yet. Send test requests or start the traffic simulator.</p>
        ) : (
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--bg-card)', position: 'sticky', top: 0, background: 'var(--bg-secondary)' }}>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Time</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Type</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Confidence</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>2nd / Δ</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Method</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Payload</th>
                  <th style={{ textAlign: 'left', padding: '0.5rem' }}>Source</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr
                    key={a.id}
                    style={{
                      borderBottom: '1px solid var(--bg-card)',
                      opacity: a.uncertain ? 0.92 : 1,
                    }}
                  >
                    <td style={{ padding: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(a.timestamp * 1000).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '0.5rem' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', flexWrap: 'wrap' }}>
                        <span style={{ color: severityColor[a.severity] || 'var(--text)' }}>{a.prediction}</span>
                        {a.uncertain && (
                          <span style={{ fontSize: '0.65rem', padding: '0.1rem 0.35rem', borderRadius: 4, background: 'rgba(251,191,36,0.35)', color: 'var(--text)', fontWeight: 600 }}>
                            ?
                          </span>
                        )}
                      </span>
                    </td>
                    <td style={{ padding: '0.5rem' }}>{(a.confidence * 100).toFixed(1)}%</td>
                    <td style={{ padding: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)', maxWidth: 140 }}>
                      {a.second_best != null && a.second_confidence != null ? (
                        <>
                          {a.second_best} {(a.second_confidence * 100).toFixed(0)}%
                          {a.confidence_margin != null && (
                            <> · Δ{(a.confidence_margin * 100).toFixed(0)}%</>
                          )}
                        </>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td style={{ padding: '0.5rem' }}>{a.method}</td>
                    <td style={{ padding: '0.5rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }} title={a.payload_preview}>
                      <code style={{ fontSize: '0.8rem' }}>{a.payload_preview.slice(0, 40)}{a.payload_preview.length > 40 ? '...' : ''}</code>
                    </td>
                    <td style={{ padding: '0.5rem', fontSize: '0.8rem' }}>{a.source_ip}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
