import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts'
import { Cpu, HardDrive, Gauge, Activity, Settings, ChevronRight, AlertCircle } from 'lucide-react'
import { training, system } from '../services/api'

type JobStatus = {
  phase?: string
  progress?: number
  step?: string
  detail?: string
  samples_loaded?: number
  train_size?: number
  val_size?: number
  test_size?: number
  feature_count?: number
  config?: Record<string, unknown>
  metrics?: Record<string, unknown>
  train_time_seconds?: number
  error?: string
}

type SystemMetrics = {
  cpu?: { cpu_percent: number; cpu_count: number; memory_percent: number; memory_used_mb: number; memory_total_mb: number }
  gpu?: { available: boolean; gpus?: { name: string; memory_used_mb: number; memory_total_mb: number; utilization_percent: number }[] }
}

type ProgressPoint = { time: number; progress: number; label: string }

const cardStyle = {
  background: 'var(--bg-secondary)',
  borderRadius: 12,
  border: '1px solid var(--bg-card)',
  padding: '1.25rem',
}

const metricLabelStyle = { fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' as const, letterSpacing: '0.05em', marginBottom: 4 }

export default function TrainingMonitor() {
  const { jobId } = useParams<{ jobId: string }>()
  const [status, setStatus] = useState<JobStatus | null>(null)
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null)
  const [progressHistory, setProgressHistory] = useState<ProgressPoint[]>([])
  const [elapsedSec, setElapsedSec] = useState(0)
  const startTimeRef = useRef<number | null>(null)

  useEffect(() => {
    if (!jobId) return
    startTimeRef.current = Date.now()
    const interval = setInterval(async () => {
      try {
        const { data } = await training.status(jobId)
        setStatus(data)
        if (data.phase === 'completed' || data.phase === 'failed') clearInterval(interval)
        setProgressHistory((prev) => {
          const next = [...prev, { time: Math.floor((Date.now() - (startTimeRef.current || Date.now())) / 1000), progress: data.progress ?? 0, label: data.step || data.phase || '' }]
          return next.slice(-60)
        })
      } catch {
        clearInterval(interval)
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [jobId])

  useEffect(() => {
    if (!jobId || !status || (status.phase !== 'running' && status.phase !== 'starting' && status.phase !== 'queued')) return
    const interval = setInterval(async () => {
      try {
        const { data } = await system.metrics()
        setSystemMetrics(data)
      } catch {}
    }, 3000)
    return () => clearInterval(interval)
  }, [jobId, status?.phase])

  useEffect(() => {
    if (!startTimeRef.current || (status?.phase === 'completed' || status?.phase === 'failed')) return
    const t = setInterval(() => setElapsedSec(Math.floor((Date.now() - startTimeRef.current!) / 1000)), 1000)
    return () => clearInterval(t)
  }, [status?.phase])

  if (!status) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <Activity size={48} style={{ margin: '0 auto 1rem', opacity: 0.5, animation: 'pulse 1.5s ease-in-out infinite' }} />
          <p>Loading training status...</p>
        </div>
      </div>
    )
  }

  const isRunning = status.phase === 'running' || status.phase === 'starting' || status.phase === 'queued'
  const isComplete = status.phase === 'completed'
  const isFailed = status.phase === 'failed'

  const phaseColor = isComplete ? 'var(--success)' : isFailed ? 'var(--danger)' : 'var(--accent)'
  const phaseLabel = status.phase === 'queued' ? 'Queued' : status.phase === 'starting' ? 'Starting' : status.phase === 'running' ? 'Training' : status.phase === 'completed' ? 'Completed' : status.phase === 'failed' ? 'Failed' : status.phase || 'Running'

  const metrics = status.metrics as Record<string, unknown> | undefined
  const testMetrics = metrics?.test as Record<string, number> | undefined
  const trainMetrics = metrics?.train as Record<string, number> | undefined
  const valMetrics = metrics?.validation as Record<string, number> | undefined
  const featureImportance = metrics?.feature_importance as Record<string, number> | undefined

  const accuracyChartData = [
    testMetrics?.accuracy != null && { split: 'Test', accuracy: testMetrics.accuracy * 100, fill: 'var(--accent)' },
    trainMetrics?.accuracy != null && { split: 'Train', accuracy: trainMetrics.accuracy * 100, fill: 'var(--success)' },
    valMetrics?.accuracy != null && { split: 'Validation', accuracy: valMetrics.accuracy * 100, fill: 'var(--warning)' },
  ].filter(Boolean) as { split: string; accuracy: number; fill: string }[]

  const importanceData = featureImportance
    ? Object.entries(featureImportance)
        .sort(([, a], [, b]) => (b as number) - (a as number))
        .slice(0, 12)
        .map(([name, value]) => ({ name, value: (value as number) * 100 }))
    : []

  const formatElapsed = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ margin: '0 0 0.25rem', fontSize: '1.75rem' }}>Training Monitor</h1>
          <p style={{ color: 'var(--text-muted)', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            Job ID: <code style={{ background: 'var(--bg-card)', padding: '0.2rem 0.5rem', borderRadius: 4 }}>{jobId}</code>
            {isRunning && <span style={{ color: 'var(--accent)', marginLeft: '0.5rem' }}>• {formatElapsed(elapsedSec)}</span>}
          </p>
        </div>
        <Link to="/training/config" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', fontSize: '0.9rem' }}>
          ← Back to Config <ChevronRight size={16} style={{ transform: 'rotate(180deg)' }} />
        </Link>
      </div>

      {/* Phase badge & progress */}
      <div style={{ ...cardStyle, marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.4rem 0.9rem',
              borderRadius: 8,
              background: `${phaseColor}22`,
              color: phaseColor,
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            {isRunning && <Activity size={16} style={{ animation: 'spin 1s linear infinite' }} />}
            {phaseLabel}
          </span>
          <span style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text)' }}>{status.progress ?? 0}%</span>
        </div>
        <div style={{ height: 12, background: 'var(--bg-primary)', borderRadius: 6, overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${status.progress ?? 0}%`,
              background: `linear-gradient(90deg, ${phaseColor}, ${phaseColor}99)`,
              transition: 'width 0.5s ease',
              borderRadius: 6,
            }}
          />
        </div>
        {status.step && (
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Current step: {status.step}
            {status.detail && ` — ${status.detail}`}
          </p>
        )}
      </div>

      {/* Stats grid */}
      {(status.samples_loaded != null || status.train_size != null || status.feature_count != null) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          {status.samples_loaded != null && (
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Samples</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{status.samples_loaded.toLocaleString()}</div>
            </div>
          )}
          {status.train_size != null && (
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Train</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{status.train_size.toLocaleString()}</div>
            </div>
          )}
          {status.val_size != null && (
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Validation</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{status.val_size.toLocaleString()}</div>
            </div>
          )}
          {status.test_size != null && (
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Test</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{status.test_size.toLocaleString()}</div>
            </div>
          )}
          {status.feature_count != null && (
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Features</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{status.feature_count}</div>
            </div>
          )}
          {metrics?.train_time_seconds != null && (
            <div style={cardStyle}>
              <div style={metricLabelStyle}>Train Time</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{Number(metrics.train_time_seconds).toFixed(1)}s</div>
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        {/* Progress over time chart */}
        {progressHistory.length > 1 && (
          <div style={{ ...cardStyle, minHeight: 260 }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={18} /> Progress Over Time
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={progressHistory}>
                <XAxis dataKey="time" stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <YAxis stroke="var(--text-muted)" domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 8 }} labelFormatter={(t) => `Elapsed: ${t}s`} />
                <Line type="monotone" dataKey="progress" stroke="var(--accent)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* System metrics: CPU, Memory, GPU */}
        {isRunning && (
          <div style={{ ...cardStyle, minHeight: 260 }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Gauge size={18} /> Process Monitor
            </h3>
            {systemMetrics ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
                  <Cpu size={24} style={{ color: 'var(--accent)' }} />
                  <div style={{ flex: 1 }}>
                    <div style={metricLabelStyle}>CPU</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ flex: 1, height: 8, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{ width: `${systemMetrics.cpu?.cpu_percent ?? 0}%`, height: '100%', background: 'var(--accent)', borderRadius: 4 }} />
                      </div>
                      <span style={{ fontWeight: 600, minWidth: 45 }}>{systemMetrics.cpu?.cpu_percent ?? 0}%</span>
                    </div>
                    {systemMetrics.cpu?.cpu_count && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{systemMetrics.cpu.cpu_count} cores</span>}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
                  <HardDrive size={24} style={{ color: 'var(--success)' }} />
                  <div style={{ flex: 1 }}>
                    <div style={metricLabelStyle}>Memory</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ flex: 1, height: 8, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{ width: `${systemMetrics.cpu?.memory_percent ?? 0}%`, height: '100%', background: 'var(--success)', borderRadius: 4 }} />
                      </div>
                      <span style={{ fontWeight: 600, minWidth: 45 }}>{systemMetrics.cpu?.memory_percent ?? 0}%</span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {systemMetrics.cpu?.memory_used_mb ?? 0} / {systemMetrics.cpu?.memory_total_mb ?? 0} MB
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem', background: 'var(--bg-primary)', borderRadius: 8 }}>
                  <Gauge size={24} style={{ color: 'var(--warning)' }} />
                  <div style={{ flex: 1 }}>
                    <div style={metricLabelStyle}>GPU</div>
                    {systemMetrics.gpu?.available && systemMetrics.gpu.gpus?.length ? (
                      systemMetrics.gpu.gpus.map((g, i) => (
                        <div key={i} style={{ marginTop: i > 0 ? '0.5rem' : 0 }}>
                          <div style={{ fontSize: '0.8rem', marginBottom: 4 }}>{g.name}</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ flex: 1, height: 6, background: 'var(--bg-card)', borderRadius: 4, overflow: 'hidden' }}>
                              <div style={{ width: `${g.utilization_percent}%`, height: '100%', background: 'var(--warning)', borderRadius: 4 }} />
                            </div>
                            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{g.utilization_percent}%</span>
                          </div>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{g.memory_used_mb} / {g.memory_total_mb} MB</span>
                        </div>
                      ))
                    ) : (
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>CPU-only (Random Forest)</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading system metrics...</p>
            )}
          </div>
        )}
      </div>

      {/* Config */}
      {status.config && Object.keys(status.config).length > 0 && (
        <div style={{ ...cardStyle, marginTop: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Settings size={18} /> Configuration
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.75rem' }}>
            {Object.entries(status.config).map(([k, v]) => (
              <div key={k} style={{ padding: '0.5rem', background: 'var(--bg-primary)', borderRadius: 6, fontSize: '0.85rem' }}>
                <div style={metricLabelStyle}>{k.replace(/_/g, ' ')}</div>
                <div style={{ fontWeight: 500 }}>{String(v)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {status.error && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(248,113,113,0.15)', borderRadius: 8, border: '1px solid var(--danger)', display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
          <AlertCircle size={20} style={{ color: 'var(--danger)', flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontWeight: 600, color: 'var(--danger)', marginBottom: '0.25rem' }}>Training Failed</div>
            <div style={{ color: 'var(--text)', fontSize: '0.9rem' }}>{status.error}</div>
          </div>
        </div>
      )}

      {/* Results: charts when completed */}
      {isComplete && metrics && (
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {accuracyChartData.length > 0 && (
            <div style={cardStyle}>
              <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Accuracy by Split</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={accuracyChartData} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                  <XAxis dataKey="split" stroke="var(--text-muted)" tick={{ fill: 'var(--text)' }} />
                  <YAxis stroke="var(--text-muted)" domain={[0, 100]} tick={{ fill: 'var(--text-muted)' }} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 8 }}
                    formatter={(v: number) => [`${v.toFixed(2)}%`, 'Accuracy']}
                  />
                  <Bar dataKey="accuracy" radius={[4, 4, 0, 0]}>
                    <LabelList
                      dataKey="accuracy"
                      position="insideTop"
                      formatter={(v: number) => `${Number(v).toFixed(1)}%`}
                      style={{ fill: '#ffffff', fontSize: 13, fontWeight: 700 }}
                    />
                    {accuracyChartData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {importanceData.length > 0 && (
            <div style={cardStyle}>
              <h3 style={{ margin: '0 0 1rem', fontSize: '1rem' }}>Top Feature Importance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={importanceData} layout="vertical" margin={{ left: 100 }}>
                  <XAxis type="number" stroke="var(--text-muted)" tick={{ fill: 'var(--text-muted)' }} />
                  <YAxis type="category" dataKey="name" width={95} stroke="var(--text-muted)" tick={{ fill: 'var(--text)', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 8 }} formatter={(v: number) => [`${v.toFixed(2)}%`, 'Importance']} />
                  <Bar dataKey="value" fill="var(--accent)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 0.5; } 50% { opacity: 1; } }
      `}</style>
    </div>
  )
}
