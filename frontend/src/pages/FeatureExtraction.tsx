import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { features, datasets } from '../services/api'

type DatasetItem = { path: string; name: string }
type ExtractStatus = {
  phase?: string
  progress?: number
  written?: number
  total?: number
  output_path?: string
  error?: string
}

type PreviewData = {
  columns?: string[]
  rows: Record<string, string>[]
  total_rows?: number | null
  preview_rows?: number
  label_counts?: Record<string, number>
}

export default function FeatureExtraction() {
  const [datasetList, setDatasetList] = useState<{ path: string; name: string }[]>([])
  /** No hardcoded path — first dataset from API is selected when the list loads. */
  const [inputPath, setInputPath] = useState('')
  const [featureMode, setFeatureMode] = useState<'payload_only' | 'response_only' | 'hybrid' | 'sqli_37'>('payload_only')
  const [result, setResult] = useState<{ job_id?: string; output_path?: string } | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const [extractStatus, setExtractStatus] = useState<ExtractStatus | null>(null)
  const [featureFiles, setFeatureFiles] = useState<DatasetItem[]>([])
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const [preview, setPreview] = useState<PreviewData | null>(null)

  useEffect(() => {
    datasets
      .list()
      .then(({ data }) => {
        const list = data.datasets || []
        setDatasetList(list)
        if (list.length) {
          const isValidSelection = list.some((d: { path: string }) => d.path === inputPath)
          if (!inputPath || !isValidSelection) setInputPath(list[0].path)
        }
      })
      .catch(() => {})
  }, [])

  const loadFeatureFiles = () => {
    datasets
      .list()
      .then(({ data }) => {
        const files = (data.datasets || []).filter((d: { name: string; path: string }) =>
          String(d.name).startsWith('features_'),
        )
        setFeatureFiles(files)
      })
      .catch(() => setFeatureFiles([]))
  }

  useEffect(() => {
    loadFeatureFiles()
  }, [])

  useEffect(() => {
    const jobId = result?.job_id
    if (!jobId) return

    let cancelled = false
    let timeoutId: number | undefined

    const poll = async () => {
      try {
        const { data } = await features.status(jobId)
        if (cancelled) return
        setExtractStatus(data)

        const phase = data.phase
        if (phase === 'completed' || phase === 'failed') return
      } catch (err) {
        if (!cancelled) {
          setExtractStatus((prev) => prev ?? { phase: 'running', progress: 0 })
        }
      }

      timeoutId = window.setTimeout(poll, 1500)
    }

    poll()

    return () => {
      cancelled = true
      if (timeoutId) window.clearTimeout(timeoutId)
    }
  }, [result?.job_id])

  useEffect(() => {
    if (extractStatus?.phase !== 'completed') return
    const outputPath = result?.output_path
    if (!outputPath) return

    setPreviewLoading(true)
    setPreviewError('')
    setPreview(null)

    loadFeatureFiles()
    datasets
      .preview(outputPath, 20)
      .then(({ data }) => {
        setPreview(data)
      })
      .catch((err: unknown) => {
        const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
        setPreviewError(msg || 'Preview failed')
      })
      .finally(() => setPreviewLoading(false))
  }, [extractStatus?.phase, result?.output_path])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputPath) {
      setResult({ output_path: 'Select an input dataset first.' })
      return
    }
    setResult(null)
    setExtractStatus(null)
    setPreview(null)
    setPreviewError('')
    setPreviewLoading(false)
    try {
      const { data } = await features.extract({ input_path: inputPath, feature_mode: featureMode })
      setResult(data)
      setExtractStatus({ phase: data.status, progress: 0, output_path: data.output_path })
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setResult({ output_path: msg || 'Extraction failed' })
    }
  }

  const handleDeleteOutput = async () => {
    const outputPath = result?.output_path
    if (!outputPath) return
    const ok = window.confirm(`Delete extracted feature file?\n\n${outputPath}`)
    if (!ok) return
    setDeleting(true)
    setDeleteError('')
    try {
      await datasets.delete(outputPath)
      setResult(null)
      setExtractStatus(null)
      setPreview(null)
      setPreviewError('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setDeleteError(msg || 'Delete failed')
    } finally {
      setDeleting(false)
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
              disabled={!datasetList.length}
              style={{ width: '100%', padding: '0.6rem', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 4, color: 'var(--text)' }}
            >
              {!datasetList.length ? (
                <option value="">No datasets available</option>
              ) : (
                datasetList.map((d) => (
                  <option key={d.path} value={d.path}>{d.name}</option>
                ))
              )}
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
              <option value="sqli_37">SQLi 37 (Full Feature Set)</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={!inputPath || !datasetList.length}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'var(--accent)',
              border: 'none',
              borderRadius: 4,
              color: 'var(--bg-primary)',
              fontWeight: 600,
              cursor: !inputPath || !datasetList.length ? 'not-allowed' : 'pointer',
              opacity: !inputPath || !datasetList.length ? 0.6 : 1,
            }}
          >
            Extract Features
          </button>
        </form>
        {result && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: result.job_id ? 'var(--bg-primary)' : 'rgba(248,113,113,0.2)', borderRadius: 4, color: result.job_id ? undefined : 'var(--danger)' }}>
            {result.job_id && <p style={{ margin: 0 }}>Job ID: {result.job_id}</p>}
            {result.output_path && <p style={{ margin: '0.25rem 0 0' }}>{result.job_id ? 'Output: ' : ''}{result.output_path}</p>}

            {result.job_id && extractStatus && (
              <div style={{ marginTop: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', alignItems: 'center' }}>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    {extractStatus.phase || 'running'}
                    {extractStatus.total ? ` (${extractStatus.written ?? 0}/${extractStatus.total})` : null}
                  </div>
                  <div style={{ fontWeight: 700 }}>{extractStatus.progress ?? 0}%</div>
                </div>
                <div style={{ height: 10, background: 'var(--bg-card)', borderRadius: 6, overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${extractStatus.progress ?? 0}%`,
                      background:
                        extractStatus.phase === 'completed'
                          ? 'var(--success)'
                          : extractStatus.phase === 'failed'
                            ? 'var(--danger)'
                            : 'var(--accent)',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
                {extractStatus.error && <p style={{ marginTop: '0.75rem', color: 'var(--danger)' }}>{extractStatus.error}</p>}
              </div>
            )}

            {result.job_id && result.output_path && (
              <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={handleDeleteOutput}
                  disabled={deleting || extractStatus?.phase !== 'completed'}
                  style={{
                    padding: '0.6rem 1rem',
                    background: 'var(--danger)',
                    border: 'none',
                    borderRadius: 4,
                    color: 'white',
                    cursor: deleting || extractStatus?.phase !== 'completed' ? 'not-allowed' : 'pointer',
                    opacity: deleting || extractStatus?.phase !== 'completed' ? 0.7 : 1,
                    fontWeight: 600,
                  }}
                >
                  {deleting ? 'Deleting...' : 'Delete Feature File'}
                </button>
                {deleteError && (
                  <span style={{ color: 'var(--danger)', fontSize: '0.9rem' }}>{deleteError}</span>
                )}
              </div>
            )}

            {extractStatus?.phase === 'completed' && result.output_path && (
              <div style={{ marginTop: '1.25rem' }}>
                <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem' }}>Extracted Feature File</h3>
                <p style={{ margin: '0 0 1rem', color: 'var(--text-muted)' }}>{result.output_path}</p>

                <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem' }}>Feature Files</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
                  {featureFiles.length ? (
                    featureFiles.map((f) => (
                      <span
                        key={f.path}
                        style={{
                          padding: '0.35rem 0.6rem',
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--bg-card)',
                          borderRadius: 999,
                          color: 'var(--text-muted)',
                          fontSize: '0.85rem',
                        }}
                      >
                        {f.name}
                      </span>
                    ))
                  ) : (
                    <span style={{ color: 'var(--text-muted)' }}>No feature files found.</span>
                  )}
                </div>

                <h3 style={{ margin: '0 0 0.75rem', fontSize: '1rem' }}>Extracted Data Preview</h3>
                <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--bg-card)', borderRadius: 12, padding: '1rem' }}>
                  {previewLoading && <p style={{ margin: 0, color: 'var(--text-muted)' }}>Loading preview...</p>}
                  {previewError && <p style={{ margin: 0, color: 'var(--danger)' }}>{previewError}</p>}
                  {!previewLoading && !previewError && preview && (
                    <>
                      <p style={{ margin: '0 0 0.75rem', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                        Columns: {preview.columns?.length ?? '—'} · Rows: {preview.preview_rows ?? '—'} · Total: {preview.total_rows ?? '—'}
                      </p>
                      {preview.label_counts && Object.keys(preview.label_counts).length > 0 && (
                        <p style={{ margin: '0 0 0.75rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                          Labels: {Object.entries(preview.label_counts).slice(0, 5).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                        </p>
                      )}
                      <pre style={{ margin: 0, maxHeight: 220, overflow: 'auto', background: 'var(--bg-primary)', border: '1px solid var(--bg-card)', borderRadius: 10, padding: '0.75rem' }}>
                        {JSON.stringify(preview.rows.slice(0, 3), null, 2)}
                      </pre>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
